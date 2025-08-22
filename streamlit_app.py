import streamlit as st
from langchain_groq import ChatGroq  # or DeepSeek if that's what you're using
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("🤖 Chatbot")

# Placeholders
chat_placeholder = st.empty()
typing_placeholder = st.empty()

def render_chat():
    """Render all chat messages."""
    with chat_placeholder.container():
        for entry in st.session_state.chat_history:
            with st.chat_message("user"):
                st.markdown(entry["user"])
            with st.chat_message("assistant"):
                st.markdown(entry["bot"])

def clean_response(text: str) -> str:
    """Remove unwanted tokens like <think> from the start of responses."""
    cleaned = text.strip()
    if cleaned.startswith("<think>"):
        cleaned = cleaned[len("<think>"):].strip()
    return cleaned

def generate_response(user_input):
    """Send user input to the model and update chat."""
    # Show typing indicator above input
    typing_placeholder.markdown("💬 Bot is typing...")

    model = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.7,
        api_key=groq_api_key
    )

    # Build context from chat history
    context = ""
    for entry in st.session_state.chat_history:
        context += f"User: {entry['user']}\nBot: {entry['bot']}\n"
    context += f"User: {user_input}\n"

    response = model.invoke(context)

    # Clean the response
    response_text = clean_response(response.content)

    # Remove typing indicator and update chat history
    typing_placeholder.empty()
    st.session_state.chat_history.append({"user": user_input, "bot": response_text})
    render_chat()

# Initial render
render_chat()

# Chat input
user_text = st.chat_input("Type your message...")

if user_text and groq_api_key:
    generate_response(user_text)


        #   streamlit run /workspaces/blank-app/streamlit_app.py