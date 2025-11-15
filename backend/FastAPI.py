__package__ = "backend"
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_ollama import OllamaEmbeddings
import uvicorn
from GitSense import ask
from config import EMBEDDING_MODEL, CHROMA_PATH, CHAT_MODEL
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def inicializations():
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[], 
        
        allow_origin_regex=r"http://127\.0\.0\.1:.*", 
        
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    try:
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    except Exception as e:
        logging.error(f"Embedding model failure. Error: {e}")

    vectorstore = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings
    )

    agent = OllamaLLM(model=CHAT_MODEL)
    return app, embeddings, vectorstore, agent

app, embeddings, vectorstore, agent = inicializations()

# -------------------------------------

@app.get("/ask_question")
def handle_ask_question(question: str):
    response_text = ask(question, vectorstore, agent)
    return {"answer": response_text}

if __name__ == "__main__":
    print("Starting server in http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)

# uvicorn backend.FastAPI:app --host 127.0.0.1 --port 8000 --reload --reload-dir backend/RAG/GitSense_Knowledge_Database