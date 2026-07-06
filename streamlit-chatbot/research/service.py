from __future__ import annotations

"""Computer-science research assistant utilities.

The service can query arXiv when network access is available and falls back to
a curated local CS corpus so the app remains functional offline.
"""

import datetime as dt
import re
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Any

from database.storage import execute, now_iso


LOCAL_CS_PAPERS: list[dict[str, Any]] = [
    {
        "title": "Attention Is All You Need",
        "authors": "Vaswani et al.",
        "published": "2017-06-12",
        "year": 2017,
        "category": "cs.CL",
        "url": "https://arxiv.org/abs/1706.03762",
        "summary": "Introduces the Transformer architecture using self-attention instead of recurrence or convolution for sequence modeling.",
        "keywords": ["transformer", "attention", "nlp", "sequence modeling"],
    },
    {
        "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "authors": "Devlin et al.",
        "published": "2018-10-11",
        "year": 2018,
        "category": "cs.CL",
        "url": "https://arxiv.org/abs/1810.04805",
        "summary": "Presents masked language modeling and next-sentence pretraining for bidirectional language representations.",
        "keywords": ["bert", "language model", "pretraining", "nlp"],
    },
    {
        "title": "Deep Residual Learning for Image Recognition",
        "authors": "He et al.",
        "published": "2015-12-10",
        "year": 2015,
        "category": "cs.CV",
        "url": "https://arxiv.org/abs/1512.03385",
        "summary": "Introduces residual connections that allow very deep convolutional networks to train effectively.",
        "keywords": ["resnet", "computer vision", "cnn", "image recognition"],
    },
    {
        "title": "Human-level Control through Deep Reinforcement Learning",
        "authors": "Mnih et al.",
        "published": "2015-02-25",
        "year": 2015,
        "category": "cs.LG",
        "url": "https://www.nature.com/articles/nature14236",
        "summary": "Combines deep neural networks with Q-learning to learn control policies from high-dimensional observations.",
        "keywords": ["reinforcement learning", "dqn", "control", "games"],
    },
    {
        "title": "Graph Attention Networks",
        "authors": "Velickovic et al.",
        "published": "2017-10-30",
        "year": 2017,
        "category": "cs.LG",
        "url": "https://arxiv.org/abs/1710.10903",
        "summary": "Applies masked self-attention over graph neighborhoods for inductive and transductive graph learning.",
        "keywords": ["graphs", "attention", "gnn", "node classification"],
    },
    {
        "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        "authors": "Lewis et al.",
        "published": "2020-05-22",
        "year": 2020,
        "category": "cs.CL",
        "url": "https://arxiv.org/abs/2005.11401",
        "summary": "Combines parametric generation with non-parametric dense retrieval to improve factual NLP responses.",
        "keywords": ["rag", "retrieval", "generation", "nlp"],
    },
]


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2}


def _score_paper(query: str, paper: dict[str, Any]) -> float:
    query_tokens = _tokens(query)
    haystack = " ".join(
        [
            paper.get("title", ""),
            paper.get("summary", ""),
            " ".join(paper.get("keywords", [])),
            paper.get("category", ""),
        ]
    )
    paper_tokens = _tokens(haystack)
    if not query_tokens:
        return 0.0
    overlap = len(query_tokens & paper_tokens)
    return overlap / max(1, len(query_tokens))


def _fetch_arxiv(query: str, max_results: int) -> list[dict[str, Any]]:
    try:
        import requests

        encoded_query = urllib.parse.quote(f"cat:cs.* AND all:{query}")
        url = (
            "https://export.arxiv.org/api/query"
            f"?search_query={encoded_query}&start=0&max_results={max_results}"
            "&sortBy=relevance&sortOrder=descending"
        )
        response = requests.get(url, timeout=12)
        response.raise_for_status()
        root = ET.fromstring(response.text)
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        papers = []
        for entry in root.findall("atom:entry", ns):
            title = " ".join((entry.findtext("atom:title", default="", namespaces=ns)).split())
            summary = " ".join((entry.findtext("atom:summary", default="", namespaces=ns)).split())
            published = entry.findtext("atom:published", default="", namespaces=ns)[:10]
            authors = ", ".join(
                author.findtext("atom:name", default="", namespaces=ns)
                for author in entry.findall("atom:author", ns)
            )
            url_value = entry.findtext("atom:id", default="", namespaces=ns)
            if url_value.startswith("http://"):
                url_value = "https://" + url_value[7:]
                
            # Extract PDF Link from Atom link attributes
            pdf_url = ""
            for link in entry.findall("atom:link", ns):
                rel = link.attrib.get("rel", "")
                link_type = link.attrib.get("type", "")
                href = link.attrib.get("href", "")
                if link_type == "application/pdf" or "pdf" in href.lower():
                    pdf_url = href
                    if pdf_url.startswith("http://"):
                        pdf_url = "https://" + pdf_url[7:]
                    break
            
            if not pdf_url and "arxiv.org/abs/" in url_value:
                pdf_url = url_value.replace("arxiv.org/abs/", "arxiv.org/pdf/") + ".pdf"
                
            category = ""
            category_el = entry.find("arxiv:primary_category", ns)
            if category_el is not None:
                category = category_el.attrib.get("term", "")
            
            # Parse DOI if available
            doi_el = entry.find("arxiv:doi", ns)
            doi = doi_el.text.strip() if doi_el is not None and doi_el.text else ""
            if not doi and "arxiv.org/abs/" in url_value:
                arxiv_id = url_value.split("/abs/")[-1]
                doi = f"10.48550/arXiv.{arxiv_id}"

            year = int(published[:4]) if published[:4].isdigit() else None
            papers.append(
                {
                    "title": title,
                    "authors": authors,
                    "published": published,
                    "year": year,
                    "category": category or "cs",
                    "url": url_value,
                    "pdf_url": pdf_url,
                    "doi": doi or "N/A",
                    "summary": summary,
                    "keywords": sorted(_tokens(title))[:8],
                    "source": "arXiv",
                }
            )
        return papers
    except Exception:
        return []


import streamlit as st

@st.cache_data(show_spinner=False)
def search_papers(query: str, max_results: int = 8, include_live_arxiv: bool = True) -> list[dict[str, Any]]:
    live = _fetch_arxiv(query, max_results) if include_live_arxiv else []
    local = sorted(
        LOCAL_CS_PAPERS,
        key=lambda item: _score_paper(query, item),
        reverse=True,
    )
    combined: list[dict[str, Any]] = []
    seen = set()
    for paper in live + local:
        key = paper.get("url") or paper.get("title", "").lower()
        if key in seen:
            continue
        seen.add(key)
        paper = dict(paper)
        paper.setdefault("source", "Local CS corpus")
        paper.setdefault("doi", f"10.48550/arXiv.{paper.get('url', '').split('/abs/')[-1] if '/abs/' in paper.get('url', '') else 'unknown'}")
        paper.setdefault("pdf_url", paper.get("url", "").replace("/abs/", "/pdf/") + ".pdf" if "/abs/" in paper.get("url", "") else "")
        paper["relevance"] = round(max(_score_paper(query, paper), 0.05), 3)
        combined.append(paper)
        if len(combined) >= max_results:
            break
    return combined


def format_papers_for_prompt(papers: list[dict[str, Any]]) -> str:
    if not papers:
        return "No matching papers found."
    lines = []
    for idx, paper in enumerate(papers, 1):
        lines.append(
            f"[{idx}] {paper.get('title')} ({paper.get('year') or paper.get('published', 'n.d.')})\n"
            f"Authors: {paper.get('authors', 'Unknown')}\n"
            f"Category: {paper.get('category', 'cs')}\n"
            f"URL: {paper.get('url', '')}\n"
            f"Summary: {paper.get('summary', '')}"
        )
    return "\n\n".join(lines)


def summarize_papers(papers: list[dict[str, Any]]) -> str:
    if not papers:
        return "No papers matched the query. Try a broader computer-science keyword."
    lines = ["### Research Summary"]
    for idx, paper in enumerate(papers[:5], 1):
        lines.append(
            f"{idx}. **{paper.get('title')}** ({paper.get('year') or paper.get('published', 'n.d.')}) - "
            f"{paper.get('summary', '')}\n"
            f"   Citation: [{paper.get('url', 'source')}]({paper.get('url', '')})"
        )
    return "\n\n".join(lines)


def related_papers(seed: dict[str, Any], candidates: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    seed_terms = _tokens(seed.get("summary", "") + " " + seed.get("title", ""))
    scored = []
    for paper in candidates:
        if paper.get("title") == seed.get("title"):
            continue
        score = len(seed_terms & _tokens(paper.get("summary", "") + " " + paper.get("title", "")))
        scored.append((score, paper))
    return [paper for score, paper in sorted(scored, key=lambda item: item[0], reverse=True)[:limit] if score > 0]


def record_research_query(user_id: str, query: str, result_count: int) -> None:
    execute(
        "INSERT INTO research_events (user_id, query, result_count, created_at) VALUES (?, ?, ?, ?)",
        (str(user_id), query, int(result_count), now_iso()),
    )


def timeline_rows(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for paper in papers:
        published = paper.get("published") or str(paper.get("year") or "")
        if len(published) == 4:
            published = f"{published}-01-01"
        try:
            dt.datetime.fromisoformat(published)
        except Exception:
            published = "2000-01-01"
        rows.append(
            {
                "date": published,
                "title": paper.get("title", "Untitled"),
                "category": paper.get("category", "cs"),
                "relevance": paper.get("relevance", 0.1),
            }
        )
    return rows

