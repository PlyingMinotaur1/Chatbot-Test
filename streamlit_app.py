import streamlit as st
import requests
import json
from langchain_groq import ChatGroq  # or your AI library

# ----------------------------
# Load secrets
# ----------------------------
OSTICKET_URL = st.secrets["OSTICKET_URL"]
OSTICKET_API_KEY = st.secrets["OSTICKET_API_KEY"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# ----------------------------
# AI Model Setup
# ----------------------------
model = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7,
    api_key=GROQ_API_KEY
)

# ----------------------------
# Ticket creation function
# ----------------------------
def create_ticket(name, email, subject, message, priority=3):
    data = {
        "name": name,
        "email": email,
        "subject": subject,
        "message": message,
        "priority": priority
    }
    headers = {
        "X-API-Key": OSTICKET_API_KEY,
        "Content-Type": "application/json"
    }
    response = requests.post(OSTICKET_URL, json=data, headers=headers)
    if response.status_code == 201:
        try:
            ticket_info = response.json()  # Try parsing JSON
        except ValueError:
            ticket_info = {}  # fallback if no JSON returned
        return True, ticket_info
    else:
        return False, response.text

# ----------------------------
# Clean AI output before JSON parsing
# ----------------------------
def clean_ai_json(raw_text):
    cleaned = raw_text.strip()
    
    # Remove leading/trailing backticks
    if cleaned.startswith("```"):
        cleaned = cleaned.lstrip("`").strip()
    if cleaned.endswith("```"):
        cleaned = cleaned.rstrip("`").strip()
    
    # Take only up to the last closing brace
    last_brace = cleaned.rfind("}")
    if last_brace != -1:
        cleaned = cleaned[:last_brace+1]
    
    return cleaned

# ----------------------------
# AI generates ticket (JSON-safe)
# ----------------------------
def ai_generate_ticket(user_description):
    prompt = f"""
    You are a support assistant. Convert this problem description into a JSON object with keys:
    - subject: short summary
    - message: detailed description
    - priority: 1=low, 2=medium, 3=high

    Return only valid JSON without any extra text or backticks.

    Problem: "{user_description}"
    """
    response = model.invoke(prompt)
    cleaned_text = clean_ai_json(response.content)
    
    try:
        ticket_data = json.loads(cleaned_text)
        return ticket_data
    except json.JSONDecodeError as e:
        st.error(f"AI failed to generate valid JSON: {e}\nRaw output: {response.content}")
        return None

# ----------------------------
# Streamlit UI
# ----------------------------
st.title("AI-Driven Ticket Creation with Review")

st.info("Describe your problem. AI will suggest a ticket, and you can review/edit before submitting.")

# User input
user_problem = st.text_area("Problem description")
name = st.text_input("Your Name")
email = st.text_input("Your Email")

# Step 1: Generate AI suggestion
if st.button("Generate Ticket Suggestion"):
    if not (user_problem and name and email):
        st.warning("Please fill out all fields.")
    else:
        ticket_fields = ai_generate_ticket(user_problem)
        if ticket_fields:
            st.session_state.suggested_subject = ticket_fields.get("subject", "")
            st.session_state.suggested_message = ticket_fields.get("message", "")
            st.session_state.suggested_priority = ticket_fields.get("priority", 2)  # default medium
            st.success("AI generated a ticket suggestion below. You can edit it before submitting.")

# Step 2: Review & edit AI suggestion
if "suggested_subject" in st.session_state:
    subject = st.text_input("Subject", value=st.session_state.suggested_subject)
    message = st.text_area("Message", value=st.session_state.suggested_message)
    
    # Priority mapping: 1=Low, 2=Medium, 3=High
    priority = st.selectbox(
        "Priority", 
        [1, 2, 3], 
        index=st.session_state.suggested_priority - 1,
        format_func=lambda x: {1:"Low", 2:"Medium", 3:"High"}[x]
    )

    if st.button("Submit Ticket"):
        success, result = create_ticket(
            name=name,
            email=email,
            subject=subject,
            message=message,
            priority=priority
        )
        if success:
            ticket_id = result.get('id', 'unknown') if isinstance(result, dict) else 'unknown'
            st.success(f"Ticket created successfully! Ticket ID: {ticket_id}")
        else:
            st.error(f"Error creating ticket: {result}")

# ----------------------------
# To run this app from terminal:
# streamlit run Chatbot-Test/streamlit_app.py
# ----------------------------
