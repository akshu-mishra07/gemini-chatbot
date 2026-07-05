"""
medical_entities.py - Medical Entity Recognition and Highlighting module.

Uses spaCy and custom vocabularies to detect symptoms, diseases, treatments,
medications, and body parts, and formats highlights for UI presentation.
"""

import re

# Categories of medical entities to detect
ENTITY_COLORS = {
    "SYMPTOM": {"text": "#cbd5e1", "border": "rgba(168, 85, 247, 0.4)", "bg": "rgba(168, 85, 247, 0.15)", "label": "Symptom"},
    "DISEASE": {"text": "#cbd5e1", "border": "rgba(239, 68, 68, 0.4)", "bg": "rgba(239, 68, 68, 0.15)", "label": "Disease"},
    "TREATMENT": {"text": "#cbd5e1", "border": "rgba(13, 148, 136, 0.4)", "bg": "rgba(13, 148, 136, 0.15)", "label": "Treatment"},
    "MEDICATION": {"text": "#cbd5e1", "border": "rgba(16, 185, 129, 0.4)", "bg": "rgba(16, 185, 129, 0.15)", "label": "Medication"},
    "BODY_PART": {"text": "#cbd5e1", "border": "rgba(14, 165, 233, 0.4)", "bg": "rgba(14, 165, 233, 0.15)", "label": "Body Part"}
}

import streamlit as st

_nlp = None

@st.cache_resource(show_spinner=False)
def get_spacy_model():
    """
    Get or initialize the spaCy pipeline.

    The entity detector uses phrase matchers, so a blank English tokenizer is
    enough when the full small English model is not installed.
    """
    global _nlp
    if _nlp is not None:
        return _nlp

    try:
        import spacy
    except ImportError:
        print("spaCy library is not installed.")
        return None

    try:
        nlp_model = spacy.load("en_core_web_sm")
    except OSError:
        print("spaCy model 'en_core_web_sm' not found. Using blank English tokenizer.")
        nlp_model = spacy.blank("en")
    except Exception as e:
        print(f"Unexpected error loading spaCy model: {e}")
        return None
    
    # Initialize phrase matchers
    try:
        setup_matchers(nlp_model)
    except Exception as e:
        print(f"Failed to setup phrase matchers: {e}")
        return None
    
    _nlp = nlp_model
    return nlp_model

# Lexicons for entity classification
SYMPTOMS_LEXICON = [
    "pain", "fever", "cough", "fatigue", "nausea", "vomiting", "dizziness", "headache", "chills", "swelling",
    "shortness of breath", "dyspnea", "chest pain", "rash", "itch", "itching", "sore throat", "congestion",
    "weakness", "diarrhea", "constipation", "insomnia", "sneezing", "wheezing", "numbness", "spasm",
    "runny nose", "abdominal pain", "muscle ache", "joint pain", "loss of appetite", "dehydration", "sweating",
    "weight loss", "weight gain", "high fever", "soreness", "bleeding"
]

DISEASES_LEXICON = [
    "diabetes", "asthma", "hypertension", "anemia", "cancer", "flu", "arthritis", "tuberculosis", "pneumonia",
    "covid-19", "covid", "depression", "anxiety", "leukemia", "lymphoma", "malaria", "cholesterol", "hepatitis",
    "alzheimer's", "parkinson's", "stroke", "heart attack", "obesity", "migraine", "bronchitis", "allergies",
    "cardiovascular disease", "osteoporosis", "dementia", "kidney disease", "kidney failure", "heart disease",
    "copd", "hiv", "aids", "lupus", "celiac", "crohn's", "colitis", "thyroid disease", "hypothyroidism", "hyperthyroidism",
    "glaucoma", "cataracts", "high blood pressure", "low blood pressure", "anemic", "diabetic",
    "pcos", "pcod", "polycystic ovary syndrome", "polycystic ovarian disease", "pregnancy", "pregnant"
]

TREATMENTS_LEXICON = [
    "therapy", "surgery", "chemotherapy", "radiation", "physical therapy", "dialysis", "acupuncture", "rehabilitation",
    "vaccine", "vaccination", "immunization", "transplant", "operation", "lifestyle changes", "exercise", "diet",
    "treatment", "prevention", "screening", "biopsy", "mastectomy", "coronary bypass", "angioplasty", "intubation",
    "first aid", "cpr", "psychotherapy", "cognitive behavioral therapy", "transplantation"
]

MEDICATIONS_LEXICON = [
    "insulin", "metformin", "aspirin", "ibuprofen", "acetaminophen", "paracetamol", "penicillin", "amoxicillin",
    "albuterol", "lipitor", "lisinopril", "statin", "antibiotics", "steroids", "advil", "tylenol", "motrin",
    "vaccines", "antihistamine", "antidepressant", "chemo", "beta blockers", "insulin therapy", "medication", "pill"
]

BODY_PARTS_LEXICON = [
    "heart", "lungs", "lung", "kidneys", "kidney", "liver", "stomach", "brain", "blood", "bones", "bone", "joints", "joint",
    "skin", "eyes", "eye", "throat", "chest", "abdomen", "intestine", "nerves", "nerve", "pancreas", "gallbladder",
    "muscles", "muscle", "arteries", "veins", "vein", "spine", "head", "neck", "ears", "mouth", "nose"
]

_matcher = None

def setup_matchers(nlp_model):
    """
    Sets up phrase matchers for each vocabulary list.
    """
    global _matcher
    if nlp_model is None:
        return
    from spacy.matcher import PhraseMatcher
    _matcher = PhraseMatcher(nlp_model.vocab, attr="LOWER")
    
    # Add rules
    _matcher.add("SYMPTOM", [nlp_model.make_doc(t) for t in SYMPTOMS_LEXICON])
    _matcher.add("DISEASE", [nlp_model.make_doc(t) for t in DISEASES_LEXICON])
    _matcher.add("TREATMENT", [nlp_model.make_doc(t) for t in TREATMENTS_LEXICON])
    _matcher.add("MEDICATION", [nlp_model.make_doc(t) for t in MEDICATIONS_LEXICON])
    _matcher.add("BODY_PART", [nlp_model.make_doc(t) for t in BODY_PARTS_LEXICON])

def detect_medical_entities(text: str) -> dict:
    """
    Analyzes the text using spaCy and the phrase matchers, extracting categorized entities.

    Returns:
        dict: A dictionary mapping entity labels to lists of unique detected phrases.
    """
    nlp = get_spacy_model()
    if nlp is None:
        return {
            "SYMPTOM": [],
            "DISEASE": [],
            "TREATMENT": [],
            "MEDICATION": [],
            "BODY_PART": [],
            "unavailable": True
        }
    global _matcher
    if _matcher is None:
        setup_matchers(nlp)
    if _matcher is None:
        return {
            "SYMPTOM": [],
            "DISEASE": [],
            "TREATMENT": [],
            "MEDICATION": [],
            "BODY_PART": [],
            "unavailable": True
        }
    
    try:
        doc = nlp(text)
        
        detected = {
            "SYMPTOM": set(),
            "DISEASE": set(),
            "TREATMENT": set(),
            "MEDICATION": set(),
            "BODY_PART": set()
        }
        
        matches = _matcher(doc)
        for match_id, start, end in matches:
            label = nlp.vocab.strings[match_id]
            phrase = doc[start:end].text
            detected[label].add(phrase)
            
        # Convert sets to sorted lists
        return {k: sorted(list(v)) for k, v in detected.items()}
    except Exception as e:
        print(f"Error executing spaCy matcher: {e}")
        return {
            "SYMPTOM": [],
            "DISEASE": [],
            "TREATMENT": [],
            "MEDICATION": [],
            "BODY_PART": [],
            "unavailable": True
        }

def highlight_medical_entities(text: str) -> str:
    """
    Scans the text, locates matches, and replaces them with inline HTML span badges.
    Uses a slice-based replacement technique to avoid nested replacement bugs.
    """
    nlp = get_spacy_model()
    if nlp is None:
        return text
    global _matcher
    if _matcher is None:
        setup_matchers(nlp)
    if _matcher is None:
        return text
    
    try:
        doc = nlp(text)
        matches = _matcher(doc)
    except Exception as e:
        print(f"Error highlighting medical entities: {e}")
        return text
    
    # 1. Gather all matched spans
    spans = []
    for match_id, start, end in matches:
        label = nlp.vocab.strings[match_id]
        span = doc[start:end]
        spans.append((span.start_char, span.end_char, label, span.text))
        
    if not spans:
        return text

    # 2. Sort by start character ascending, and length descending (to resolve overlapping)
    spans.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    
    # 3. Filter out overlapping matches
    filtered_spans = []
    last_end = -1
    for start, end, label, matched_text in spans:
        if start >= last_end:
            filtered_spans.append((start, end, label, matched_text))
            last_end = end

    # 4. Construct final highlighted text
    output = []
    current_idx = 0
    for start, end, label, matched_text in filtered_spans:
        # Append plain text before this match
        output.append(text[current_idx:start])
        
        # Retrieve colors for this category
        color_info = ENTITY_COLORS.get(label)
        bg = color_info["bg"]
        border = color_info["border"]
        txt = color_info["text"]
        lbl = color_info["label"]
        
        # Wrap the match in a premium styled HTML span (no inline label suffix for clean reading)
        badge = (
            f'<span style="'
            f'background-color: {bg}; '
            f'border: 1px solid {border}; '
            f'color: {txt}; '
            f'border-radius: 4px; '
            f'padding: 1px 6px; '
            f'font-weight: 500; '
            f'font-size: 0.92em; '
            f'display: inline-block; '
            f'margin: 0 2px; '
            f'box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);'
            f'">{matched_text}</span>'
        )
        output.append(badge)
        current_idx = end
        
    # Append remaining text
    output.append(text[current_idx:])
    
    return "".join(output)

if __name__ == "__main__":
    # Test script execution
    test_text = "The patient is a 45-year-old male with diabetes who experiences chest pain, high fever and severe fatigue. He is currently taking metformin and insulin therapy. The doctor recommended heart screening."
    print("Original:", test_text)
    print("Entities:", detect_medical_entities(test_text))
    print("Highlighted:", highlight_medical_entities(test_text))
