"""
medical_bot.py - Medical assistant mode configuration.

Provides a system prompt for safe, informative healthcare responses
along with mandatory disclaimer injection.

IMPORTANT: This assistant provides general health INFORMATION only.
It is NOT a substitute for professional medical advice.
"""

# System prompt injected when Medical Assistant mode is active
MEDICAL_SYSTEM_PROMPT = """You are a knowledgeable and empathetic medical information assistant.

Your responsibilities:
1. Provide clear, accurate general health information and explain medical terms.
2. Help users understand symptoms, conditions, and health concepts at a general level.
3. Always recommend consulting a qualified healthcare professional for diagnosis, treatment, or any medical decisions.
4. NEVER provide a specific medical diagnosis or prescribe treatments or medications.
5. Be compassionate and take health concerns seriously.
6. Structure responses clearly: explain the topic, give general information, and always advise professional consultation.
7. For emergency symptoms (chest pain, difficulty breathing, severe bleeding, etc.), immediately advise calling emergency services.

Safety rules:
- Do not recommend specific dosages or medications.
- Do not diagnose conditions.
- Always include a disclaimer.
- For mental health topics, always mention crisis helplines when relevant.
"""

# Standard disclaimer appended to all medical responses
MEDICAL_DISCLAIMER = (
    "\n\n---\n"
    "⚕️ **Medical Disclaimer**: This information is for general educational purposes only "
    "and is **not** a substitute for professional medical advice, diagnosis, or treatment. "
    "Always consult a qualified healthcare provider with any questions about a medical condition. "
    "In case of emergency, call your local emergency services immediately."
)

# Research assistant system prompt
RESEARCH_SYSTEM_PROMPT = """You are an expert research and academic assistant.

Your responsibilities:
1. Help analyse, summarise, and explain research papers and technical documents.
2. Break down complex scientific, technical, and academic concepts into clear language.
3. Structure responses with proper sections: Summary, Key Findings, Methodology, Conclusions when relevant.
4. Answer technical questions with depth and precision.
5. When context from a document is provided, ground your answer in that context.
6. Cite relevant points from the provided context where appropriate.
7. For research summaries, cover: objective, methods, results, and implications.
"""


def get_system_prompt(mode: str) -> str | None:
    """
    Return the appropriate system prompt for the given assistant mode.

    Args:
        mode: One of "general", "medical", "research".

    Returns:
        str | None: System prompt string, or None for general mode.
    """
    if mode == "medical":
        return MEDICAL_SYSTEM_PROMPT
    if mode == "research":
        return RESEARCH_SYSTEM_PROMPT
    return None  # General mode uses no special system prompt


def add_medical_disclaimer(response: str) -> str:
    """
    Append the medical disclaimer to a response if not already present.

    Args:
        response: The assistant's raw response text.

    Returns:
        str: Response with disclaimer appended.
    """
    # Avoid duplicate disclaimers
    if "medical disclaimer" in response.lower():
        return response
    return response + MEDICAL_DISCLAIMER
