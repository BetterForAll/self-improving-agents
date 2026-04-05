import re

# Define stop words at the module level to avoid re-initialization on every function call.
# Expanded to include common contractions that regex might treat as single words.
_STOP_WORDS = {"a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
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
                  "they", "them", "their", "theirs", "themselves", "i", "you'd", "you'll", "you're", "you've", "we'd", "we'll", "we're", "we've", "it's", "he's", "she's", "they're", "they've", "they'd", "i'm", "i've", "i'd", "i'll"}

def _tokenize_and_filter(text):
    """
    Helper function to tokenize text into words, convert to lowercase, and remove
    common stop words. Returns a set of relevant keywords for efficient lookup.
    """
    tokens = set(re.findall(r'\b\w+\b', text.lower()))
    return tokens - _STOP_WORDS

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version identifies keywords in the question and attempts to find
    the most relevant sentence in the knowledge base by counting shared keywords.
    It leverages built-in string methods, regex for tokenization and sentence
    splitting, and sets for efficient keyword matching.

    Improvements:
    1.  **Algorithmic Consistency & Efficiency**: Introduced a `_tokenize_and_filter`
        helper function to ensure consistent text processing (tokenization, lowercasing,
        and stop-word removal) for both the question and knowledge base sentences.
        This leads to smaller, more semantically focused sets for intersection,
        making the matching process more efficient and accurate.
    2.  **Reduced Redundancy**: The knowledge base sentences are pre-processed
        once at the beginning, storing tuples of `(original_sentence, filtered_word_set)`.
        This avoids repeatedly tokenizing and filtering each sentence's words within the
        main scoring loop, thus streamlining operations.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    if not knowledge_base or not question:
        return "Thank you for contacting us. We could not process your request with the provided information."

    # --- 1. Preprocess Question for Keywords ---
    # Use the helper to tokenize, lowercase, and filter out stop words from the question.
    relevant_question_words = _tokenize_and_filter(question)
    
    if not relevant_question_words:
        # If no relevant keywords are found, the question might be too generic.
        return "Thank you for contacting us. Please provide a more specific question."

    # --- 2. Process Knowledge Base and Identify Most Relevant Sentence ---
    # Split the knowledge base into individual sentences.
    # The regex uses a positive lookbehind to ensure the delimiter ('.', '?', '!')
    # is kept as part of the sentence, improving readability.
    sentences = [s.strip() for s in re.split(r'(?<=[.?!])\s*', knowledge_base) if s.strip()]
    
    # Pre-process all knowledge base sentences once using the helper.
    # Store tuples of (original_sentence, processed_word_set) for efficient access in the scoring loop.
    processed_kb_sentences = []
    for original_sentence in sentences:
        processed_kb_sentences.append((original_sentence, _tokenize_and_filter(original_sentence)))
    
    best_match_score = 0
    best_answer_sentence = None

    for original_sentence, processed_sentence_words in processed_kb_sentences:
        # Calculate a relevance score: the number of common words between the
        # relevant question keywords and the *processed* sentence's words.
        # Set intersection between two stop-word-filtered sets is efficient and focused.
        current_score = len(relevant_question_words.intersection(processed_sentence_words))

        # Update the best match if the current sentence has a higher score.
        if current_score > best_match_score:
            best_match_score = current_score
            best_answer_sentence = original_sentence # Store the original (stripped) sentence

    # --- 3. Formulate the Answer ---
    if best_answer_sentence and best_match_score > 0:
        # If a relevant sentence was found with at least one matching keyword, return it.
        return best_answer_sentence
    else:
        # Fallback response if no relevant sentence could be identified.
        return "Thank you for contacting us. We couldn't find a direct answer in our knowledge base. Please visit our website for more information."