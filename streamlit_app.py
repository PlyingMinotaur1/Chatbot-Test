import streamlit as st
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

# Load variables from .env
load_dotenv()

# Access the key
groq_api_key = os.getenv("GROQ_API_KEY")

st.title("🤖 Groq Chatbot with Streamlit")

# Function to generate responses
def generate_response(input_text):
    model = ChatGroq(
        model="llama-3.1-8b-instant",  # You can switch to llama-3.1-70b if needed
        temperature=0.7,
        api_key=groq_api_key
    )
    response = model.invoke(input_text)
    st.info(response.content)

# Chat form
with st.form("my_form"):
    text = st.text_area(
        "Enter text:",
        "What are the three key pieces of advice for learning how to code?",
    )
    submitted = st.form_submit_button("Submit")

    # Validation
    if not groq_api_key:
        st.error("❌ No Groq API key found. Please set GROQ_API_KEY in your .env file.")
    elif submitted:
        generate_response(text)
