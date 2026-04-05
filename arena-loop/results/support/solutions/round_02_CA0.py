import re

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version identifies keywords in the question and attempts to find
    the most relevant sentence in the knowledge base by counting shared keywords.
    It leverages built-in string methods, regex for tokenization and sentence
    splitting, and sets for efficient keyword matching.

    Optimizations:
    1. Pre-compiles regex patterns to avoid repeated compilation overhead.
    2. Processes the entire knowledge base once to tokenize all sentences into word sets
       *before* entering the main scoring loop. This avoids redundant regex and set
       creation operations inside the loop, significantly boosting performance
       for large knowledge bases.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    if not knowledge_base or not question:
        return "Thank you for contacting us. We could not process your request with the provided information."

    # Pre-compile regex patterns for efficiency.
    # This avoids recompiling the same pattern repeatedly, reducing overhead.
    _word_tokenizer_pattern = re.compile(r'\b\w+\b')
    _sentence_splitter_pattern = re.compile(r'(?<=[.?!])\s*')

    # --- 1. Preprocess Question for Keywords ---
    # Normalize question: lowercase, extract word tokens using the pre-compiled regex,
    # and store as a set for efficient lookup (O(1) average time complexity).
    question_tokens = set(_word_tokenizer_pattern.findall(question.lower()))
    
    # Define a set of common stop words to filter out less relevant words.
    # This reduces noise and focuses on core concepts, improving relevance matching.
    # This set is defined once per function call.
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

    # --- 2. Preprocess Knowledge Base (Optimized) ---
    # This is a key optimization: Split the knowledge base into sentences using
    # the pre-compiled regex, then tokenize each sentence *once* into a word set.
    # This avoids redundant regex and set creation operations in the subsequent scoring loop.
    raw_sentences = _sentence_splitter_pattern.split(knowledge_base)
    
    # Stores tuples of (original_sentence_string, set_of_tokenized_words_in_sentence)
    processed_sentences_data = [] 
    for s in raw_sentences:
        stripped_sentence = s.strip()
        if stripped_sentence: # Ensure the sentence is not empty after stripping
            # Tokenize and create a set of words for each sentence once
            sentence_words_set = set(_word_tokenizer_pattern.findall(stripped_sentence.lower()))
            processed_sentences_data.append((stripped_sentence, sentence_words_set))
    
    best_match_score = 0
    best_answer_sentence = None

    # --- 3. Identify Most Relevant Sentence (Optimized Scoring Loop) ---
    # Iterate through the preprocessed sentence data. The word sets are already
    # prepared, making the scoring much faster.
    for original_sentence, sentence_words in processed_sentences_data:
        # Calculate a relevance score: the number of common words between the
        # relevant question keywords and the sentence's words.
        # Set intersection is an efficient way to find common elements.
        current_score = len(relevant_question_words.intersection(sentence_words))

        # Update the best match if the current sentence has a higher score.
        if current_score > best_match_score:
            best_match_score = current_score
            best_answer_sentence = original_sentence # Store the original (stripped) sentence

    # --- 4. Formulate the Answer ---
    if best_answer_sentence and best_match_score > 0:
        # If a relevant sentence was found with at least one matching keyword, return it.
        return best_answer_sentence
    else:
        # Fallback response if no relevant sentence could be identified.
        return "Thank you for contacting us. We couldn't find a direct answer in our knowledge base. Please visit our website for more information."