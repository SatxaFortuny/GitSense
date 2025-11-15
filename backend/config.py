__package__ = "backend"

import os


EMBEDDING_MODEL = "mxbai-embed-large" 
CHAT_MODEL = "phi3"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIRECTORY = os.path.join(SCRIPT_DIR, "RAG", "data")
CHROMA_PATH = os.path.join(SCRIPT_DIR, "RAG", "GitSense_Knowledge_Database")