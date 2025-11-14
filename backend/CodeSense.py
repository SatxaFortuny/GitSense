__package__ = "backend"

from time import sleep


def ask(question_text: str) -> str:

    print(f"Question received: {question_text}")
    sleep(1) 
    
    return question_text