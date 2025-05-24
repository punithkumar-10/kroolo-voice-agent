import os
import asyncio
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.google import Gemini
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
import speech_recognition as sr
import time
import pyttsx3 # Keep the import
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import uvicorn

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY not found")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found")

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
expected_dimension = embedding_model.get_sentence_embedding_dimension()

pinecone = Pinecone(api_key=PINECONE_API_KEY)
index_name = "kroolo"
existing_indexes = [idx.name for idx in pinecone.list_indexes()]
if index_name not in existing_indexes:
    print(f"Index '{index_name}' not found. Creating new index with dimension {expected_dimension} for model 'all-MiniLM-L6-v2'.")
    pinecone.create_index(
        name=index_name,
        dimension=expected_dimension,
        metric="cosine",
        spec=ServerlessSpec(cloud='aws', region='us-east-1')
    )
    for _ in range(10):
        if index_name in [idx.name for idx in pinecone.list_indexes()]:
            print(f"Index '{index_name}' created successfully.")
            break
        time.sleep(2)
    else:
        print(f"Warning: Index '{index_name}' might not be ready after waiting.")
else:
    try:
        index_description = pinecone.describe_index(index_name)
        actual_dimension = index_description.dimension
        print(f"Using existing index '{index_name}' with dimension {actual_dimension}.")
        if actual_dimension != expected_dimension:
            print(f"CRITICAL WARNING: Index dimension {actual_dimension} does not match model dimension {expected_dimension}.")
    except Exception as e:
        print(f"Error describing existing index '{index_name}': {e}.")

index = pinecone.Index(index_name)

def embed_text(text):
    return embedding_model.encode([text])[0].tolist()

def search_kroolo_help_context(query, top_k=2):
    query_vector = embed_text(query)
    try:
        results = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            include_values=False,
            namespace="kroolo-docs"
        )
        if hasattr(results, 'matches') and results.matches:
            score_threshold = 0.1
            context_texts = [
                match.metadata['text'] for match in results.matches
                if 'text' in match.metadata and hasattr(match, 'score') and match.score > score_threshold
            ]
            return context_texts
        return []
    except Exception as e:
        print(f"Error during Pinecone query: {e}")
        return []

def retrieve_context_for_query(query, top_k=2):
    return search_kroolo_help_context(query, top_k=top_k)

help_specialist_agent = Agent(
    name="Kroolo Platform Assistant",
    role="Provides expert assistance and information regarding the Kroolo platform.",
    model=Gemini(id="gemini-2.0-flash", api_key=os.getenv("GEMINI_API_KEY")),
    instructions=[
        "*Objective:* Your primary goal is to be an exceptionally helpful Kroolo Platform Assistant. Strive to understand the user\\'s intent, provide clear, accurate, and actionable information about Kroolo, and guide them effectively. Be conversational and engaging.",
        "*Input Structure:* User queries are framed with optional conversation history and mandatory context data: \\'[Optional: ---CONVERSATION HISTORY START---\\n[dialogue history]\\n---CONVERSATION HISTORY END---\\n\\n]Context Data:\\n---CONTEXT START---\\n[retrieved data or \\'No context data available.\\']\\n---CONTEXT END---\\n\\nUser Query:\\n[user\\'s query]\\']",

        "*1. Understanding the User & Conversation History:*",
        "   a. *Analyze History:* If \\'---CONVERSATION HISTORY START---\\' is present, carefully review it to grasp the ongoing dialogue, understand user goals, resolve ambiguities (like pronouns), and address follow-up questions naturally.",
        "   b. *Infer Intent:* Go beyond the literal query. Try to understand what the user is truly trying to achieve with Kroolo.",
        "   c. *Interpreting \\'Kroolo\\' and its Variations:* Users might mispronounce or misspell \\'Kroolo\\' (e.g., \\'Crewlo\\', \\'Croolo\\', \\'Cruelo\\', \\'Kroolu\\', \\'Krooloo\\', \\'Kuru lu\\', \\'Groolo\\', \\'Coolo\\', \\'Krool\\', \\'Krola\\'). Silently interpret these variations as references to \\'Kroolo\\'. **Never point out the misspelling or ask for clarification on the platform\\'s name if a phonetically similar term is used.** Simply proceed as if they correctly said \\'Kroolo\\'. Your primary goal is to assist them with the platform they are asking about, which you should understand to be Kroolo even with these variations.",

        "*2. Core Operational Protocol: Kroolo Inquiry Resolution*",
        "   a. *Deconstruct Query:* Meticulously analyze the \\'User Query\\'. If it includes a greeting, acknowledge it briefly and professionally, then focus on the core request.",
        "   b. *Context Data - Your Primary Resource:*",
        "      i. *Synthesize, Don\\'t Just Extract:* If \\'Context Data\\' is available and relevant, use it as your primary source. However, do not simply copy phrases. Understand the information and rephrase it in a helpful, explanatory way. Integrate it seamlessly into your response.",
        "      ii. *Embody the Kroolo (or \\'Cruelo\\', etc.) Assistant Persona:* You ARE the assistant for the Kroolo platform (which users might call \\'Cruelo\\', \\'Crollo\\', etc., as per instruction 1.c). All your knowledge, whether from \\'Context Data\\' or general training, should be presented as your inherent expertise of this platform. Speak directly and authoritatively. **Crucially, you must AVOID phrases like \\'Based on the context...\\', \\'The Kroolo Help Center says...\\', \\'According to the information provided...\\', \\'It appears to offer...\\' or any similar meta-references to the source of the information.** Similarly, never mention that the user might have misspelled the platform\\'s name. The user believes they are talking to an expert *from* and *about* Kroolo (or their version of its name). Maintain this persona consistently. For example, if context indicates Kroolo aids in task management, state confidently: \\'Yes, Kroolo (or \\'we\\' when speaking as the platform\\'s assistant) helps you manage tasks efficiently by...\\' or \\'We offer robust tools for task management, allowing you to...\\'. The user should feel they are talking directly to an expert from Kroolo.",
        "      iii. *Descriptive Power:* If context describes Kroolo's purpose, features, or benefits (even through titles like 'Kroolo User Guide'), use this to build a comprehensive understanding and explanation, especially for definitional queries (e.g., 'What is Kroolo?').",
        "      iv. *Partial or Indirect Context:* If context is only partially relevant or hints at an answer, use your reasoning to provide the most helpful response possible. Acknowledge if you're making a logical inference based on the available information if necessary for clarity, but aim for a confident answer.",
        "   c. *General Kroolo Knowledge:* If \\'Context Data\\' is \\'No context data available,\\' insufficient, or the query is general, draw upon your broad knowledge of the Kroolo platform. Your responses should be consistent whether drawing from specific context or general knowledge, without explicitly stating the source to the user.",
        "   d. *Response Formulation:*",
        "      i. *Clear & Actionable:* Provide detailed, step-by-step instructions if applicable. Use formatting like bullet points or numbered lists for clarity, but express these lists in natural language suitable for speech (e.g., \\'First, do this. Second, do that.\\' instead of using markdown lists).",
        "      ii. *Conversational & Helpful:* Adopt a friendly, professional, and supportive tone. Anticipate follow-up questions if appropriate.",
        "      iii. *TTS-Friendly Formatting (CRITICAL):* Your responses WILL be converted to speech. Therefore, you MUST AVOID using any symbols or markdown that are read literally and awkwardly by text-to-speech systems. **Under NO circumstances should you use asterisks (`*`) for any purpose (emphasis, lists, etc.).** Instead of `* item 1, * item 2`, use natural language like \\'First, item 1. Second, item 2.\\' or structure lists narratively. For emphasis, use phrasing or word choice, not symbols. Prioritize clear spoken communication ABSOLUTELY over visual markdown formatting. Non-compliance with this rule will result in poor user experience.",

        "*3. Specific Query Handling Directives:*",
        "   a. *Identity Query ('Who are you?'):* If the query is solely 'who are you?', respond: 'I am the Kroolo Platform Assistant, an AI designed to provide expert support and guidance for the Kroolo platform. How can I help you with Kroolo today?'",
        "   b. *Capabilities Inquiry ('What can you do?'):* Respond by outlining your function: 'As the Kroolo Platform Assistant, I can help you understand Kroolo's features, explain how to use the platform, guide you through troubleshooting, and offer best practices. For example, I can explain how to set up a new project, manage your tasks, or collaborate with your team. What Kroolo topic are you interested in?' If relevant context is available, you can add: 'For instance, Kroolo is great for [mention 1-2 key capabilities from data].'",
        "   c. *Simple Greetings (e.g., 'hi', 'hello'):* If the query is just a greeting, respond: 'Hello! I am the Kroolo Platform Assistant. How can I assist you with the Kroolo platform today?' Avoid giving substantive answers based on context retrieved for a simple greeting.",
        "   d. *'How to' / Procedural Queries (e.g., 'How do I create an account?'):*",
        "      i. *Prioritize Context:* If context provides steps, synthesize them clearly.",
        "      ii. *General Knowledge Fallback:* If context is missing or insufficient for a common Kroolo procedure (like account creation, password reset, etc.), provide a general, logical set of steps based on typical platform behavior. For example: 'To create an account in Kroolo, you would typically go to the Kroolo website, look for a Sign Up or Create Account button, and then follow the on-screen instructions, which usually involve providing an email address and creating a password. You might also be asked for other details like your name or company.'",
        "      iii. *If Truly Unknown:* If it's a very specific or advanced procedure not in context or general knowledge, state: 'I don't have specific step-by-step instructions for that particular process in my current knowledge. Generally, for [task type], you would look for [relevant section/menu] in Kroolo. For detailed guidance, the Kroolo Help Center or support team would be the best resource.'",
        "   e. *Comparative Queries (e.g., 'How is Kroolo better than Asana?', 'Why choose Kroolo over Trello?'):*",
        "      i. *Acknowledge and Frame:* Acknowledge the comparative nature of the query. For example: 'That's a great question. When comparing Kroolo to other platforms like [Other Platform Name if mentioned, otherwise \\'similar tools\\'], it\\'s helpful to look at what makes Kroolo stand out.'",
        "      ii. *Highlight Kroolo's Strengths:* Based on your general knowledge of Kroolo's core features and benefits, emphasize what makes Kroolo a strong choice. Focus on aspects like its intuitive interface designed for seamless collaboration, powerful project visualization tools, flexible workflow automation, or integrated AI-powered assistance for task management and insights. You can tailor these examples based on what you know Kroolo excels at.",
        "      iii. *Focus on Value, Not Direct Attack:* Frame Kroolo's advantages positively. Avoid directly criticizing or making unsubstantiated negative claims about other platforms. The goal is to showcase Kroolo's value.",
        "      iv. *If Other Platform is Unknown:* If the specific competitor is obscure or you lack detailed knowledge about it, you can say: 'While I don\\'t have a detailed feature-by-feature comparison for every platform, Kroolo excels in areas such as [reiterate Kroolo\\'s key strengths]. Many users find these aspects particularly beneficial for [mention use cases like \\'managing complex projects\\' or \\'enhancing team productivity\\'].' ",
        "      v. *Encourage Exploration:* Conclude by inviting the user to explore Kroolo further or ask about specific features: 'Would you like to know more about any of these specific Kroolo features, or perhaps how Kroolo handles a particular task you have in mind?'",

        "*4. Managing Informational Gaps & Ambiguity:*",
        "   a. *Insufficient Information:* If you cannot adequately address a specific Kroolo-related question after consulting context and general knowledge, state this clearly: 'I don't have the specific information about [topic] right now. For detailed assistance, you might want to check the official Kroolo documentation or contact Kroolo support. Is there anything else about Kroolo I can help you with?'",
        "   b. *Clarification:* If a query is vague or ambiguous, ask clarifying questions to better understand the user's need before attempting an answer. For example: 'Could you tell me a bit more about what you're trying to do in Kroolo?'",

        "*5. General Professional Conduct:*",
        "   a. *Tone & Style:* Maintain a highly professional, yet friendly, approachable, and expert tone. Language should be clear, concise, and confident. Avoid jargon where possible, or explain it.",
        "   b. *Helpfulness First:* Always aim to be as helpful as possible within your role as a Kroolo assistant.",
        "   c. *Self-Identification:* Only use your full title as per directive #3a, #3b, or #3c. In other interactions, focus on assisting the user.",
        "   d. *Avoid Speculation:* Do not make up information or features that don't exist. Stick to what's known from context or general platform knowledge."
    ],
    add_datetime_to_instructions=True,
)

async def get_agent_response_async(user_message: str, conversation_history: list[dict[str, str]]) -> str:
    try:
        retrieved_texts = retrieve_context_for_query(user_message)
        context_for_prompt = "No context found."
        if retrieved_texts:
            full_context = "\\n\\n".join(retrieved_texts)
            max_context_length = 2000 
            context_for_prompt = full_context[:max_context_length] + ("... [context truncated]" if len(full_context) > max_context_length else "")

        history_for_prompt = ""
        if conversation_history:
            formatted_history_turns = []
            prompt_history_window = conversation_history[-(MAX_HISTORY_TURNS_FOR_PROMPT * 2):] 
            for turn in prompt_history_window:
                if turn.get('content'):
                    formatted_history_turns.append(f"{turn['role'].capitalize()}: {turn['content']}")
            if formatted_history_turns:
                history_for_prompt = (
                    "---CONVERSATION HISTORY START---\\n"
                    f"{'\\n'.join(formatted_history_turns)}\\n"
                    "---CONVERSATION HISTORY END---\\n\\n"
                )

        # Construct the prompt for the agent
        query_with_context_and_history = (
            f"{history_for_prompt}"
            f"Context Data:\\n---CONTEXT START---\\n{context_for_prompt}\\n---CONTEXT END---\\n\\n"
            f"User Question:\\n{user_message}"
        )

        response_obj = await help_specialist_agent.arun(query_with_context_and_history, stream=False)

        if response_obj:
            raw_response = str(response_obj.content).strip() if hasattr(response_obj, 'content') and response_obj.content else str(response_obj).strip()
            import re
            cleaned_response = re.sub(r"  +", " ", raw_response)
            return cleaned_response.strip()
        return "Error: No response received from the specialist agent."
    except Exception as e:
        import traceback
        print(f"Error in get_agent_response_async: {e}")
        traceback.print_exc()
        return f"I encountered a critical error processing your request: {str(e)}"


MAX_HISTORY_TURNS_FOR_PROMPT = 5

recognizer = sr.Recognizer() 

# --- TTS Voice Selection and Speaking is now handled within speak_text_sync ---

def speak_text_sync(text_to_speak):
    tts_success = False
    engine = None  
    try:
        print("Speak (Backend): Initializing pyttsx3 engine...")
        engine = pyttsx3.init()
        if engine is None:
            print("Speak (Backend): CRITICAL - pyttsx3.init() returned None. Cannot speak.")
            return False 
        
        if hasattr(engine, '_inLoop') and engine._inLoop:
            try:
                print("Speak (Backend): Engine was in loop, attempting endLoop().")
                engine.endLoop()
                print("Speak (Backend): endLoop() called. Re-initializing engine.")
                engine = pyttsx3.init() 
                if engine is None:
                    print("Speak (Backend): CRITICAL - pyttsx3.init() after endLoop returned None.")
                    return False
            except Exception as e_loop:
                print(f"Speak (Backend): Error during endLoop/re-init: {e_loop}")
                return False 

        voices = engine.getProperty('voices')
        selected_voice_id = None
        current_voice_name = "default"

        preferred_voice_names = [
            "Microsoft Zira Desktop - English (United States)",
            "Microsoft David Desktop - English (United States)"
        ]

        for preferred_name in preferred_voice_names:
            for voice in voices:
                if voice.name == preferred_name:
                    selected_voice_id = voice.id
                    current_voice_name = voice.name
                    break
            if selected_voice_id:
                break
        
        if not selected_voice_id and voices:
            selected_voice_id = voices[0].id 
            current_voice_name = voices[0].name
            print(f"Speak (Backend): Preferred voices not found, using fallback: {current_voice_name}")
        
        if selected_voice_id:
            engine.setProperty('voice', selected_voice_id)
            print(f"Speak (Backend): Using voice: {current_voice_name}")
        else:
            print("Speak (Backend): CRITICAL - No voices found for TTS. Cannot speak.")
            return False 

        print(f"Speak (Backend): Attempting to say: '{text_to_speak[:70].replace(chr(10), " ") + "..." if len(text_to_speak) > 70 else text_to_speak.replace(chr(10), " ")}'")
        engine.say(text_to_speak)
        engine.runAndWait()
        print("Speak (Backend): runAndWait completed.")
        import sys
        sys.stdout.flush() 
        tts_success = True
    except RuntimeError as e:
        print(f"Speak (Backend): RuntimeError in speak_text_sync (often indicates engine issues): {e}")
        if engine and hasattr(engine, '_inLoop') and engine._inLoop:
            try:
                engine.endLoop()
            except Exception as el:
                print(f"Speak (Backend): Error trying to endLoop on RuntimeError: {el}")
    except Exception as e:
        print(f"Speak (Backend): General error in speak_text_sync: {e}")
    finally:
        try:
            if engine is not None:
                engine.stop()  
        except Exception as stop_exc:
            print(f"Speak (Backend): Exception during engine.stop(): {stop_exc}")
        print(f"Speak (Backend): Exiting speak_text_sync. Success: {tts_success}")
        return tts_success


# --- FastAPI Setup ---
app = FastAPI()

# --- Pydantic Models ---
class QueryRequest(BaseModel):
    user_message: str
    conversation_history: list[dict[str, str]] = []

class VoiceInitiateRequest(BaseModel):
    conversation_history: list[dict[str, str]] = []

class SpeakRequest(BaseModel):
    text: str

class VoiceInteractionManager:
    def __init__(self):
        self.is_processing: bool = False
        self.user_speech: str | None = None
        self.agent_response: str | None = None
        self.error_message: str | None = None
        self.status_message: str = "idle" 

    def reset(self):
        self.user_speech = None
        self.agent_response = None
        self.error_message = None

voice_interaction_manager = VoiceInteractionManager()

async def process_single_voice_interaction(current_conversation_history: list[dict[str, str]]):
    global voice_interaction_manager
    try:
        voice_interaction_manager.reset()
        voice_interaction_manager.is_processing = True 
        voice_interaction_manager.status_message = "listening"
        print("Background task: Listening...")

        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            recognizer.pause_threshold = 1.2
            print("Background task: Listening for speech (pause_threshold=1.2s, phrase_time_limit=20s, timeout=7s)...")
            audio = recognizer.listen(source, phrase_time_limit=20, timeout=7)

        voice_interaction_manager.status_message = "recognizing"
        print("Background task: Recognizing...")
        text = recognizer.recognize_google(audio)
        voice_interaction_manager.user_speech = text
        print(f"Background task: Recognized text: {text}")

        history_for_agent = current_conversation_history + [{"role": "user", "content": text}]

        voice_interaction_manager.status_message = "responding"
        print("Background task: Getting agent response...")
        answer = await get_agent_response_async(text, history_for_agent)
        voice_interaction_manager.agent_response = answer
        print(f"Background task: Agent response: {answer}")
        
        voice_interaction_manager.status_message = "complete"

    except sr.WaitTimeoutError:
        voice_interaction_manager.error_message = "No speech detected."
        voice_interaction_manager.status_message = "error"
        print("Background task: WaitTimeoutError")
    except sr.UnknownValueError:
        voice_interaction_manager.error_message = "Could not understand audio."
        voice_interaction_manager.status_message = "error"
        print("Background task: UnknownValueError")
    except sr.RequestError as e:
        voice_interaction_manager.error_message = f"Speech recognition service error: {e}"
        voice_interaction_manager.status_message = "error"
        print(f"Background task: RequestError: {e}")
    except Exception as e:
        print(f"Background task: General error: {e}")
        voice_interaction_manager.error_message = f"An unexpected error occurred during voice processing: {str(e)}"
        voice_interaction_manager.status_message = "error"
    finally:
        voice_interaction_manager.is_processing = False
        print(f"Background task: Processing finished. Status: {voice_interaction_manager.status_message}")

#API Endpoints
@app.post("/chat")
async def http_chat(request: QueryRequest):
    answer = await get_agent_response_async(request.user_message, request.conversation_history)
    return {"response": answer}

@app.post("/speak")
async def http_speak(request: SpeakRequest):
    try:
        print(f"Speak (API): Received request to speak: '{request.text[:50]}...'")
        success = await asyncio.to_thread(speak_text_sync, request.text)
        
        if success:
            print("Speak (API): TTS reported success.")
            return {"status": "success", "message": "Speech completed successfully."}
        else:
            print("Speak (API): TTS reported failure.")
            return {"status": "error", "message": "TTS engine failed to speak or encountered an internal issue."}
    except Exception as e:
        print(f"Speak (API): Error in /speak endpoint: {e}")
        return {"status": "error", "message": f"An unexpected error occurred in the speak endpoint: {str(e)}"}

@app.post("/voice/initiate")
async def initiate_voice_interaction_endpoint(request: VoiceInitiateRequest, background_tasks: BackgroundTasks):
    if voice_interaction_manager.is_processing:
        return {"status": "error", "message": "A voice interaction is already in progress. Please wait or check status."}
    
    voice_interaction_manager.reset()
    voice_interaction_manager.is_processing = True
    voice_interaction_manager.status_message = "queued"
    
    background_tasks.add_task(process_single_voice_interaction, list(request.conversation_history))
    return {"status": "success", "message": "Voice interaction processing initiated."}

@app.get("/voice/status")
async def get_voice_interaction_status():
    return {
        "is_processing": voice_interaction_manager.is_processing,
        "user_speech": voice_interaction_manager.user_speech,
        "agent_response": voice_interaction_manager.agent_response,
        "error_message": voice_interaction_manager.error_message,
        "status_message": voice_interaction_manager.status_message,
    }

async def cli_listen_and_ask_async(conversation_history: list[dict[str, str]]):
    print("[Listening mode ON. Say 'stop listening' to exit. Speak now!]")
    speak_text_sync("Listening mode is on. How can I help you with Kroolo?")
    while True:
        print("Speak now...")
        with sr.Microphone() as source:
            try:
                recognizer.adjust_for_ambient_noise(source, duration=0.2)
                audio = recognizer.listen(source)
                text = recognizer.recognize_google(audio)
                print(f"You said: {text}")

                if text.strip().lower() in ["stop listening", "stop", "exit"]:
                    print("[Listening mode OFF]")
                    speak_text_sync("Listening mode off.")
                    break

                conversation_history.append({"role": "user", "content": text})
                answer = await get_agent_response_async(text, conversation_history)
                print(answer)
                speak_text_sync(answer)
                if not answer.startswith("I encountered a critical error"):
                    conversation_history.append({"role": "assistant", "content": answer})
                if len(conversation_history) > MAX_HISTORY_TURNS_FOR_PROMPT * 2:
                    conversation_history[:] = conversation_history[-(MAX_HISTORY_TURNS_FOR_PROMPT * 2):]
            except sr.WaitTimeoutError:
                print("No speech detected.")
            except sr.UnknownValueError:
                print("Could not understand audio.")
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
            except Exception as e:
                print(f"Error in listening loop: {e}")

async def cli_main():
    conversation_history: list[dict[str, str]] = []
    while True:
        user_message = input("Ask your Kroolo question (or type 'exit' or 'listen'): ")
        if user_message.strip().lower() == 'exit':
            break
        if user_message.strip().lower() == 'listen':
            await cli_listen_and_ask_async(conversation_history)
            continue

        conversation_history.append({"role": "user", "content": user_message})
        answer = await get_agent_response_async(user_message, conversation_history)
        print(answer)
        if not answer.startswith("I encountered a critical error"):
            conversation_history.append({"role": "assistant", "content": answer})
        if len(conversation_history) > MAX_HISTORY_TURNS_FOR_PROMPT * 2:
            conversation_history[:] = conversation_history[-(MAX_HISTORY_TURNS_FOR_PROMPT * 2):]

if __name__ == "__main__":
    print("Starting Kroolo AI Assistant with FastAPI server...")
    print("Access the API at http://127.0.0.1:8000")
    print("Example endpoint: POST to http://127.0.0.1:8000/chat with JSON body like:")
    print('{ "user_message": "What is Kroolo?", "conversation_history": [] }')
    print("To run the CLI for voice, type 'listen' in the separate CLI input prompt after starting this server.")

    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)
    
    if os.name == 'nt' and isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    async def main_with_server():
        await server.serve()

    asyncio.run(main_with_server())