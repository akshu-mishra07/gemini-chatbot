# Gemini Chatbot

A clean, multi-turn chatbot built with Python and Streamlit, powered by Google's Gemini API.

## Features

- Clean chat interface with message bubbles
- Full conversation history preserved across turns
- Automatic model selection — picks the best available Gemini model for your API key
- Automatic fallback — if a model returns a 503 or quota error, the next model in the priority list is tried seamlessly
- Clear conversation button in the sidebar
- API key read securely from environment variables

## Project Structure

```
streamlit-chatbot/
├── app.py          # Streamlit UI — chat interface, session state, user input
├── chatbot.py      # Gemini API layer — client, model selection, fallback logic
├── requirements.txt
└── .streamlit/
    └── config.toml # Server and browser config
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

### 2. Install dependencies

```bash
pip install -r streamlit-chatbot/requirements.txt
```

### 3. Set your Gemini API key

Get a free API key at https://aistudio.google.com/app/apikey, then set it as an environment variable:

```bash
export GEMINI_API_KEY=your_api_key_here
```

### 4. Run the app

```bash
cd streamlit-chatbot
streamlit run app.py --server.port 5000
```

Open http://localhost:5000 in your browser.

## Model Fallback Priority

The chatbot automatically tries models in this order, falling back on 503 or quota errors:

1. `gemini-2.5-flash-lite`
2. `gemini-2.0-flash`
3. `gemini-flash-latest`
4. `gemini-pro-latest`

## Tech Stack

- [Streamlit](https://streamlit.io/) — web UI framework
- [Google Gemini API](https://ai.google.dev/) via the `google-genai` SDK
- Python 3.11+

## Environment Variables

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Your Google Gemini API key (required) |
