import os
import openai
from datetime import datetime
from db import SessionLocal, ChatMessage, Analysis
from dotenv import load_dotenv
import json
import uuid
import re

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

class ChatService:
    @staticmethod
    def store_user_message(session_id: str, content: str):
        db = SessionLocal()
        try:
            msg = ChatMessage(
                session_id=session_id,
                role="user",
                content=content,
                timestamp=datetime.utcnow()
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)
            return msg
        finally:
            db.close()

    @staticmethod
    def store_assistant_message(session_id: str, content: str):
        db = SessionLocal()
        try:
            msg = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=content,
                timestamp=datetime.utcnow()
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)
            return msg
        finally:
            db.close()

    @staticmethod
    def get_last_messages(session_id: str, limit: int = 10):
        db = SessionLocal()
        try:
            msgs = (
                db.query(ChatMessage)
                .filter(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.id.desc())
                .limit(limit)
                .all()
            )
            return [{"role": m.role, "content": m.content} for m in reversed(msgs)]
        finally:
            db.close()

    @staticmethod
    def generate_response(messages: list):
        system_prompt = {
            "role": "system",
            "content": (
                "You are an Election Officer in India. "
                "Always consider the last conversation messages and respond consistently. "
                "Collect user information if missing (name, email, age, citizenship)."
            )
        }
        message_with_system = [system_prompt] + messages
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=message_with_system
        )
        return response.choices[0].message.content

    @staticmethod
    def update_analysis(session_id: str, last_messages: list):
        db = SessionLocal()
        try:
            context = "\n".join([f"{m['role']}: {m['content']}" for m in last_messages])
            prompt = (
                "You are an Election Officer in India. Extract eligibility information from the conversation. "
                "Reply ONLY with valid JSON (no explanations, no text outside JSON). "
                "Always include all keys: is_eligible, reason, name, email. "
                "If a value is unknown, set it to null. "
                f"Conversation:\n{context}"
            )

            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": prompt}]
            )

            raw_output = response.choices[0].message.content.strip()

            json_match = re.search(r"{.*}", raw_output, re.DOTALL)
            if json_match:
                try:
                    ai_output = json.loads(json_match.group())
                except json.JSONDecodeError:
                    ai_output = {}
            else:
                ai_output = {}

            analysis = db.query(Analysis).filter(Analysis.session_id == session_id).first()
            if not analysis:
                analysis = Analysis(session_id=session_id)
                db.add(analysis)
                db.commit()
                db.refresh(analysis)

            if "is_eligible" in ai_output and ai_output["is_eligible"] is not None:
                analysis.is_eligible = ai_output["is_eligible"]
            if "reason" in ai_output and ai_output["reason"]:
                analysis.reason = ai_output["reason"]
            if "name" in ai_output and ai_output["name"]:
                analysis.name = ai_output["name"]
            if "email" in ai_output and ai_output["email"]:
                analysis.email = ai_output["email"]

            analysis.last_updated = datetime.utcnow()

            db.commit()
            db.refresh(analysis)
            return analysis

        finally:
            db.close()

    @staticmethod
    def process_user_question(question: str, session_id: str = None):
        if not session_id:
            session_id = str(uuid.uuid4())
        print(session_id)

        ChatService.store_user_message(session_id, question)
        messages = ChatService.get_last_messages(session_id, limit=10)

        today_date = datetime.utcnow().strftime("%Y-%m-%d")
        system_message = {
            "role": "system",
            "content": f"Today's date is {today_date}. Use this information when answering questions."
        }
        messages = [system_message] + messages

        answer = ChatService.generate_response(messages)
        ChatService.store_assistant_message(session_id, answer)
        ChatService.update_analysis(session_id, messages + [{"role": "assistant", "content": answer}])
        return {"answer": answer}

    @staticmethod
    def get_or_update_analysis(session_id: str):
        db = SessionLocal()
        try:
            analysis = db.query(Analysis).filter(Analysis.session_id == session_id).first()
            if analysis:
                db.refresh(analysis)
                return {
                    "session_id": analysis.session_id,
                    "is_eligible": analysis.is_eligible,
                    "reason": analysis.reason,
                    "name": analysis.name,
                    "email": analysis.email,
                    "last_updated": analysis.last_updated.isoformat() if analysis.last_updated else None
                }

            messages = ChatService.get_last_messages(session_id, limit=10)
            updated_analysis = ChatService.update_analysis(session_id, messages)
            return {
                "session_id": updated_analysis.session_id,
                "is_eligible": updated_analysis.is_eligible,
                "reason": updated_analysis.reason,
                "name": updated_analysis.name,
                "email": updated_analysis.email,
                "last_updated": updated_analysis.last_updated.isoformat()
            }
        finally:
            db.close()
