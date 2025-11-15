__package__ = "backend"
from config import EMBEDDING_MODEL
import logging

SIMILARITY_SCORE_THRESHOLD = 0.7

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def ask(question_text: str, vectorstore, agent) -> str:
    try:
        context=obtain_RAG_context(question_text, vectorstore)
        PROMPT_TEMPLATE = """
        Here you have some context in order to respond the question. If "context:" is empty, it means there is no relevant context, and you should mention it to the user.

        Context:
        {context}

        --- END OF CONTEXT ---

        Question: {question}

        Answer:
        """
        final_prompt = PROMPT_TEMPLATE.format(context=context, question=question_text)
        logging.info(f"prompt: {final_prompt}")
        messages = [
            {'role': 'user', 'content': final_prompt}
        ]
        response = agent.invoke(final_prompt)
        return response
    except Exception as e:
        error_msg = f"Ollama (phi-3) connection error: {e}"
        return error_msg
    
def obtain_RAG_context(question_text: str, vectorstore):
    logging.info(f"Transforming the prompt into a embedding using: {EMBEDDING_MODEL}")
    chunks=vectorstore.similarity_search_with_score(question_text, k=10) # We only obtain the best k chunks
    context = ""
    good_matches = 0
    for chunk, distance in chunks:
        logging.info(f"Chunk score: {distance}")
        # If the distance is greater it means it isn't actually similar
        
        if distance < SIMILARITY_SCORE_THRESHOLD:
            logging.info("Chunk accepted.")
            context += chunk.page_content + "\n\n"
            good_matches += 1
        else:
            logging.info("Chunk denied.")

    if good_matches == 0:
        logging.warning(f"No decent matches found.")
        return ""
    
    return context

if __name__ == "__main__":
    upload("data")