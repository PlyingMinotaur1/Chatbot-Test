import streamlit as st
import requests
import json
from base64 import b64encode
from langchain_groq import ChatGroq

# ----------------------------
# Load secrets from Streamlit
# ----------------------------
ADO_ORG = st.secrets["ADO_ORG"]       # e.g., "myorg"
ADO_PROJECT = st.secrets["ADO_PROJECT"]  # e.g., "MyProject"
ADO_PAT = st.secrets["ADO_PAT"]       # Personal Access Token
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# ----------------------------
# Chat history placeholder
# ----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

chat_placeholder = st.empty()
typing_placeholder = st.empty()

def render_chat():
    """Render chat messages."""
    with chat_placeholder.container():
        for entry in st.session_state.chat_history:
            with st.chat_message("user"):
                st.markdown(entry["user"])
            with st.chat_message("assistant"):
                st.markdown(entry["bot"])

# ----------------------------
# Ticket state
# ----------------------------
if "ticket_state" not in st.session_state:
    st.session_state.ticket_state = {
        "user_name": "",
        "user_email": "",
        "user_problem": "",
        "title": "",
        "description": "",
        "priority": 2,
        "step": "ask_name"
    }

# ----------------------------
# AI Model
# ----------------------------
model = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7,
    api_key=GROQ_API_KEY
)

def generate_ai_prompt(state):
    """Generate AI prompt for work item creation."""
    return f"""
    You are a support assistant. Create an Azure DevOps work item from this info:
    Name: {state['user_name']}
    Email: {state['user_email']}
    Problem: {state['user_problem']}

    Return JSON only with fields:
    - title: short work item title
    - description: detailed description
    - priority: 1=low, 2=medium, 3=high
    """

# ----------------------------
# Azure DevOps API
# ----------------------------
def create_ado_work_item(title, description, priority=2):
    url = f"https://dev.azure.com/{ADO_ORG}/{ADO_PROJECT}/_apis/wit/workitems/$Issue?api-version=7.0"
    
    # Azure DevOps expects JSON Patch content
    payload = [
        {"op": "add", "path": "/fields/System.Title", "value": title},
        {"op": "add", "path": "/fields/System.Description", "value": description},
        {"op": "add", "path": "/fields/Microsoft.VSTS.Common.Priority", "value": priority}
    ]
    
    auth_token = b64encode(f":{ADO_PAT}".encode()).decode()
    headers = {
        "Content-Type": "application/json-patch+json",
        "Authorization": f"Basic {auth_token}"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        try:
            work_item = response.json()
            return True, work_item.get("id", "unknown")
        except:
            return True, "unknown"
    else:
        return False, response.text

# ----------------------------
# Process user input
# ----------------------------
def process_input(user_input: str):
    state = st.session_state.ticket_state
    step = state["step"]
    bot_response = ""

    if step == "ask_name":
        state["user_name"] = user_input.strip()
        state["step"] = "ask_email"
        bot_response = "Thanks! What's your email address?"
    elif step == "ask_email":
        state["user_email"] = user_input.strip()
        state["step"] = "ask_problem"
        bot_response = "Great! Please describe the problem you are experiencing."
    elif step == "ask_problem":
        state["user_problem"] = user_input.strip()
        # Generate title/description using AI
        response = model.invoke(generate_ai_prompt(state))
        try:
            ticket_data = json.loads(response.content.strip().strip('`'))
            state["title"] = ticket_data.get("title", "Support Request")
            state["description"] = ticket_data.get("description", state["user_problem"])
            state["priority"] = ticket_data.get("priority", 2)
        except:
            state["title"] = "Support Request"
            state["description"] = state["user_problem"]
            state["priority"] = 2
        state["step"] = "confirm"
        bot_response = f"I will create a work item with title: \"{state['title']}\". Is this correct? (Yes/No)"
    elif step == "confirm":
        if user_input.lower() in ["yes", "y"]:
            success, work_item_id = create_ado_work_item(
                state["title"], state["description"], state["priority"]
            )
            if success:
                bot_response = f"✅ Work item created successfully! ID: {work_item_id}. Updates will be sent to {state['user_email']}."
            else:
                bot_response = f"❌ Failed to create the work item: {work_item_id}"
            state["step"] = "done"
        else:
            bot_response = "Okay, let's try again. Please describe your problem."
            state["step"] = "ask_problem"

    st.session_state.chat_history.append({"user": user_input, "bot": bot_response})
    render_chat()

# ----------------------------
# Streamlit UI
# ----------------------------
st.title("💬 Azure DevOps Support Chatbot")

render_chat()

if user_text := st.chat_input("Type your message..."):
    process_input(user_text)

# ----------------------------
# Run command reminder
# ----------------------------
# streamlit run Chatbot-Test/streamlit_app.py
