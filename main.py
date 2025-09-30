from fastapi import FastAPI
from routes import router

app = FastAPI(title="Election Chatbot API")

app.include_router(router)

@app.get("/")
def root():
    return {"message": "Election Chatbot API is running"}