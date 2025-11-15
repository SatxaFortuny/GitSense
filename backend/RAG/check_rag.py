import logging
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from config import CHROMA_PATH, EMBEDDING_MODEL

# Set up logging, just like in your uploader
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def view_all_chunks():
    logging.info("--- Connecting to existing RAG database ---")

    # 1. Initialize the embedding model
    # We need this to tell Chroma how to "understand" text
    try:
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        logging.info(f"Embedding model loaded: {EMBEDDING_MODEL}")
    except Exception as e:
        logging.error(f"Error loading embedding model: {e}")
        return

    # 2. Connect to the existing, persisted database
    # Note: We use Chroma() directly, not Chroma.from_documents()
    try:
        vectorstore = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=embeddings
        )
        logging.info(f"Connected to database at: {CHROMA_PATH}")
    except Exception as e:
        logging.error(f"Error connecting to ChromaDB. Is the path correct?: {e}")
        return

    # 3. Fetch all chunks
    # The .get() method retrieves documents and metadata from the collection
    all_chunks = vectorstore.get(include=["metadatas", "documents"])
    
    documents = all_chunks.get("documents", [])
    metadatas = all_chunks.get("metadatas", [])

    if not documents:
        logging.warning("No chunks found in the database.")
        return

    logging.info(f"--- Found {len(documents)} total chunks ---")

    # 4. Loop and print
    for i, (doc, meta) in enumerate(zip(documents, metadatas)):
        print(f"\n--- CHUNK {i + 1} ---")
        
        # Print metadata
        if meta:
            print("Metadata:")
            for key, value in meta.items():
                print(f"  {key}: {value}")
        
        # Print the actual text content
        print("\nContent:")
        print(doc)
        print("-" * 30) # Separator

    logging.info("--- Finished viewing all chunks ---")

if __name__ == "__main__":
    view_all_chunks()