"""
app.py - Main Streamlit application entry point.

Renders the chat interface, manages session-level chat history, and
delegates all Gemini API calls to chatbot.py.
"""

import streamlit as st
from chatbot import send_message

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Gemini Chatbot",
    page_icon="💬",
    layout="centered",
)

st.title("💬 Gemini Chatbot")
st.caption("Powered by Google Gemini — type a message below to get started.")

# ---------------------------------------------------------------------------
# Session state — persists across Streamlit reruns within the same browser tab
# ---------------------------------------------------------------------------

# `messages` holds the full conversation as a list of dicts:
#   {"role": "user" | "assistant", "content": "..."}
# We display this list to render the chat history.
if "messages" not in st.session_state:
    st.session_state.messages = []

# `gemini_history` mirrors the conversation in the format expected by the
# Gemini SDK: [{"role": "user"|"model", "parts": [{"text": "..."}]}]
# We keep it in sync with `messages` so we can reconstruct the chat session.
if "gemini_history" not in st.session_state:
    st.session_state.gemini_history = []

# ---------------------------------------------------------------------------
# Display existing chat history
# ---------------------------------------------------------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---------------------------------------------------------------------------
# User input box (pinned to the bottom of the page by st.chat_input)
# ---------------------------------------------------------------------------
user_input = st.chat_input("Ask me anything…")

if user_input:
    # Show the user's message immediately
    with st.chat_message("user"):
        st.markdown(user_input)

    # Persist the user's message to session state
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.gemini_history.append(
        {"role": "user", "parts": [{"text": user_input}]}
    )

    # Call Gemini and stream / display the response
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                # Send the message along with the full history for context
                # (gemini_history does not yet include the current user turn)
                reply = send_message(st.session_state.gemini_history, user_input)
                st.markdown(reply)

                # Persist the assistant's reply to session state
                st.session_state.messages.append(
                    {"role": "assistant", "content": reply}
                )
                st.session_state.gemini_history.append(
                    {"role": "model", "parts": [{"text": reply}]}
                )

            except ValueError as e:
                # API key is missing — surface a clear error to the user
                st.error(str(e))
            except Exception as e:
                # Any other Gemini / network error
                st.error(f"An error occurred: {e}")

# ---------------------------------------------------------------------------
# Sidebar — clear conversation button
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Options")
    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.gemini_history = []
        st.rerun()
