import re

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version extracts keywords from the question, searches the
    knowledge base for sentences containing those keywords, and returns
    the most relevant sentences as the answer.

    Improvements in this version include:
    - More inclusive keyword extraction by allowing shorter keywords (e.g., "AI", "OS", "4G")
      while still filtering common stop words. This enhances recall for technical terms.
    - Enhanced keyword filtering in the question to explicitly exclude purely numeric terms
      (e.g., "123") that are unlikely to be meaningful keywords on their own, reducing noise.
    - **Dynamic answer sentence selection**: It now intelligently selects sentences
      based on their relevance relative to the highest-scoring sentence, ensuring
      that only sufficiently relevant information is included. This, combined with a
      maximum sentence limit, promotes conciseness and quality by preventing the inclusion
      of weakly relevant sentences when stronger ones exist.
    - Preserves the refined relevance scoring, efficient keyword matching,
      and improved answer formatting from the previous version.

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
    # 2. Filter out stop words, very short words (length < 2), and purely numeric words.
    #    'len(word) > 1' allows important short keywords like "AI", "OS", "4G".
    #    'not word.isdigit()' prevents purely numeric strings (e.g., "123") from being keywords,
    #    unless they are part of a larger term (like "4G").
    question_words = re.findall(r'\b\w+\b', question_lower)
    keywords = [
        word for word in question_words
        if word not in stop_words and len(word) > 1 and not word.isdigit()
    ]

    if not keywords:
        return "I'm sorry, I couldn't understand your question. Could you please rephrase it using more specific terms?"

    # Split the knowledge base into individual sentences for more granular search.
    # We use a regex to split by common sentence terminators (., !, ?),
    # keeping the terminator with the sentence and allowing for optional spaces after it.
    sentences = re.split(r'(?<=[.!?])\s*', knowledge_base)
    # Filter out any empty strings that might result from splitting and strip whitespace.
    sentences = [s.strip() for s in sentences if s.strip()]

    # Dictionary to store sentences along with their relevance scores.
    # Score tuple: (unique_keyword_matches, total_keyword_matches, sentence_length_in_tokens)
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
    
    # Define parameters for dynamic answer sentence selection.
    # A sentence must contain at least this many unique keywords.
    min_unique_keyword_matches_per_sentence = 1 
    # A sentence's unique matches count must be at least this fraction of the top sentence's unique matches.
    relative_unique_matches_threshold = 0.6 # e.g., if top sentence has 5 unique matches, others must have >= 3.
    # Absolute maximum number of sentences to include in the answer for conciseness.
    max_sentences_in_answer = 3

    top_score_unique_matches = 0
    if sorted_sentences_with_scores:
        # Get unique_matches of the top sentence to use as a baseline for relative filtering.
        top_score_unique_matches = sorted_sentences_with_scores[0][1][0] 

    for sentence, (unique_matches, total_matches, sentence_len) in sorted_sentences_with_scores:
        # Apply absolute and relative unique keyword match thresholds.
        # top_score_unique_matches will always be > 0 if sorted_sentences_with_scores is not empty.
        if unique_matches >= min_unique_keyword_matches_per_sentence and \
           unique_matches >= top_score_unique_matches * relative_unique_matches_threshold:
            
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