import logging
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

DATA_PATH = "backend/RAG/data"
CHROMA_PATH = "backend/RAG/GitSense_Knowledge_Database"
EMBEDDING_MODEL = "nomic-embed-text" 
CHUNK_SIZE = 300
CHUNK_OVERLAP = 100

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def upload_RAG():
    logging.info("Starting RAG uploader...")
    # First of all we load all the pdfs in the "data" folder
    loader = PyPDFDirectoryLoader(DATA_PATH)
    documents = loader.load()
    if not documents:
        logging.warning(f"Data folder empty: {DATA_PATH}")
        return 0
    logging.info(f"Loaded {len(documents)} PDF files.")

    # Now we split those documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len
    )
    chunks = text_splitter.split_documents(documents)
    logging.info(f"{len(chunks)} new chunks created.")

    # Now we try to inicialize the embedding model.
    logging.info(f"Inicializing embedding model: {EMBEDDING_MODEL}")
    try:
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    except Exception as e:
        logging.error(f"Embedding model failure. Error: {e}")
        return 0
    
    logging.info(f"Uploading chunks into the database: {CHROMA_PATH}")
    
    vectorstore = Chroma.from_documents(
        documents=chunks,           
        embedding=embeddings,       
        persist_directory=CHROMA_PATH 
    )
    
    logging.info("Uploaded succesful.")