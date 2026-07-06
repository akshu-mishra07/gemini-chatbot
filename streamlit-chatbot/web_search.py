"""
web_search.py - Lightweight live web search helpers for real-time questions.
"""

from __future__ import annotations

import datetime as _dt
import html
import re
import sys
import urllib.parse

import requests


REALTIME_TERMS = {
    "latest", "today", "yesterday", "current", "news", "weather", "ipl",
    "match", "score", "won", "winner", "sports", "result", "results",
    "election", "stock", "price", "live",
}


def is_realtime_query(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(rf"\b{re.escape(term)}\b", lowered) for term in REALTIME_TERMS)


import streamlit as st

@st.cache_data(show_spinner=False)
def search_web(query: str, max_results: int = 5) -> list[dict]:
    headers = {"User-Agent": "Mozilla/5.0 OmniChatAI/1.0"}
    endpoints = [
        "https://duckduckgo.com/html/",
        "https://html.duckduckgo.com/html/",
    ]
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, params={"q": query}, headers=headers, timeout=12)
            response.raise_for_status()
            return _parse_duckduckgo_html(response.text, max_results=max_results)
        except Exception as exc:
            print(f"[Live Search] DuckDuckGo request failed for {endpoint}: {exc}", file=sys.stderr)
    return []


def _parse_duckduckgo_html(page: str, max_results: int) -> list[dict]:
    blocks = re.findall(r'(<div[^>]+class="result[^"]*".*?</div>\s*</div>)', page, flags=re.S)
    results = []
    for block in blocks:
        title_match = re.search(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', block, flags=re.S)
        snippet_match = re.search(r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', block, flags=re.S)
        if not title_match:
            continue
        href = html.unescape(title_match.group(1))
        title = _clean_html(title_match.group(2))
        snippet_raw = snippet_match.group(1) if snippet_match else ""
        snippet = _clean_html(snippet_raw)
        if title and href:
            results.append({"title": title, "url": _unwrap_ddg_url(href), "snippet": snippet})
        if len(results) >= max_results:
            break
    return results


def _clean_html(value: str) -> str:
    value = re.sub(r"<.*?>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def _unwrap_ddg_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    if "uddg" in query:
        return query["uddg"][0]
    return url


def get_weather(location: str) -> str:
    loc = urllib.parse.quote(location.strip() or "")
    if not loc:
        raise ValueError("A location is required for weather lookup.")
    url = f"https://wttr.in/{loc}?format=3"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text.strip()


def extract_weather_location(query: str) -> str | None:
    match = re.search(r"weather\s+(?:in|for|at)\s+(.+)", query, flags=re.I)
    if match:
        return match.group(1).strip(" ?.!")
    return None


def format_results_for_prompt(query: str, results: list[dict]) -> str:
    now = _dt.datetime.now().strftime("%A, %B %d, %Y %I:%M %p")
    if not results:
        return f"No live web results were found for: {query}\nChecked at: {now}"
    lines = [f"Live web results for: {query}", f"Checked at: {now}"]
    for idx, item in enumerate(results, 1):
        lines.append(
            f"[{idx}] {item['title']}\nURL: {item['url']}\nSnippet: {item.get('snippet', '')}"
        )
    return "\n\n".join(lines)


def fallback_answer(query: str, results: list[dict]) -> str:
    if not results:
        return (
            "I could not retrieve live web results for that query. "
            "Please check your internet connection or try a more specific question."
        )
    lines = ["Here are the live results I found:"]
    for idx, item in enumerate(results, 1):
        snippet = f" - {item['snippet']}" if item.get("snippet") else ""
        lines.append(f"{idx}. [{item['title']}]({item['url']}){snippet}")
    return "\n".join(lines)
