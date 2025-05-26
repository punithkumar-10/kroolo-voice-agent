import streamlit as st
import os
import base64
import time
import requests



# --- Page Configuration (MUST BE THE FIRST STREAMLIT COMMAND) ---
st.set_page_config(
    page_title="Kroolo AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for a Modern UI ---
st.markdown("""
<style>
    /* --- General --- */
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #F8F9FA; /* Lighter gray background */
    }
    .stApp {
        background-color: #F8F9FA; /* Lighter gray background */
    }

    /* --- Sidebar --- */
    .st-emotion-cache-16txtl3 { /* Sidebar main container */
        background-color: #ffffff; /* White sidebar */
        border-right: 1px solid #DEE2E6; /* Slightly lighter border */
    }
    .st-emotion-cache-16txtl3 h1, .st-emotion-cache-16txtl3 h2, .st-emotion-cache-16txtl3 h3, .st-emotion-cache-16txtl3 .stRadio > label {
        color: #0078D4; /* Primary blue for sidebar headers/text */
    }
    .stRadio > label {
        font-weight: 500;
    }

    /* --- Main Content --- */
    .st-emotion-cache-z5fcl4 { /* Main content block */
        padding: 2rem;
    }
    h1, h2, h3 {
        color: #005A9E; /* Darker blue for main titles */
    }

    /* --- Buttons (General) --- */
    /* General .stButton > button styles might be overridden by Jarvis button if specific enough */
    /* We can keep them as a fallback or for other buttons */
    .stButton > button {
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 500;
        border: none;
        color: white;
        background-color: #0078D4; /* Primary blue */
        transition: background-color 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #005A9E; /* Darker blue on hover */
    }
    .stButton > button:active {
        background-color: #004578; /* Even darker blue on active */
    }

    /* --- Jarvis Voice Button (Primary Styling Target) --- */
    .jarvis-button-wrapper {
        width: 100%; /* Ensure the wrapper takes full available width */
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 20px; 
        margin-bottom: 25px; 
    }
    /* This div is just a container for class assignment and flex alignment; should not have visual styles itself */
    .jarvis-button-container {
        display: flex; 
        justify-content: center;
        align-items: center;
    }
    /* Styles the actual Streamlit button element when inside .jarvis-button-container */
    .jarvis-button-container div[data-testid="stButton"] > button {
        width: 240px !important; 
        height: 240px !important; 
        border-radius: 50% !important; 
        font-size: 6rem !important; 
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        padding: 0 !important; 
        box-shadow: 0 5px 18px rgba(0, 0, 0, 0.25) !important;
        transition: all 0.3s ease !important;
        border: 3px solid transparent !important; 
        line-height: 1 !important; 
    }
    .jarvis-button-container.start-button div[data-testid="stButton"] > button {
        background-color: #0078D4 !important; 
        color: white !important;
    }
    .jarvis-button-container.start-button div[data-testid="stButton"] > button:hover {
        background-color: #005A9E !important;
        transform: translateY(-3px) scale(1.05) !important;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3) !important;
        border-color: #004578 !important;
    }
    .jarvis-button-container.stop-button div[data-testid="stButton"] > button {
        background-color: #FF7043 !important; 
        color: white !important;
    }
    .jarvis-button-container.stop-button div[data-testid="stButton"] > button:hover {
        background-color: #F4511E !important;
        transform: translateY(-3px) scale(1.05) !important;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3) !important;
        border-color: #D84315 !important;
    }

    /* --- Text Input --- */
    .stTextInput > div > div > input {
        border-radius: 8px;
        padding: 10px;
        border: 1px solid #CED4DA; 
        background-color: #ffffff; 
        color: #212529; 
    }
    .stTextInput > div > div > input:focus {
        border-color: #0078D4; 
        box-shadow: 0 0 0 0.2rem rgba(0, 120, 212, 0.25);
    }
    
    /* --- Text Area (for displaying speech/responses - if any are kept elsewhere) --- */
    .stTextArea textarea {
        border-radius: 8px;
        padding: 10px;
        background-color: #ffffff; 
        border: 1px solid #CED4DA; 
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 0.95rem; 
        color: #212529; 
        margin-bottom: 10px; 
    }

    /* --- Chat Messages --- */
    .chat-container {
        margin-bottom: 20px;
        padding: 15px;
        border-radius: 12px;
        background-color: #ffffff;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .chat-bubble {
        padding: 10px 15px;
        border-radius: 18px;
        margin-bottom: 8px;
        max-width: 75%;
        word-wrap: break-word;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .user-bubble {
        background-color: #0078D4; 
        color: white;
        margin-left: auto;
        text-align: right;
        border-bottom-right-radius: 5px;
    }
    .assistant-bubble {
        background-color: #E9ECEF; 
        color: #212529; 
        margin-right: auto;
        text-align: left;
        border-bottom-left-radius: 5px;
    }
    .chat-bubble strong { 
        font-weight: 600;
    }
    
    /* --- Status Messages --- */
    .stAlert { 
        border-radius: 8px;
        padding: 12px;
    }
    .stAlert[data-baseweb="notification"] .st-emotion-cache-1wmy9hl { 
        fill: #0078D4; 
    }
</style>
""", unsafe_allow_html=True)

# FastAPI backend URL
BACKEND_URL = "http://127.0.0.1:8000"
MAX_HISTORY_TURNS_STREAMLIT = 5 # Max history turns to keep in frontend state
TTS_COOLDOWN_S = 0.2 # Cooldown period in seconds after TTS before next listen

# Helper function to convert image to base64
def image_to_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        print(f"Error: Logo image not found at {path}. Cannot embed.")
        return "" # Return empty string or a placeholder base64

# --- Title with Logo ---
# Construct the absolute path to the image
image_file_path = os.path.join(os.path.dirname(__file__), "static", "image.png")
logo_base64 = image_to_base64(image_file_path)

if logo_base64:
    st.markdown(
        f"""
        <div style="display: flex; flex-direction: column; align-items: center; width: 100%; margin-bottom: 2rem; margin-top: 1rem;">
            <img src="data:image/png;base64,{logo_base64}" style="width: 60px; height: auto; margin-bottom: 10px;" alt="Kroolo Logo">
            <h1 style="margin: 0; font-size: 2.2rem; color: #005A9E; text-align: center;">Kroolo Platform Assistant</h1>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    # Fallback if image couldn't be loaded - just show the title
    st.markdown(
        """
        <div style="display: flex; flex-direction: column; align-items: center; width: 100%; margin-bottom: 2rem; margin-top: 1rem;">
            <h1 style="margin: 0; font-size: 2.2rem; color: #005A9E; text-align: center;">Kroolo Platform Assistant</h1>
        </div>
        """,
        unsafe_allow_html=True
    )
    # Optionally, notify the user in the app if the logo is missing
    # st.warning("Kroolo logo could not be loaded. Please check the file path: static/image.png")


st.sidebar.header("Interaction Mode")
interaction_mode = st.sidebar.radio(
    "Choose interaction mode:",
    ("Voice", "Text"),
    key="interaction_mode_radio"
)

# Initialize session state variables
if 'voice_is_processing' not in st.session_state: # True if frontend is managing an active voice cycle with backend
    st.session_state.voice_is_processing = False
if 'voice_user_speech' not in st.session_state:
    st.session_state.voice_user_speech = ""
if 'voice_agent_response' not in st.session_state:
    st.session_state.voice_agent_response = ""
if 'voice_status_message' not in st.session_state: # Backend status for current/last cycle
    st.session_state.voice_status_message = "idle"
if 'voice_error_message' not in st.session_state:
    st.session_state.voice_error_message = ""
if 'continuous_voice_mode_active' not in st.session_state: # True if continuous loop is enabled
    st.session_state.continuous_voice_mode_active = False
if 'voice_conversation_history' not in st.session_state:
    st.session_state.voice_conversation_history = []
if 'tts_cooldown_active' not in st.session_state: # True if waiting for TTS to finish before relistening
    st.session_state.tts_cooldown_active = False
if 'waiting_for_backend_ready' not in st.session_state: # True if waiting for backend to be free for new cycle
    st.session_state.waiting_for_backend_ready = False

if 'text_chat_response' not in st.session_state:
    st.session_state.text_chat_response = ""
if 'text_chat_error' not in st.session_state:
    st.session_state.text_chat_error = ""
if 'text_conversation_history' not in st.session_state:
    st.session_state.text_conversation_history = []


def handle_voice_interaction():
    st.markdown(
        "<div style='display: flex; flex-direction: column; align-items: center; width: 100%; margin-bottom: 1rem;'>", # Removed margin-top from here as it's part of the button's wrapper now
        unsafe_allow_html=True
    )

    button_label = "🎙️ Start Conversation with Kroolo Assistant"
    if st.session_state.continuous_voice_mode_active:
        button_label = "⏹️ End Conversation with Kroolo Assistant"
    
    if st.button(button_label, key="toggle_continuous_voice_button", help="Start or end a voice conversation with the Kroolo Assistant", use_container_width=False):
        st.session_state.continuous_voice_mode_active = not st.session_state.continuous_voice_mode_active
        st.session_state.voice_is_processing = False
        st.session_state.tts_cooldown_active = False
        st.session_state.waiting_for_backend_ready = False
        if st.session_state.continuous_voice_mode_active:
            st.session_state.voice_conversation_history = []
            st.session_state.voice_status_message = "idle"
            st.session_state.voice_user_speech = ""
            st.session_state.voice_agent_response = ""
            st.session_state.voice_error_message = ""
        st.rerun()


    st.markdown("</div>", unsafe_allow_html=True)

    # --- Display Voice Conversation History ---
    voice_chat_history_placeholder = st.container()
    with voice_chat_history_placeholder:
        if st.session_state.voice_conversation_history:
            # st.markdown("<h3 style='text-align: center; color: #005A9E; margin-bottom: 1rem;'>Conversation</h3>", unsafe_allow_html=True)
            for message in st.session_state.voice_conversation_history:
                role_label = "You" if message["role"] == "user" else "Kroolo Assistant"
                bubble_class = "user-bubble" if message["role"] == "user" else "assistant-bubble"
                avatar_emoji = "👤" if message["role"] == "user" else "🤖"
                
                content_display = str(message.get('content', ''))

                st.markdown(
                    f"<div class='chat-bubble {bubble_class}'><strong>{avatar_emoji} {role_label}:</strong><br>{content_display}</div>",
                    unsafe_allow_html=True
                )
            st.markdown("<hr style='margin-top: 10px; margin-bottom: 10px;'>", unsafe_allow_html=True)
        elif st.session_state.continuous_voice_mode_active and not st.session_state.voice_is_processing : # If active but no history yet, and not in middle of processing
            st.markdown("<p style='text-align: center; color: #555; margin-top:1rem; margin-bottom:1rem;'>Your voice conversation will appear here. Click the button above to start.</p>", unsafe_allow_html=True)


    status_container = st.container()

    # 1. Handle TTS Cooldown Period if active
    if st.session_state.tts_cooldown_active:
        # The main display block (further down, within status_container) will show 
        # "🗣️ Agent is speaking..." and the relevant text areas.
        # We just need the sleep and state transition here.
        time.sleep(TTS_COOLDOWN_S) # Short cooldown period 
        st.session_state.tts_cooldown_active = False
        st.session_state.voice_is_processing = False # Ensure this is false
        if st.session_state.continuous_voice_mode_active: # Only proceed to wait for backend if still continuous
            st.session_state.waiting_for_backend_ready = True # Signal to check backend readiness next
        st.rerun() 

    # 2. Handle Waiting for Backend to be Ready (NEW BLOCK)
    elif st.session_state.waiting_for_backend_ready and st.session_state.continuous_voice_mode_active:
        st.info("Checking if backend is ready for new voice input...")
        try:
            status_response = requests.get(f"{BACKEND_URL}/voice/status")
            status_response.raise_for_status()
            backend_state = status_response.json()
            
            if not backend_state.get("is_processing"): # Backend is NOT processing, so it's ready
                st.session_state.waiting_for_backend_ready = False
                # voice_is_processing is already False from tts_cooldown or initial state
                st.info("Backend is ready. Listening for your voice...")
                st.rerun() # Proceed to initiate interaction in the next block
            else: # Backend is still processing from its view
                # st.warning("Backend is still finishing up. Waiting a moment...")
                time.sleep(0.75) # Wait a bit before checking again
                st.rerun()
                
        except requests.exceptions.RequestException as e:
            st.error(f"Error checking backend status: {e}. Stopping continuous mode.")
            st.session_state.continuous_voice_mode_active = False 
            st.session_state.waiting_for_backend_ready = False
            st.session_state.voice_is_processing = False
            st.rerun()

    # 3. Initiate new voice interaction cycle (if continuous, not processing, not in cooldown, not waiting for backend)
    elif st.session_state.continuous_voice_mode_active and \
         not st.session_state.voice_is_processing and \
         not st.session_state.tts_cooldown_active and \
         not st.session_state.waiting_for_backend_ready:
        
        st.session_state.voice_is_processing = True 
        st.session_state.voice_status_message = "initiating_listen" 
        st.session_state.voice_user_speech = "" # Clear for new turn
        st.session_state.voice_agent_response = "" # Clear for new turn
        st.session_state.voice_error_message = "" # Clear for new turn

        try:
            # Tell backend to start a full voice interaction cycle
            initiate_response = requests.post(
                f"{BACKEND_URL}/voice/initiate",
                json={"conversation_history": st.session_state.voice_conversation_history}
            )
            initiate_response.raise_for_status()
            initiate_data = initiate_response.json()
            
            if initiate_data.get("status") == "error":
                st.session_state.voice_error_message = initiate_data.get("message", "Backend could not start voice interaction.")
                st.session_state.voice_is_processing = False 
                st.session_state.continuous_voice_mode_active = False # Stop continuous mode on critical init error
            # else: Backend has started, polling will pick it up.
            st.rerun() # Rerun to start polling or show error

        except requests.exceptions.RequestException as e:
            st.session_state.voice_error_message = f"Error connecting to backend (initiate): {e}"
            st.session_state.voice_is_processing = False
            st.session_state.continuous_voice_mode_active = False
            st.rerun()
        except Exception as e:
            st.session_state.voice_error_message = f"Unexpected error during voice initiation: {e}"
            st.session_state.voice_is_processing = False
            st.session_state.continuous_voice_mode_active = False # Stop continuous on unexpected init error
            st.rerun()

    # Polling logic: This runs if frontend is managing a voice cycle (voice_is_processing is true)
    # and not in TTS cooldown or waiting for backend (those are handled by the preceding 'if'/'elif' blocks)
    elif st.session_state.voice_is_processing:
        try:
            status_response = requests.get(f"{BACKEND_URL}/voice/status")
            status_response.raise_for_status()
            backend_state = status_response.json()

            current_backend_status = backend_state.get("status_message", "unknown")
            st.session_state.voice_status_message = current_backend_status # Update frontend status with backend's current phase

            # Update user speech as soon as it's available from backend
            if backend_state.get("user_speech"):
                 st.session_state.voice_user_speech = backend_state.get("user_speech")
            
            # Agent response is typically set when status is 'complete', but check defensively
            if backend_state.get("agent_response"):
                 st.session_state.voice_agent_response = backend_state.get("agent_response")


            if current_backend_status == "complete":
                # Final update of all relevant fields from the backend
                st.session_state.voice_user_speech = backend_state.get("user_speech", st.session_state.voice_user_speech)
                
                agent_resp_from_backend = backend_state.get("agent_response")
                if agent_resp_from_backend is not None:
                    st.session_state.voice_agent_response = agent_resp_from_backend
                else: # Should not happen if status is complete without error, but good to handle
                    st.session_state.voice_agent_response = "Error: Agent did not provide a response."
                
                st.session_state.voice_error_message = backend_state.get("error_message", "") # This is backend's STT/process error

                # Determine if we can and should speak
                can_add_to_history_and_speak = bool(st.session_state.voice_agent_response and \
                                                 not st.session_state.voice_error_message and \
                                                 st.session_state.voice_user_speech)

                if can_add_to_history_and_speak:
                    # Add to conversation history
                    st.session_state.voice_conversation_history.append({"role": "user", "content": st.session_state.voice_user_speech})
                    st.session_state.voice_conversation_history.append({"role": "assistant", "content": st.session_state.voice_agent_response})
                    if len(st.session_state.voice_conversation_history) > MAX_HISTORY_TURNS_STREAMLIT * 2:
                        st.session_state.voice_conversation_history = st.session_state.voice_conversation_history[-(MAX_HISTORY_TURNS_STREAMLIT * 2):]

                    # Speak the AGENT'S response
                    try:
                        short_response_for_log = st.session_state.voice_agent_response[:70].replace(chr(10), " ") + "..." if len(st.session_state.voice_agent_response) > 70 else st.session_state.voice_agent_response.replace(chr(10), " ")
                        st.info(f"Attempting to speak: '{short_response_for_log}'") # UI feedback
                        print(f"[DEBUG] Sending TTS to backend: {st.session_state.voice_agent_response}")
                        speak_payload = {"text": st.session_state.voice_agent_response} 
                        speak_response = requests.post(f"{BACKEND_URL}/speak", json=speak_payload, timeout=15) # Increased timeout
                        speak_response.raise_for_status() # Raises HTTPError for bad responses (4XX or 5XX)
                        speak_data = speak_response.json()

                        if speak_data.get("status") == "success":
                            st.success(f"TTS Backend: {speak_data.get('message', 'Speech initiated.')}") # UI feedback
                            print(f"Frontend: TTS Backend reported success: {speak_data.get('message')}")
                        elif speak_data.get("status") == "error":
                            st.warning(f"TTS Error (from backend): {speak_data.get('message', 'Unknown TTS error.')}") # UI feedback
                            print(f"Frontend: Error during TTS speak from backend: {speak_data.get('message')}")
                        else:
                            st.warning(f"TTS status from backend unknown: {speak_data}") # UI feedback
                            print(f"Frontend: Unknown TTS status from backend: {speak_data}")

                    except requests.exceptions.Timeout:
                        st.warning("TTS request timed out.") # UI feedback
                        print("Frontend: TTS request timed out.")
                    except requests.exceptions.HTTPError as e_http:
                        st.warning(f"TTS request failed (HTTP Error): {e_http.response.status_code} - {e_http.response.text}") # UI feedback
                        print(f"Frontend: HTTPError during TTS speak call: {e_http.response.status_code} - {e_http.response.text}")
                    except requests.exceptions.RequestException as e_speak_req:
                        st.warning(f"TTS request failed (Connection/Other): {e_speak_req}") # UI feedback
                        print(f"Frontend: Exception during TTS speak call (request): {e_speak_req}")
                    except Exception as e_speak_other: # Catch other errors like JSONDecodeError if response is not JSON
                        st.warning(f"TTS failed (unexpected error): {e_speak_other}") # UI feedback
                        print(f"Frontend: Exception during TTS speak call (other): {e_speak_other}")
                else:
                    # Log why speaking (and history update for this turn) was skipped
                    reason_skipped = []
                    if not st.session_state.voice_agent_response: reason_skipped.append("No agent response.")
                    if st.session_state.voice_error_message: reason_skipped.append(f"Backend error flagged: '{st.session_state.voice_error_message}'")
                    if not st.session_state.voice_user_speech: reason_skipped.append("No user speech recorded for this turn.")
                    st.warning(f"[AUDIO NOT PLAYED] Skipped speaking and adding to history for this turn. Reasons: {'; '.join(reason_skipped)}")
                    print(f"[DEBUG] Skipped TTS: {'; '.join(reason_skipped)}")
                
                # Transition for continuous mode or stop
                if st.session_state.continuous_voice_mode_active:
                    st.session_state.voice_is_processing = False 
                    st.session_state.tts_cooldown_active = True 
                else: # Not continuous, so just mark processing as done
                    st.session_state.voice_is_processing = False 
                st.rerun()

            elif current_backend_status == "error":
                st.session_state.voice_error_message = backend_state.get("error_message", "Unknown error from backend.")
                st.session_state.voice_agent_response = backend_state.get("agent_response", st.session_state.voice_agent_response) # Preserve any partial agent response
                st.session_state.voice_is_processing = False 
                if st.session_state.continuous_voice_mode_active:
                    # Go to TTS cooldown to display error and allow user to see it before next cycle
                    st.session_state.tts_cooldown_active = True 
                st.rerun()
            
            elif backend_state.get("is_processing"): # Backend is still working (e.g., listening, recognizing, responding)
                # The main status display (st.info at the bottom) will show current_backend_status
                time.sleep(0.5) # Polling interval
                st.rerun()
            
            else: # Backend is not processing, and status is not 'complete' or 'error' (e.g., 'idle' unexpectedly)
                  # This is an ambiguous state. If continuous, it might recover via the waiting_for_backend_ready state.
                  # If not continuous, effectively stops.
                if not st.session_state.continuous_voice_mode_active:
                    st.session_state.voice_is_processing = False
                # If continuous, the main loop structure should handle transitioning.
                # For safety, if backend is not processing, we shouldn't be in this polling block long.
                # The tts_cooldown or waiting_for_backend states should take over if continuous.
                # If not continuous, setting voice_is_processing to False above handles it.
                # Let's rerun to allow state machine to progress.
                time.sleep(0.5) # Give a moment before re-evaluating states
                st.rerun()

        except requests.exceptions.RequestException as e:
            st.session_state.voice_error_message = f"Error connecting to backend (polling): {e}"
            st.session_state.voice_is_processing = False
            st.session_state.continuous_voice_mode_active = False # Stop continuous on connection error
            st.rerun()
        except Exception as e:
            st.session_state.voice_error_message = f"Unexpected error during voice polling: {e}"
            st.session_state.voice_is_processing = False
            st.session_state.continuous_voice_mode_active = False # Stop continuous on unexpected polling error
            st.rerun()

    # Display elements (always show based on session state)
    with status_container: 
        status_display = st.session_state.voice_status_message
        if st.session_state.continuous_voice_mode_active and status_display == "listening":
            status_display = "🎤 Listening continuously..."
        elif st.session_state.continuous_voice_mode_active and status_display == "recognizing":
            status_display = "🧠 Recognizing speech..."
        elif st.session_state.continuous_voice_mode_active and status_display == "responding":
            status_display = "💬 Agent is preparing response..."
        elif st.session_state.continuous_voice_mode_active and status_display == "initiating_listen":
            status_display = "🚀 Initiating next listen cycle..."
        elif not st.session_state.continuous_voice_mode_active and not st.session_state.voice_is_processing and status_display == "complete":
            status_display = "✅ Interaction complete. Start new session or switch mode."
        elif not st.session_state.continuous_voice_mode_active and not st.session_state.voice_is_processing and status_display == "error":
            status_display = "⚠️ Interaction ended with error. Start new session or switch mode."
        elif st.session_state.tts_cooldown_active:
            status_display = "🗣️ Agent is speaking..."

        # Main status display
        if st.session_state.voice_error_message:
            st.error(f"{st.session_state.voice_error_message}")
        elif status_display: # Check if status_display has content
            st.info(f"**Status:** {status_display}")
            
    if not st.session_state.voice_is_processing and \
       not st.session_state.continuous_voice_mode_active and \
       st.session_state.voice_status_message == "complete" and \
       not st.session_state.voice_error_message:
        st.success("Voice interaction cycle completed.")


def handle_text_interaction():
    # st.subheader("Text Chat")
    st.markdown("<h2 style='text-align: center;'>Text Chat</h2>", unsafe_allow_html=True)

    # Chat history display area
    chat_history_placeholder = st.container()
    with chat_history_placeholder:
        if st.session_state.text_conversation_history:
            st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
            for turn in st.session_state.text_conversation_history:
                if turn.get("role") == "user":
                    st.markdown(f"<div class='chat-bubble user-bubble'><b>You:</b> {turn.get('content')}</div>", unsafe_allow_html=True)
                elif turn.get("role") == "assistant":
                    st.markdown(f"<div class='chat-bubble assistant-bubble'><b>Assistant:</b> {turn.get('content')}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        if st.session_state.text_chat_error:
            st.error(f"Error: {st.session_state.text_chat_error}")

    # Input area at the bottom
    with st.form(key="text_chat_form", clear_on_submit=True):
        user_query = st.text_input("Ask Kroolo a question:", key="text_chat_input_form", placeholder="Type your message here...")
        submit_button = st.form_submit_button(label="✉️ Send")

    if submit_button and user_query:
        st.session_state.text_chat_error = ""
        st.session_state.text_chat_response = "" 

        current_user_message_for_history = {"role": "user", "content": user_query}
        st.session_state.text_conversation_history.append(current_user_message_for_history)
        
        # Trim history if it gets too long
        if len(st.session_state.text_conversation_history) > MAX_HISTORY_TURNS_STREAMLIT * 2:
            st.session_state.text_conversation_history = st.session_state.text_conversation_history[-(MAX_HISTORY_TURNS_STREAMLIT * 2):]

        # Prepare history for backend: send all turns *before* the current user's message
        history_to_send_to_backend = [
            turn for turn in st.session_state.text_conversation_history[:-1]
        ]

        try:
            response = requests.post(
                f"{BACKEND_URL}/chat", 
                json={"user_message": user_query, "conversation_history": history_to_send_to_backend}
            )
            response.raise_for_status()
            chat_data = response.json()
            agent_reply = chat_data.get("response", "No response received.")
            # st.session_state.text_chat_response = agent_reply # Not strictly needed if history is primary display
            st.session_state.text_chat_error = chat_data.get("error", "")
            
            if agent_reply and not st.session_state.text_chat_error:
                st.session_state.text_conversation_history.append({"role": "assistant", "content": agent_reply})
                # Trim again after adding assistant reply
                if len(st.session_state.text_conversation_history) > MAX_HISTORY_TURNS_STREAMLIT * 2:
                    st.session_state.text_conversation_history = st.session_state.text_conversation_history[-(MAX_HISTORY_TURNS_STREAMLIT * 2):]
                
        except requests.exceptions.RequestException as e:
            st.session_state.text_chat_error = f"Error connecting to backend: {e}"
        except Exception as e:
            st.session_state.text_chat_error = f"An unexpected error occurred: {e}"
        st.rerun() 
    elif submit_button and not user_query:
        st.warning("Please enter a question.")


if interaction_mode == "Voice":
    handle_voice_interaction()
elif interaction_mode == "Text":
    handle_text_interaction()

st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 Tips")
st.sidebar.info(
    "🎙️ **Voice Mode:** Ensure your microphone is enabled. Click 'Start Voice' for continuous interaction. "
    "The assistant will listen, respond, and then listen again automatically."
)
st.sidebar.info(
    "⌨️ **Text Mode:** Type your question and press Enter or click Send. The conversation will be displayed above."
)
st.sidebar.markdown("--- ")
st.sidebar.caption("Kroolo AI Assistant v1.0")
