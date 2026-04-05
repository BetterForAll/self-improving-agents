import re

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version identifies keywords in the question and attempts to find
    the most relevant sentence in the knowledge base by counting shared keywords.
    It leverages built-in string methods, regex for tokenization and sentence
    splitting, and sets for efficient keyword matching.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    if not knowledge_base or not question:
        return "Thank you for contacting us. We could not process your request with the provided information."

    # --- 1. Preprocess Question for Keywords ---
    # Normalize question: lowercase, extract word tokens using regex, and store as a set
    # for efficient lookup (O(1) average time complexity).
    question_tokens = set(re.findall(r'\b\w+\b', question.lower()))
    
    # Define a set of common stop words to filter out less relevant words.
    # This reduces noise and focuses on core concepts, improving relevance matching.
    stop_words = {"a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
                  "and", "or", "but", "if", "then", "else", "for", "with", "at", "by",
                  "of", "on", "in", "to", "from", "up", "down", "out", "off", "over",
                  "under", "again", "further", "then", "once", "here", "there", "when",
                  "where", "why", "how", "all", "any", "both", "each", "few", "more",
                  "most", "other", "some", "such", "no", "nor", "not", "only", "own",
                  "same", "so", "than", "too", "very", "s", "t", "can", "will", "just",
                  "don", "should", "now", "what", "which", "who", "whom", "this", "that",
                  "these", "those", "me", "my", "myself", "we", "our", "ours", "ourselves",
                  "you", "your", "yours", "yourself", "yourselves", "he", "him", "his",
                  "himself", "she", "her", "hers", "herself", "it", "its", "itself",
                  "they", "them", "their", "theirs", "themselves"}
    
    # Filter out stop words to get a set of relevant keywords from the question.
    relevant_question_words = question_tokens - stop_words

    if not relevant_question_words:
        # If no relevant keywords are found, the question might be too generic.
        return "Thank you for contacting us. Please provide a more specific question."

    # --- 2. Process Knowledge Base and Identify Most Relevant Sentence ---
    # Split the knowledge base into individual sentences.
    # The regex uses a positive lookbehind to ensure the delimiter ('.', '?', '!')
    # is kept as part of the sentence, improving readability of the extracted sentence.
    # `\s*` handles optional whitespace after punctuation.
    # Filtering `if s.strip()` removes any empty strings resulting from the split.
    sentences = [s.strip() for s in re.split(r'(?<=[.?!])\s*', knowledge_base) if s.strip()]
    
    best_match_score = 0
    best_answer_sentence = None

    for sentence in sentences:
        # For each sentence, normalize it (lowercase) and extract word tokens into a set.
        sentence_words = set(re.findall(r'\b\w+\b', sentence.lower()))
        
        # Calculate a relevance score: the number of common words between the
        # relevant question keywords and the sentence's words.
        # Set intersection is an efficient way to find common elements.
        current_score = len(relevant_question_words.intersection(sentence_words))

        # Update the best match if the current sentence has a higher score.
        if current_score > best_match_score:
            best_match_score = current_score
            best_answer_sentence = sentence # Store the original (stripped) sentence

    # --- 3. Formulate the Answer ---
    if best_answer_sentence and best_match_score > 0:
        # If a relevant sentence was found with at least one matching keyword, return it.
        return best_answer_sentence
    else:
        # Fallback response if no relevant sentence could be identified.
        return "Thank you for contacting us. We couldn't find a direct answer in our knowledge base. Please visit our website for more information."