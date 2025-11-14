__package__ = "backend"

from RAG.uploader import upload_RAG

def ask(question_text: str) -> str:
    return question_text

def upload(file_name:str):
    upload_RAG()

if __name__ == "__main__":
    upload("data")