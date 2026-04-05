import re

def answer_question(question: str, knowledge_base: str) -> str:
    """Answer a customer question using the knowledge base.

    Args:
        question: The customer's question.
        knowledge_base: Product information text.

    Returns: The answer.
    """
    # Define common English stop words. This list can be expanded for better filtering.
    # Lazily initialize STOP_WORDS once on the first call to improve performance,
    # while keeping it self-contained within the function definition as per task constraints.
    if not hasattr(answer_question, '_STOP_WORDS_CACHE'):
        answer_question._STOP_WORDS_CACHE = {
            'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"
        }
    STOP_WORDS = answer_question._STOP_WORDS_CACHE # Reference the lazily initialized set

    question_lower = question.lower()
    # Extract keywords from the question: alphanumeric words, longer than 2 characters,
    # and not present in the stop words list. This helps focus on meaningful terms.
    keywords = set(word for word in re.findall(r'\b\w+\b', question_lower)
                   if len(word) > 2 and word not in STOP_WORDS)

    if not keywords:
        # If no meaningful keywords are extracted, return a fallback response.
        return "Thank you for contacting us. Please rephrase your question with more specific details so we can assist you better."

    # Split the knowledge base into potential answer chunks (sentences).
    # This regex splits after a period, question mark, or exclamation mark followed by whitespace.
    # It also filters out empty strings from the split result.
    knowledge_chunks_raw = [chunk.strip() for chunk in re.split(r'(?<=[.!?])\s+', knowledge_base) if chunk.strip()]

    best_match = ""
    max_score = 0

    # Pre-process knowledge chunks into sets of words for efficient whole-word matching.
    # This avoids repeatedly tokenizing and lowercasing chunks inside the scoring loop.
    processed_chunks = []
    for original_chunk in knowledge_chunks_raw:
        chunk_lower = original_chunk.lower()
        # Using a regex to find words in the chunk for accurate whole-word matching.
        chunk_words = set(re.findall(r'\b\w+\b', chunk_lower))
        processed_chunks.append((original_chunk, chunk_words)) # Store original chunk and its word set

    # Iterate through each processed chunk to find the best matching sentence.
    for original_chunk, chunk_word_set in processed_chunks:
        score = 0
        # Count how many unique keywords from the question are present as whole words in the current chunk.
        for keyword in keywords:
            if keyword in chunk_word_set: # Now it's a whole-word match, which is more precise.
                score += 1
        
        # Determine if the current chunk is a better match:
        # 1. A higher score (more matching keywords) is always preferred.
        # 2. If scores are equal, prefer a shorter answer (more concise) if it's not the initial empty string.
        #    Ensuring `score > 0` avoids picking an irrelevant short string over another irrelevant long string
        #    when max_score is still 0 (i.e., no relevant match found yet).
        if score > max_score:
            max_score = score
            best_match = original_chunk
        elif score == max_score and score > 0 and len(original_chunk) < len(best_match):
            best_match = original_chunk

    if max_score > 0:
        # If a relevant chunk was found, return it as the answer.
        # original_chunk (stored in best_match) is already stripped.
        return best_match
    else:
        # If no keywords matched any chunks, or knowledge_base was empty, return a fallback.
        return "Thank you for contacting us. We couldn't find a direct answer to your question in our knowledge base. Please try rephrasing or check our website."