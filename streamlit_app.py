import streamlit as st
import requests

# Load secrets
OSTICKET_URL = st.secrets["OSTICKET_URL"]
OSTICKET_API_KEY = st.secrets["OSTICKET_API_KEY"]

st.title("Create osTicket Support Ticket")

# Form fields
name = st.text_input("Your Name")
email = st.text_input("Your Email")
subject = st.text_input("Subject")
message = st.text_area("Message")
priority = st.selectbox("Priority", [1, 2, 3], index=2)

# Submit button
if st.button("Submit Ticket"):
    if not (name and email and subject and message):
        st.warning("Please fill out all fields before submitting.")
    else:
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
            st.success("Ticket created successfully!")
        else:
            st.error(f"Error creating ticket: {response.text}")
