# Kroolo AI Voice Assistant & Help Center

## 1. Overview

This project is a  AI-powered Voice Assistant and Help Center for the Kroolo platform. It leverages a multi-agent system built with the AGNO framework, a Pinecone vector database for knowledge retrieval, and FastAPI for serving the backend. The application allows users to interact with the Kroolo help system via voice or text, receive intelligent responses, and hear those responses spoken back.

## 2. Key Features

*   **Voice Interaction:**
    *   Speech-to-text (STT) using the `SpeechRecognition` library for user input.
    *   Text-to-speech (TTS) using `pyttsx3` for spoken agent responses.
    *   Dedicated FastAPI endpoints for initiating voice interactions and checking status.
*   **Intelligent Agent System (AGNO Framework):**
    *   Utilizes a `Gemini` model (via `agno.models.google`) as the core LLM for the agent.
    *   The "Kroolo Platform Assistant" agent is designed with detailed instructions to understand user queries, interpret variations of "Kroolo", and synthesize information.
    *   Manages conversation history for contextual understanding.
*   **Knowledge Base Integration (Pinecone):**
    *   Uses a Pinecone vector database to store and search Kroolo help documentation.
    *   Embeddings are generated using `SentenceTransformer('all-MiniLM-L6-v2')`.
    *   Retrieves relevant context from the "kroolo-docs" namespace to provide accurate answers.
*   **FastAPI Backend:**
    *   Provides API endpoints for:
        *   Text-based chat (`/chat`)
        *   Text-to-speech (`/speak`)
        *   Initiating voice interaction (`/voice/initiate`)
        *   Checking voice interaction status (`/voice/status`)
*   **Web Scraping & Data Preparation:**
    *   Includes scripts in the `web-scrape/` directory for crawling and preparing Kroolo help documentation.
    *   `vector-store.py` likely handles the embedding and upserting of this data into Pinecone.
*   **Potential Frontend:**
    *   `streamlit-app.py` suggests a user interface, possibly built with Streamlit (as it's in `requirements.txt`).

## 3. How It Works (Architecture & Data Flow)

1.  **User Input (Voice or Text):**
    *   **Voice:** The user initiates a voice interaction. The system listens via microphone, converts speech to text.
    *   **Text:** The user sends a text query directly to the chat endpoint.
2.  **Query Processing:**
    *   The user's query (and conversation history, if any) is sent to the `get_agent_response_async` function.
3.  **Context Retrieval (Pinecone):**
    *   The system embeds the user query using `SentenceTransformer`.
    *   It queries the Pinecone index (`kroolo` index, `kroolo-docs` namespace) to find relevant documents.
4.  **Agent Interaction (AGNO & Gemini):**
    *   The user query, conversation history, and retrieved context are formatted into a prompt for the `help_specialist_agent`.
    *   The agent, powered by a Gemini model, generates a response based on its instructions and the provided information.
5.  **Response Delivery:**
    *   **Text:** The agent's text response is returned via the API.
    *   **Voice:** If the interaction was voice-initiated, the agent's text response is converted to speech using `pyttsx3` and played back to the user.

## 4. Setup

### 4.1. Prerequisites

*   Python 3.8+
*   A Pinecone account and API key.
*   A Gemini API key (or relevant Google AI Studio API key).

### 4.2. Installation

1.  **Clone the repository (if applicable) or ensure you are in the project root (`app` directory).**

2.  **Create a virtual environment (recommended):**
    ```powershell
    python -m venv env
    .\env\Scripts\Activate.ps1
    ```

3.  **Install required packages:**
    ```powershell
    pip install -r requirements.txt
    ```

4.  **Create a `.env` file** in the `app` directory with your API keys:
    ```env
    PINECONE_API_KEY=your_pinecone_api_key
    GEMINI_API_KEY=your_gemini_api_key
    # Add any other necessary environment variables (e.g., for Groq if still used elsewhere)
    ```

### 4.3. Knowledge Base Setup

1.  **Prepare your Kroolo help documentation:**
    *   Use the scripts in `web-scrape/` (e.g., `2-crawl_docs_sequential.py`) to gather your documentation into a usable format (e.g., markdown files as seen in `web-scrape/help-kroolo-scraped-files/`).
    *   The `combined-kroolo-records.json` file might be an intermediate or final output of this process.
2.  **Embed and Upsert to Pinecone:**
    *   Run the `vector-store.py`. This script should handle:
        *   Reading the prepared documentation.
        *   Generating embeddings for each document chunk.
        *   Creating the "kroolo" index in Pinecone if it doesn't exist (dimension should match `all-MiniLM-L6-v2` model, which is 384).
        *   Upserting the vectors and metadata into the "kroolo-docs" namespace.
    *   Ensure the Pinecone index name and namespace in `backend.py` and `vector-store.py` match.

## 5. Usage

### 5.1. Running the Backend Server

Navigate to the `app` directory in your terminal and run the FastAPI application using Uvicorn:

```powershell
cd c:\Users\npuni\Desktop\Kroolo\app
uvicorn backend:app --reload
```

This will typically start the server on `http://127.0.0.1:8000`.

### 5.2. Interacting with the API

You can interact with the API using tools like Postman, curl, or a custom frontend.

*   **Chat:** `POST` to `http://127.0.0.1:8000/chat` with JSON body:
    ```json
    {
        "user_message": "How do I create a task in Kroolo?",
        "conversation_history": []
    }
    ```
*   **Speak Text:** `POST` to `http://127.0.0.1:8000/speak` with JSON body:
    ```json
    {
        "text": "Hello, this is a test."
    }
    ```
*   **Initiate Voice Interaction:** `POST` to `http://127.0.0.1:8000/voice/initiate` with JSON body (optional history):
    ```json
    {
        "conversation_history": []
    }
    ```
*   **Get Voice Status:** `GET` from `http://127.0.0.1:8000/voice/status`

### 5.3. Running the Frontend (Streamlit - Hypothesized)

If `streamlit-app.py` is a Streamlit application, you would typically run it with:

```powershell
streamlit run streamlit-app.py
```

## 6. Directory Structure

```
app/                          # Incorrect, should be project root
├── .git/                     # Git repository files
├── .gitignore                # Files and directories ignored by Git
├── backend.py                # FastAPI application, core logic
├── streamlit-app.py          # Potential Streamlit frontend
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── readme.txt                # Another readme file, perhaps a duplicate or old version?
├── .env                      # Environment variables (API keys) - This is typically not committed
├── vector-store.py           # Script to populate Pinecone (assuming this is the correct name)
├── env/                      # Python virtual environment (typically not committed)
├── static/                   # Static assets (e.g., images for frontend)
│   └── image.png
└── web-scrape/               # Scripts and data for web scraping
    ├── 2-crawl_docs_sequential.py
    ├── combined-kroolo-records.json # Scraped and processed data for Pinecone
    ├── help-kroolo-scraped-files/ # Raw scraped markdown files
    │   └── ... (multiple .md files)
    └── kroolo-scraped-files/    # Another directory with scraped files
        └── ... (content unknown without further listing)
```

## 7. Developer Notes & Potential Enhancements

*   **Error Handling:** Enhance error handling and logging throughout the application.
*   **Configuration:** Move hardcoded values (like Pinecone index name, model names) to a configuration file or environment variables.
*   **Frontend Development:** If `streamlit-app.py` is a placeholder, develop a user-friendly Streamlit (or other) interface.
*   **Agent Specialization:** The original README mentioned multiple specialized agents (Help Desk, Team Management, etc.). The current `backend.py` shows a single `help_specialist_agent`. This could be expanded by re-implementing the multi-agent routing/collaboration logic.
*   **Security:** Implement proper security measures if exposing the API publicly.
*   **Testing:** Add unit and integration tests.
*   **Pinecone v3+:** Monitor AGNO framework compatibility and consider upgrading Pinecone client when possible.

---

This README provides a comprehensive guide to understanding, setting up, and using the Kroolo AI Voice Assistant. For further questions, refer to the code comments or contact the project maintainers.
