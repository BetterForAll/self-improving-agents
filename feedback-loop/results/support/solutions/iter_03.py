import re

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version extracts keywords from the question, searches the
    knowledge base for sentences containing those keywords, and returns
    the most relevant sentences as the answer.

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
        "just", "don", "now"
    ])

    # Extract keywords from the question:
    # 1. Remove punctuation using regex.
    # 2. Split into words.
    # 3. Filter out stop words and very short words (length < 3).
    question_words = re.findall(r'\b\w+\b', question_lower)
    keywords = [word for word in question_words if word not in stop_words and len(word) > 2]

    if not keywords:
        return "I'm sorry, I couldn't understand your question. Could you please rephrase it?"

    # Split the knowledge base into individual sentences for more granular search.
    # We use a regex to split by common sentence terminators (., !, ?),
    # keeping the terminator with the sentence and allowing for optional spaces after it.
    sentences = re.split(r'(?<=[.!?])\s*', knowledge_base)
    # Filter out any empty strings that might result from splitting and strip whitespace.
    sentences = [s.strip() for s in sentences if s.strip()]

    # Dictionary to store sentences along with their relevance scores:
    # (total_keyword_matches, unique_keyword_matches)
    relevant_sentences_info = {}

    for sentence in sentences:
        sentence_lower = sentence.lower()
        total_matches = 0
        unique_matched_keywords = set()

        for keyword in keywords:
            # Use regex to find whole word matches to avoid partial matches (e.g., 'car' matching 'carpet').
            # re.escape() is used to handle keywords that might contain regex special characters.
            if re.search(r'\b' + re.escape(keyword) + r'\b', sentence_lower):
                total_matches += 1
                unique_matched_keywords.add(keyword)

        if total_matches > 0:
            # Store the original sentence along with its relevance scores.
            relevant_sentences_info[sentence] = (total_matches, len(unique_matched_keywords))

    # Sort sentences by relevance:
    # Prefer sentences with more unique keyword matches, then by the total number of keyword occurrences.
    sorted_sentences_with_scores = sorted(
        relevant_sentences_info.items(),
        key=lambda item: (item[1][1], item[1][0]), # Sort by (unique_matches, total_matches)
        reverse=True # Descending order for most relevant first
    )

    # Construct the answer from the most relevant sentences.
    answer_parts = []
    
    # Threshold for a sentence to be considered relevant enough to include:
    # it must contain at least one unique keyword from the question.
    min_unique_keyword_matches_per_sentence = 1 
    
    # Limit the number of sentences in the answer for conciseness.
    max_sentences_in_answer = 3

    for sentence, (total_matches, unique_matches) in sorted_sentences_with_scores:
        if unique_matches >= min_unique_keyword_matches_per_sentence:
            answer_parts.append(sentence)
            if len(answer_parts) >= max_sentences_in_answer:
                break
    
    if answer_parts:
        # Join the selected sentences to form the answer.
        final_answer = " ".join(answer_parts)
        
        # Clean up any potential extra spaces and ensure the answer ends with punctuation.
        final_answer = final_answer.strip()
        if not final_answer.endswith(('.', '!', '?')):
            final_answer += "."
        
        return final_answer
    else:
        # Fallback if no sufficiently relevant sentences were found in the knowledge base.
        return "I couldn't find specific information matching your question in our knowledge base. Please visit our website for more information or try rephrasing your question."