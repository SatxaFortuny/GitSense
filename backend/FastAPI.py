__package__ = "backend"
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from backend.GitSense import ask

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[], 
    
    allow_origin_regex=r"http://127\.0\.0\.1:.*", 
    
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# -------------------------------------

@app.get("/ask_question")
def handle_ask_question(question: str):
    response_text = ask(question)
    return {"answer": response_text}

if __name__ == "__main__":
    print("Starting server in http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)

# uvicorn backend.FastAPI:app --host 127.0.0.1 --port 8000 --reload --reload-dir backend/RAG/GitSense_Knowledge_Database