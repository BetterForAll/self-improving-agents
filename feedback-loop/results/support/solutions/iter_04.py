import re

# Define a simple set of stop words as a global frozenset for efficiency.
# Moving it outside the function prevents re-initialization on every call.
_STOP_WORDS = frozenset([
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

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version extracts keywords from the question, searches the
    knowledge base for sentences containing those keywords, and returns
    the most relevant sentences as the answer. It enhances relevance scoring
    by considering whether all question keywords are present, and prefers
    shorter, more concise relevant sentences.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    question_lower = question.lower()

    # Extract keywords from the question:
    # 1. Remove punctuation using regex.
    # 2. Split into words.
    # 3. Filter out stop words and very short words (length < 3).
    question_words_raw = re.findall(r'\b\w+\b', question_lower)
    keywords = [word for word in question_words_raw if word not in _STOP_WORDS and len(word) > 2]
    
    # Create a set of unique keywords for faster lookups and to check if all keywords are matched.
    keywords_set = set(keywords)

    if not keywords:
        return "I'm sorry, I couldn't understand your question. Could you please rephrase it?"

    # Split the knowledge base into individual sentences for more granular search.
    # We use a regex to split by common sentence terminators (., !, ?),
    # keeping the terminator with the sentence and allowing for optional spaces after it.
    sentences = re.split(r'(?<=[.!?])\s*', knowledge_base)
    # Filter out any empty strings that might result from splitting and strip whitespace.
    sentences = [s.strip() for s in sentences if s.strip()]

    # Dictionary to store sentences along with their detailed relevance scores.
    # Scores include unique matches, total occurrences, a bonus for containing all question keywords,
    # and the sentence length (for preferring brevity).
    relevant_sentences_info = {}

    for sentence in sentences:
        sentence_lower = sentence.lower()
        # Extract words from the sentence to determine its length
        sentence_words = re.findall(r'\b\w+\b', sentence_lower)
        
        current_total_occurrences = 0
        current_unique_matched_keywords = set()

        for keyword in keywords_set: # Iterate over unique keywords for efficiency
            # Use regex to find whole word matches. re.escape() handles special characters.
            # re.finditer() counts all occurrences of the keyword within the sentence.
            for match in re.finditer(r'\b' + re.escape(keyword) + r'\b', sentence_lower):
                current_total_occurrences += 1
                current_unique_matched_keywords.add(keyword)
        
        unique_matches_count = len(current_unique_matched_keywords)

        if unique_matches_count > 0:
            # Assign a bonus if the sentence contains all unique keywords extracted from the question.
            # This prioritizes sentences that fully address the query.
            contains_all_keywords_bonus = 1 if current_unique_matched_keywords == keywords_set else 0

            relevant_sentences_info[sentence] = {
                "unique_matches": unique_matches_count,
                "total_occurrences": current_total_occurrences,
                "contains_all_keywords_bonus": contains_all_keywords_bonus,
                "sentence_length": len(sentence_words) # Store length to prefer shorter sentences
            }

    # Sort sentences by relevance using a multi-criteria key:
    # 1. Sentences with 'contains_all_keywords_bonus' (1) are ranked highest.
    # 2. Then, sentences with more unique keyword matches.
    # 3. Then, sentences with more total keyword occurrences.
    # 4. Finally, shorter sentences are preferred (by sorting negative length in descending order).
    sorted_sentences_with_scores = sorted(
        relevant_sentences_info.items(),
        key=lambda item: (item[1]["contains_all_keywords_bonus"],
                          item[1]["unique_matches"],
                          item[1]["total_occurrences"],
                          -item[1]["sentence_length"]), # Negative length sorts shorter sentences first in reverse=True order
        reverse=True # Descending order for most relevant first
    )

    # Construct the answer from the most relevant sentences.
    answer_parts = []
    
    # Threshold for a sentence to be considered relevant enough to include:
    # it must contain at least one unique keyword from the question.
    min_unique_keyword_matches_per_sentence = 1 
    
    # Limit the number of sentences in the answer for conciseness.
    max_sentences_in_answer = 3

    for sentence, scores in sorted_sentences_with_scores:
        if scores["unique_matches"] >= min_unique_keyword_matches_per_sentence:
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