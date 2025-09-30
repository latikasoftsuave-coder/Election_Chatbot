import streamlit as st
import requests
from datetime import datetime
import uuid

API_URL = "http://127.0.0.1:8000"

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("Chat2Vote Chatbot")

def load_history():
    try:
        response = requests.get(f"{API_URL}/analysis/{st.session_state.session_id}")
        data = response.json() or {}
        messages = data.get("messages",[])
        st.session_state.chat_history = messages
    except Exception as e:
        st.error(f"Error loading chat history: {e}")

if not st.session_state.chat_history:
    load_history()

for msg in st.session_state.chat_history:
    if msg["role"]=="user":
        with st.chat_message("user"):
            st.write(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.write(msg["content"])

if user_input := st.chat_input("Ask a question..."):
    with st.chat_message("user"):
        st.write(user_input)

    try:
        today_date = datetime.utcnow().strftime("%Y-%m-%d")
        payload = {
            "question": user_input,
            "date": today_date
        }

        params = {"session_id": st.session_state.session_id}
        response = requests.post(f"{API_URL}/ask", json=payload, params=params)
        data = response.json()

        if "answer" in data:
            answer = data["answer"]
            with st.chat_message("assistant"):
                st.write(answer)

            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.utcnow().isoformat()
            })

            st.session_state.chat_history.append({
                "role":"assistant",
                "content": answer,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            st.error(data.get("error", "No answer returned"))

    except Exception as e:
        st.error(f"Error connecting to backend: {e}")