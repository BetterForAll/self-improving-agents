import re

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version extracts keywords from the question, searches the
    knowledge base for sentences containing those keywords, and returns
    the most relevant sentences as the answer.

    Improvements in this version include:
    - More efficient keyword matching by tokenizing sentences once and using set lookups.
    - More accurate `total_matches` count for keywords within sentences.
    - **Refined relevance scoring**: Prioritizes sentences with more unique keyword matches,
      then more total keyword occurrences, and finally prefers shorter sentences
      among equally relevant ones for conciseness.
    - **Improved answer formatting**: Joins relevant sentences with newlines for better readability.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    question_lower = question.lower()

    # Define a simple list of stop words to filter out common words from the question.
    # This helps focus on key terms.
    stop_words = set([
        "what", "is", "the", "a", "an", "how", "where", "can", "i", "my", "me",
        "for", "of", "and", "or", "to", "in", "on", "at", "with", "about",
        "do", "does", "are", "you", "your", "it", "its", "we", "our", "us",
        "he", "she", "they", "them", "their", "this", "that", "these", "those",
        "be", "been", "was", "were", "has", "have", "had", "will", "would",
        "should", "could", "may", "might", "must", "if", "then", "than", "but",
        "not", "no", "yes", "please", "thank", "help", "information",
        "tell", "me", "from", "by", "as", "into", "through", "during",
        "before", "after", "above", "below", "up", "down", "out", "off", "over",
        "under", "again", "further", "once", "here", "there", "when",
        "why", "who", "whom", "each", "few", "more", "most", "other", "some",
        "such", "nor", "only", "own", "same", "so", "too", "very", "s", "t",
        "just", "don", "now", "get", "any", "much", "many", "also", "like"
    ])

    # Extract keywords from the question:
    # 1. Tokenize words using regex, converting to lowercase.
    # 2. Filter out stop words and very short words (length < 3) to focus on key terms.
    question_words = re.findall(r'\b\w+\b', question_lower)
    keywords = [word for word in question_words if word not in stop_words and len(word) > 2]

    if not keywords:
        return "I'm sorry, I couldn't understand your question. Could you please rephrase it using more specific terms?"

    # Split the knowledge base into individual sentences for more granular search.
    # We use a regex to split by common sentence terminators (., !, ?),
    # keeping the terminator with the sentence and allowing for optional spaces after it.
    sentences = re.split(r'(?<=[.!?])\s*', knowledge_base)
    # Filter out any empty strings that might result from splitting and strip whitespace.
    sentences = [s.strip() for s in sentences if s.strip()]

    # Dictionary to store sentences along with their relevance scores.
    # Score tuple: (unique_keyword_matches, total_keyword_matches, sentence_length)
    # We store positive sentence_length, and will negate it during sorting to prefer shorter sentences.
    relevant_sentences_info = {}

    for sentence in sentences:
        sentence_lower = sentence.lower()
        # Tokenize the sentence once to enable efficient word-level matching.
        sentence_tokens = re.findall(r'\b\w+\b', sentence_lower)
        # Use a set for faster O(1) average-case lookup of unique tokens.
        sentence_token_set = set(sentence_tokens)

        total_matches = 0
        unique_matched_keywords = set()

        for keyword in keywords:
            # Check if the keyword exists as a whole word token in the sentence.
            if keyword in sentence_token_set:
                # Count total occurrences of the keyword in the sentence.
                # This makes 'total_matches' more accurate.
                total_matches += sentence_tokens.count(keyword)
                unique_matched_keywords.add(keyword)

        if total_matches > 0:
            # Store the original sentence along with its relevance scores.
            relevant_sentences_info[sentence] = (len(unique_matched_keywords), total_matches, len(sentence_tokens))

    # Sort sentences by relevance:
    # Priority 1: More unique keyword matches (descending).
    # Priority 2: More total keyword occurrences (descending).
    # Priority 3: Shorter sentence length (ascending) for conciseness.
    sorted_sentences_with_scores = sorted(
        relevant_sentences_info.items(),
        key=lambda item: (-item[1][0], -item[1][1], item[1][2]) # Negate unique/total for descending, keep length positive for ascending
    )

    # Construct the answer from the most relevant sentences.
    answer_parts = []
    
    # Threshold for a sentence to be considered relevant enough to include:
    # it must contain at least one unique keyword from the question.
    min_unique_keyword_matches_per_sentence = 1 
    
    # Limit the number of sentences in the answer for conciseness.
    max_sentences_in_answer = 3

    for sentence, (unique_matches, total_matches, sentence_len) in sorted_sentences_with_scores:
        if unique_matches >= min_unique_keyword_matches_per_sentence:
            answer_parts.append(sentence)
            if len(answer_parts) >= max_sentences_in_answer:
                break
    
    if answer_parts:
        # Join the selected sentences with newlines for better readability.
        final_answer = "\n\n".join(answer_parts)
        
        # Clean up any potential extra spaces and ensure the answer ends with punctuation.
        final_answer = final_answer.strip()
        if not final_answer.endswith(('.', '!', '?')):
            final_answer += "."
        
        return final_answer
    else:
        # Fallback if no sufficiently relevant sentences were found in the knowledge base.
        return "I couldn't find specific information matching your question in our knowledge base. Please visit our website for more information or try rephrasing your question."