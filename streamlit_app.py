import streamlit as st
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
import time

# Load environment variables
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("🤖 Groq Chatbot")

# Placeholder for chat messages
chat_placeholder = st.empty()
# Placeholder for typing indicator (above input)
typing_placeholder = st.empty()

def render_chat():
    """Render all chat messages in the placeholder."""
    with chat_placeholder.container():
        for entry in st.session_state.chat_history:
            with st.chat_message("user"):
                st.markdown(entry["user"])
            with st.chat_message("assistant"):
                st.markdown(entry["bot"])

def generate_response(user_input):
    """Generate response from Groq and update chat history."""
    # Show typing indicator above input
    typing_placeholder.markdown("💬 Bot is typing...")

    model = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.7,
        api_key=groq_api_key
    )

    # Build context from history
    context = ""
    for entry in st.session_state.chat_history:
        context += f"User: {entry['user']}\nBot: {entry['bot']}\n"
    context += f"User: {user_input}\n"

    response = model.invoke(context)

    # Remove typing indicator and append new message
    typing_placeholder.empty()
    st.session_state.chat_history.append({"user": user_input, "bot": response.content})
    render_chat()  # Immediately show the new message

# Initial render
render_chat()

# Chat input (fires immediately on Enter)
user_text = st.chat_input("Type your message...")

if user_text:
    generate_response(user_text)


        #   streamlit run /workspaces/blank-app/streamlit_app.py