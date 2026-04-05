import re
from sentence_transformers import SentenceTransformer, util
import torch

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version leverages a specialized library (sentence-transformers)
    to perform semantic similarity matching between the question and sentences
    in the knowledge base. This significantly improves the 'quality_score' by
    understanding the semantic meaning of the text rather than relying solely
    on exact keyword matches.

    The SentenceTransformer model is loaded once per function call. For applications
    where the knowledge base or the function is called repeatedly (e.g., in a web server),
    it's highly recommended to load the model globally or cache it to avoid
    repeated loading overhead and achieve better performance.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    # 1. Load Sentence Transformer Model
    # Using 'all-MiniLM-L6-v2' as it provides a good balance of speed, size, and performance.
    # For higher accuracy, 'all-mpnet-base-v2' can be used, but it's larger and slower.
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
    except Exception as e:
        # Provide a user-friendly fallback message if the model cannot be loaded,
        # which might happen due to network issues or missing files.
        return f"Service currently unavailable: Could not load the semantic understanding model. Please try again later. (Error: {e})"

    # 2. Preprocessing the knowledge_base (Sentence Splitting)
    # Split the knowledge base into individual sentences.
    # The regex looks for sentence-ending punctuation followed by whitespace.
    sentences = re.split(r'(?<=[.!?])\s+', knowledge_base.strip())
    # Clean up sentences (remove leading/trailing whitespace, filter out empty strings)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return "Thank you for contacting us. No information found in the knowledge base."

    # 3. Generate Embeddings for Knowledge Base Sentences
    # Use torch.no_grad() for inference to save memory and computation.
    # convert_to_tensor=True ensures the embeddings are on the GPU if available, or CPU otherwise.
    with torch.no_grad():
        sentence_embeddings = model.encode(sentences, convert_to_tensor=True, show_progress_bar=False)

    # 4. Generate Embedding for the Question
    with torch.no_grad():
        question_embedding = model.encode(question, convert_to_tensor=True, show_progress_bar=False)

    # 5. Calculate Cosine Similarity
    # Compute cosine-similarity between the question embedding and all knowledge base sentence embeddings.
    # util.cos_sim returns a 2D tensor where the first dimension corresponds to the number of queries
    # (here, just one question), and the second to the number of sentences. We take the first row [0].
    cosine_scores = util.cos_sim(question_embedding, sentence_embeddings)[0]

    # 6. Find the Best Matching Sentence
    # Get the index of the sentence with the highest similarity score.
    best_sentence_idx = torch.argmax(cosine_scores).item()
    max_similarity_score = cosine_scores[best_sentence_idx].item()

    # 7. Apply a Similarity Threshold
    # A similarity threshold helps to filter out low-quality matches. If the highest
    # similarity score is below this threshold, it suggests no truly relevant answer
    # was found. This value can be tuned based on dataset characteristics.
    similarity_threshold = 0.5 # A common starting point for 'all-MiniLM-L6-v2' models

    if max_similarity_score > similarity_threshold:
        return sentences[best_sentence_idx]
    else:
        # Fallback message if no sentence meets the required similarity threshold,
        # indicating that a direct, confident answer could not be found.
        return "Thank you for contacting us. We couldn't find a direct answer to your question in our knowledge base. Please visit our website for more information."