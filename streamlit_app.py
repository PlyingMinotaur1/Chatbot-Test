import streamlit as st
import requests
import json
from langchain_groq import ChatGroq
from typing import TypedDict, List

# -------------------------
# Jira Configuration
# -------------------------
JIRA_URL = "https://aiticketingtest.atlassian.net/rest/api/2/issue"
JIRA_EMAIL = "chikams@live.com"
JIRA_PROJECT_KEY = "KAN"
JIRA_API_KEY = st.secrets["JIRA_API_KEY"]

# -------------------------
# ChatGroq Setup
# -------------------------
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
model = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7, api_key=GROQ_API_KEY)

# -------------------------
# Ticket State
# -------------------------
class TicketState(TypedDict):
    user_name: str
    user_email: str
    user_problem: str
    subject: str
    priority: int
    awaiting_confirmation: bool
    chat_history: List[dict]  # {"user": str, "bot": str}

# -------------------------
# Helper functions
# -------------------------
def map_priority_to_jira(priority: int) -> str:
    """Map numeric priority to Jira's 5-tier priority system."""
    mapping = {1: "Highest", 2: "High", 3: "Medium", 4: "Low", 5: "Lowest"}
    return mapping.get(priority, "Medium")  # default to Medium

def generate_ticket_subject_and_priority(problem: str) -> dict:
    """Generate a ticket subject and numeric priority (1-5) via ChatGroq."""
    prompt = f"""
You are a Jira assistant.
The user reported this problem: "{problem}"

Instructions:
- Generate a short subject line (max 60 characters, no quotes).
- Assign a priority: 1=Highest, 2=High, 3=Medium, 4=Low, 5=Lowest.
- Return ONLY valid JSON with keys "subject" and "priority".
- Example output:
{{"subject": "Example subject", "priority": 3}}
"""
    response = model.invoke([{"role": "user", "content": prompt}])
    try:
        result = json.loads(response.content.strip().strip("`"))
        result["priority"] = min(max(int(result.get("priority", 3)), 1), 5)
        return result
    except Exception:
        return {"subject": problem[:60], "priority": 3}

def create_jira_ticket(subject: str, description: str, email: str, priority: int) -> str:
    headers = {"Content-Type": "application/json"}
    auth = (JIRA_EMAIL, JIRA_API_KEY)
    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": subject,
            "description": f"{description}\n\nReported by: {email}",
            "issuetype": {"name": "Task"},
            "priority": {"name": map_priority_to_jira(priority)}
        }
    }
    response = requests.post(JIRA_URL, json=payload, headers=headers, auth=auth)
    if response.status_code == 201:
        return response.json()["key"]
    else:
        return f"Error: {response.status_code} - {response.text}"

# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title="💬 Jira Support Chatbot", layout="centered")
st.title("💬 Jira Support Chatbot")

# Initialize state
if "ticket_state" not in st.session_state:
    st.session_state.ticket_state = TicketState(
        user_name="",
        user_email="",
        user_problem="",
        subject="",
        priority=3,  # default Medium
        awaiting_confirmation=False,
        chat_history=[{"user": "", "bot": "Hi! I'm your Jira assistant. What's your name?"}]
    )

state = st.session_state.ticket_state

# Render existing chat history
for entry in state["chat_history"]:
    if entry["user"]:
        with st.chat_message("user"):
            st.write(entry["user"])
    if entry["bot"]:
        with st.chat_message("assistant"):
            st.write(entry["bot"])

# Chat input
if user_text := st.chat_input("Type your message..."):
    # Step 0: always append user message
    state["chat_history"].append({"user": user_text, "bot": None})

    # Step 1: determine bot reply
    if not state["user_name"]:
        state["user_name"] = user_text
        bot_reply = "Thanks! What's your email address?"

    elif not state["user_email"]:
        state["user_email"] = user_text
        bot_reply = "Great! Please describe the problem you are experiencing."

    elif not state["user_problem"]:
        state["user_problem"] = user_text
        result = generate_ticket_subject_and_priority(state["user_problem"])
        state["subject"] = result.get("subject", state["user_problem"][:60])
        state["priority"] = result.get("priority", 3)
        bot_reply = f'I will create a Jira ticket with title: "{state["subject"]}". Is this correct? (Yes/No)'
        state["awaiting_confirmation"] = True

    elif state["awaiting_confirmation"]:
        if user_text.lower() in ["yes", "y", "correct"]:
            ticket_id = create_jira_ticket(
                state["subject"],
                state["user_problem"],
                state["user_email"],
                state["priority"]
            )
            bot_reply = f"✅ Ticket created successfully! ID: {ticket_id}. Updates will be sent to {state['user_email']}."
            state["awaiting_confirmation"] = False
        elif user_text.lower() in ["no", "n", "incorrect"]:
            bot_reply = "Okay, please re-describe the problem so I can update the ticket title."
            state["user_problem"] = ""
            state["subject"] = ""
            state["priority"] = 3  # reset to Medium
            state["awaiting_confirmation"] = False
        else:
            bot_reply = "Please answer 'Yes' to create the ticket, or 'No' to retry."

    # Step 2: always append bot reply as a new entry
    state["chat_history"].append({"user": None, "bot": bot_reply})
    st.session_state.ticket_state = state

    # Step 3: render BOTH user + bot messages
    with st.chat_message("user"):
        st.write(user_text)
    with st.chat_message("assistant"):
        st.write(bot_reply)

# -------------------------
# Run command:
# streamlit run Chatbot-Test/streamlit_app.py
