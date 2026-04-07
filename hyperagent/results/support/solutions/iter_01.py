import string
import re

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version extracts keywords from the question, searches the
    knowledge base for sentences containing these keywords, and constructs
    an answer from the most relevant snippets found.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    # 1. Pre-process question to extract relevant keywords
    question_lower = question.lower()
    # Remove punctuation from the question
    question_cleaned = question_lower.translate(str.maketrans('', '', string.punctuation))
    question_words = set(question_cleaned.split())

    # A basic list of common stop words to filter out noise from keywords
    stop_words = {"a", "an", "the", "is", "are", "was", "were", "and", "or", "for", "on", "in", "with", 
                  "how", "what", "where", "when", "why", "can", "could", "may", "might", "do", "does", 
                  "did", "of", "to", "from", "at", "about", "this", "that", "these", "those", "it", 
                  "its", "you", "your", "we", "our", "us", "i", "my", "me", "he", "him", "his", "she", 
                  "her", "hers", "they", "them", "their", "which", "who", "whom", "whose", "if", "then", 
                  "but", "not", "no", "yes", "please", "thank", "would", "will", "shall", "should", 
                  "get", "got", "go", "goes", "going", "have", "has", "had", "been", "be", "being", "am"}
    
    # Filter out stop words and keep content words (words longer than 2 characters)
    relevant_question_words = {word for word in question_words if word not in stop_words and len(word) > 2}

    # If no relevant keywords are found after filtering, return a generic but slightly more helpful response
    if not relevant_question_words:
        return "Thank you for your question. While I couldn't identify specific keywords, please visit our comprehensive FAQ page or contact customer support for more information."

    # 2. Pre-process knowledge base: Split into sentences and score them
    knowledge_base_lower = knowledge_base.lower()
    
    # A simple regex for splitting the knowledge base into sentences
    # It splits on '.', '!', '?' followed by a space, but keeps the punctuation.
    sentences = re.split(r'(?<=[.!?])\s+', knowledge_base_lower)

    scored_sentences = []

    for sentence in sentences:
        # Clean sentence for word comparison
        sentence_cleaned = sentence.translate(str.maketrans('', '', string.punctuation))
        sentence_words = set(sentence_cleaned.split())
        
        score = 0
        # Calculate a score based on how many relevant question keywords are in the sentence
        for q_word in relevant_question_words:
            if q_word in sentence_words:
                score += 1
        
        if score > 0:  # Only consider sentences that contain at least one matching keyword
            scored_sentences.append((score, sentence))

    # 3. Construct Answer from relevant snippets
    if not scored_sentences:
        # If no sentences in the knowledge base contained any relevant keywords
        return "I apologize, but I couldn't find information directly matching your question in the knowledge base. Please try rephrasing your question or consult our detailed product documentation."

    # Sort sentences by their score in descending order
    scored_sentences.sort(key=lambda x: x[0], reverse=True)

    relevant_snippets = []
    # Take the top N (e.g., 3) most relevant sentences
    for score, sentence_lower in scored_sentences:
        # Ensure the sentence is not empty after stripping whitespace
        processed_sentence = sentence_lower.strip()
        if not processed_sentence:
            continue
        
        # Capitalize the first letter of the sentence for better readability
        processed_sentence = processed_sentence[0].upper() + processed_sentence[1:]

        # Ensure the sentence ends with proper punctuation
        if not processed_sentence.endswith(('.', '!', '?')):
            processed_sentence += '.'
        
        relevant_snippets.append(processed_sentence)
        
        # Limit the number of snippets to avoid overly long answers
        if len(relevant_snippets) >= 3:
            break

    if relevant_snippets:
        # Join the selected snippets to form the final answer
        # A prefix indicates that the answer is derived from the knowledge base
        return "Based on our knowledge base: " + " ".join(relevant_snippets)
    else:
        # Fallback if, after all processing and filtering, no snippets are left
        return "I couldn't find a direct answer to your question in the provided knowledge base. Please check our website or contact support."