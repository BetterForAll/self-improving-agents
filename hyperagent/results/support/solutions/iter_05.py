def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    import re

    # Define common English stop words. This list can be expanded for better filtering.
    # Placed inside the function to ensure the output contains ONLY the function definition.
    STOP_WORDS = {
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"
    }

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
    knowledge_chunks = [chunk.strip() for chunk in re.split(r'(?<=[.!?])\s+', knowledge_base) if chunk.strip()]

    best_match = ""
    max_score = 0

    # Iterate through each chunk in the knowledge base to find the best matching sentence.
    for chunk in knowledge_chunks:
        chunk_lower = chunk.lower()
        score = 0
        # Calculate score by counting the frequency of each keyword within the chunk,
        # ensuring whole word matches using word boundaries (\b).
        for keyword in keywords:
            # Use re.escape to handle any special regex characters that might be in a keyword.
            score += len(re.findall(r'\b' + re.escape(keyword) + r'\b', chunk_lower))
        
        # Determine if the current chunk is a better match:
        # 1. A higher score (more matching keywords or higher frequency) is always preferred.
        # 2. If scores are equal, prefer a shorter answer (more concise) if it's not the initial empty string
        #    and if there's an actual positive score.
        if score > max_score:
            max_score = score
            best_match = chunk
        elif score == max_score and score > 0 and len(chunk) < len(best_match):
            best_match = chunk

    if max_score > 0:
        # If a relevant chunk was found, return it as the answer.
        return best_match.strip()
    else:
        # If no keywords matched any chunks, or knowledge_base was empty, return a fallback.
        return "Thank you for contacting us. We couldn't find a direct answer to your question in our knowledge base. Please try rephrasing or check our website."