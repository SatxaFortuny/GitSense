__package__ = "backend"

import os
import logging
from langchain_community.document_loaders import PyPDFLoader, TextLoader, JSONLoader
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
    HTMLHeaderTextSplitter,
    Language
)
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from config import EMBEDDING_MODEL, CHROMA_PATH, SOURCE_DIRECTORY

TEXT_CHUNK_SIZE = 1000      # The chunk lenght in characters
TEXT_CHUNK_OVERLAP = 200    # In order to have more senseful chunks, the have bits of neighbour chunks

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".java", ".cs", ".cpp", ".c", ".h", ".hpp",
    ".go", ".rb", ".php", ".swift", ".kt", ".scala", ".rs"
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Now we will proceed to process and load into the RAG files of various extensions.
"""
    Loads a PDF file and splits it using a 'brute-force' recursive strategy.
    When converting the PDF file, we lose the typical structure, 
    that's why it uses basic chunking in which it only splits by counting characters.
"""
def load_pdf(file_path):
    logging.info(f"Processing PDF: {file_path}")
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=TEXT_CHUNK_SIZE,
        chunk_overlap=TEXT_CHUNK_OVERLAP
    )
    chunks = text_splitter.split_documents(documents)
    return chunks

"""
    Loads a Markdown file and splits it intelligently based on its structure.
    
    This uses MarkdownHeaderTextSplitter, a 'structured' splitter that understands Markdown syntax (like #, ##). It creates chunks based on
    headers, ensuring that logically related content stays together. This results in far more coherent and semantically relevant chunks
    for the RAG system compared to a recursive split (as seen above).
"""
def load_markdown(file_path):
    logging.info(f"Processing Markdown: {file_path}")
    loader = TextLoader(file_path, encoding="utf-8")
    document = loader.load()
    headers_to_split_on = [
        ("#", "H1"),
        ("##", "H2"),
        ("###", "H3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        return_each_line=False
    )
    markdown_text = document[0].page_content 
    chunks = markdown_splitter.split_text(markdown_text)
    return chunks

"""
    Loads a source code file and splits it with semantic awareness of the language.
    
    This uses a structured splitter that is specifically aware of the language's syntax. 
    It avoids splitting in the middle of a function or class, preferring to create chunks that
    represent complete logical blocks of code. This is crucial for providing useful context for coding-related questions.
"""
def load_code_file(file_path, language):
    logging.info(f"Processing code ({language.value}): {file_path}")
    loader = TextLoader(file_path, encoding="utf-8")
    documents = loader.load()
    code_splitter = RecursiveCharacterTextSplitter.from_language(
        language=language,
        chunk_size=TEXT_CHUNK_SIZE,
        chunk_overlap=TEXT_CHUNK_OVERLAP
    )
    chunks = code_splitter.split_documents(documents)
    return chunks

"""
    Loads an HTML file and splits it intelligently based on its structure.
    
    Similar to the Markdown splitter, this 'structured' splitter uses HTML header tags (<h1>, <h2>) to divide the content. 
    This respects the document's intended layout and keeps semantic sections grouped together, leading to much higher-quality chunks.
"""
def load_html(file_path):
    logging.info(f"Processing HTML: {file_path}")
    loader = TextLoader(file_path, encoding="utf-8")
    document = loader.load()
    headers_to_split_on = [
        ("h1", "H1"),
        ("h2", "H2"),
        ("h3", "H3"),
    ]
    html_splitter = HTMLHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        return_each_line=False
    )
    html_text = document[0].page_content
    chunks = html_splitter.split_text(html_text)
    return chunks

"""
    Loads a plain text file (.txt) and splits it using the basic recursive strategy.
    
    Like PDFs, plain text files have no reliable semantic structure for a splitter to use. Therefore, we use the default 
    RecursiveCharacterTextSplitter to simply chunk the text by the amount of characters.
"""
def load_plain_text(file_path):
    logging.info(f"Processing .txt: {file_path}")
    loader = TextLoader(file_path, encoding="utf-8")
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=TEXT_CHUNK_SIZE,
        chunk_overlap=TEXT_CHUNK_OVERLAP
    )
    chunks = text_splitter.split_documents(documents)
    return chunks

"""
    Scans the directory and aplies a loading function based on its extension.
"""
def load_and_split_documents(source_dir):
    chunks = []
    # recursively searches for files
    for root, _, files in os.walk(source_dir):
        for file in files:
            # now we unify the path into a single string in order to extract the extension
            file_path = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower()
            # now that we have the extension we can call each separate load function according to the extension
            try:
                if ext == ".pdf":
                    chunks.extend(load_pdf(file_path))
                elif ext == ".md":
                    chunks.extend(load_markdown(file_path))
                elif ext == ".html":
                    chunks.extend(load_html(file_path))
                elif ext == ".txt":
                    chunks.extend(load_plain_text(file_path))
                elif ext in CODE_EXTENSIONS:
                    # translates the extension into its language
                    if ext == ".py": lang = Language.PYTHON
                    elif ext == ".js": lang = Language.JS
                    elif ext == ".java": lang = Language.JAVA
                    else: lang = Language.PYTHON    # Python is the basic mode if we don't have a load function for that specific language
                    chunks.extend(load_code_file(file_path, lang))  
                else:
                    logging.warning(f"Extension not supported for file: {file_path}")
            except Exception as e:
                logging.error(f"File processing error {file_path}: {e}")
    return chunks

def main():
    logging.info("--- Starting RAG uploading ---")
    all_chunks = load_and_split_documents(SOURCE_DIRECTORY)
    if not all_chunks:
        logging.warning("No chunks generated.")
        return
    logging.info(f"{len(all_chunks)} chunks generated.")
    logging.info(f"Starting embedding model: {EMBEDDING_MODEL}")
    try:
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    except Exception as e:
        logging.error(f"Embedding model error: {e}")
        return
    logging.info(f"Loading {len(all_chunks)} chunks into the BD: {CHROMA_PATH}")
    vectorstore = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )
    logging.info("--- Uploading completed ---")

if __name__ == "__main__":
    main()