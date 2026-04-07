import re

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    # Handle invalid or empty question input
    if not isinstance(question, str) or not question.strip():
        return "Please provide a valid question."
    
    # Handle invalid or empty knowledge_base input
    if not isinstance(knowledge_base, str) or not knowledge_base.strip():
        return "Thank you for contacting us. We need more information to answer your question."

    question_lower = question.lower()
    
    # Split the knowledge base into sentences.
    # This regex attempts to split on . ? ! followed by a space,
    # while trying to avoid splitting on decimal points or abbreviations (e.g., U.S.A.).
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s+', knowledge_base)
    # Filter out any empty strings that might result from splitting
    sentences = [s.strip() for s in sentences if s.strip()]

    # Extract all words from the question, convert to lowercase
    all_question_words = set(re.findall(r'\b\w+\b', question_lower))

    # A basic set of common English stop words.
    # These words are usually not informative keywords for answering a question.
    stop_words = {"a", "an", "the", "is", "are", "was", "were", "be", "been", "being", "to", "of", "and", "or",
                  "in", "on", "at", "for", "with", "from", "by", "about", "what", "which", "who", "whom", "where",
                  "when", "why", "how", "can", "could", "would", "should", "will", "may", "might", "must", "do",
                  "does", "did", "have", "has", "had", "not", "no", "don't", "can't", "i", "you", "he", "she",
                  "it", "we", "they", "me", "him", "her", "us", "them", "my", "your", "his", "its", "our",
                  "their", "this", "that", "these", "those", "if", "then", "else", "but", "so", "as", "such",
                  "than", "up", "down", "out", "off", "over", "under", "again", "further", "once", "here",
                  "there", "all", "any", "both", "each", "few", "more", "most", "other", "some", "same",
                  "too", "very", "s", "t", "just", "now", "ve", "ll", "d", "m", "re", "y", "am"}

    # Filter out stop words and single-letter words to get meaningful keywords for matching
    question_keywords = {word for word in all_question_words if word not in stop_words and len(word) > 1}

    best_sentence = ""
    max_matches = 0 # Stores the count of matching keywords for the best sentence found

    # If no meaningful keywords can be extracted from the question, it's too generic
    if not question_keywords:
        return "Thank you for contacting us. Please provide a more specific question."

    # Pre-process the question for the exact phrase match:
    # Remove all punctuation and extra whitespace to create a normalized phrase.
    # This makes the phrase matching more robust against punctuation differences.
    normalized_question_phrase = re.sub(r'[^\w\s]', '', question_lower).strip()

    # Iterate through each sentence in the knowledge base to find the most relevant one
    for sentence in sentences:
        sentence_lower = sentence.lower()
        
        # Count how many of the question's keywords appear in the current sentence
        current_matches = sum(1 for keyword in question_keywords if keyword in sentence_lower)
        
        # Improvement: Make the exact phrase match more robust to punctuation.
        # If the question (as a phrase, normalized for punctuation) is found within a normalized sentence,
        # it's a very strong indicator of relevance. Boost its score significantly.
        # This prioritizes direct answers where the question itself is part of the KB,
        # even if punctuation in the question differs from the knowledge base.
        if normalized_question_phrase: # Ensure there's a meaningful phrase to search for
            normalized_sentence_phrase = re.sub(r'[^\w\s]', '', sentence_lower).strip()
            if normalized_question_phrase in normalized_sentence_phrase:
                 current_matches += len(question_keywords) * 2 # A substantial boost

        # Update best_sentence if current sentence has more matches
        if current_matches > max_matches:
            max_matches = current_matches
            best_sentence = sentence.strip()

    # Determine if the best found sentence is relevant enough to be an answer
    question_keywords_count = len(question_keywords)
    
    # A match is considered good if it meets one of these criteria:
    # 1. At least 2 relevant keywords are found AND at least half of the question's keywords are matched.
    #    This prevents returning weak matches for longer questions.
    # 2. If it's a very specific question with only one primary keyword (e.g., "Pricing?")
    #    and that single keyword is found.
    if max_matches > 0:
        if (max_matches >= 2 and max_matches >= question_keywords_count / 2.0) or \
           (question_keywords_count == 1 and max_matches == 1):
            return best_sentence
            
    # Fallback to a more informative generic response if no sufficiently relevant answer is found
    return "Thank you for contacting us. We couldn't find a direct answer in our knowledge base. Please visit our website or contact support for more information."