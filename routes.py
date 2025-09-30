from fastapi import APIRouter, Query
from pydantic import BaseModel
from services import ChatService

router = APIRouter()

class Question(BaseModel):
    question: str

@router.post("/ask")
def ask_question(q: Question, session_id: str = Query(None)):
    return ChatService.process_user_question(q.question, session_id)

@router.get("/analysis/{session_id}")
def get_analysis(session_id: str):
    return ChatService.get_or_update_analysis(session_id)