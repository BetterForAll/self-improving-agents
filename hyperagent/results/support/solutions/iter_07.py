import string
import re

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version extracts keywords from the question, searches the
    knowledge base for sentences containing these keywords, and constructs
    an answer from the most relevant snippets found.
    It now preserves the original casing of the knowledge base sentences
    for better readability in the final answer.
    This version normalizes sentence scores by the number of *content* words to favor concise and dense information
    and includes a basic duplicate sentence filtering to improve conciseness and avoid redundancy.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    # 1. Pre-process question to extract relevant keywords
    question_lower = question.lower()
    # Remove punctuation from the question
    question_cleaned = question_lower.translate(str.maketrans('', '', string.punctuation))
    question_words = set(question_cleaned.split())

    # A basic list of common stop words to filter out noise from keywords
    stop_words = {"a", "an", "the", "is", "are", "was", "were", "and", "or", "for", "on", "in", "with", 
                  "how", "what", "where", "when", "why", "can", "could", "may", "might", "do", "does", 
                  "did", "of", "to", "from", "at", "about", "this", "that", "these", "those", "it", 
                  "its", "you", "your", "we", "our", "us", "i", "my", "me", "he", "him", "his", "she", 
                  "her", "hers", "they", "them", "their", "which", "who", "whom", "whose", "if", "then", 
                  "but", "not", "no", "yes", "please", "thank", "would", "will", "shall", "should", 
                  "get", "got", "go", "goes", "going", "have", "has", "had", "been", "be", "being", "am"}
    
    # Filter out stop words and keep content words (words longer than 2 characters)
    relevant_question_words = {word for word in question_words if word not in stop_words and len(word) > 2}

    # If no relevant keywords are found after filtering, return a generic but slightly more helpful response
    if not relevant_question_words:
        return "Thank you for your question. While I couldn't identify specific keywords, please visit our comprehensive FAQ page or contact customer support for more information."

    # 2. Pre-process knowledge base: Split into sentences and score them
    # Split the original knowledge base into sentences to preserve original casing.
    # The regex splits on '.', '!', '?' followed by a space, keeping the punctuation within the sentence string.
    original_sentences = re.split(r'(?<=[.!?])\s+', knowledge_base)

    scored_sentences = []

    for original_sentence in original_sentences:
        # Create a lowercase version of the sentence for keyword comparison
        sentence_lower = original_sentence.lower() 
        # Clean the lowercase sentence for word comparison (remove punctuation)
        sentence_cleaned_for_comparison = sentence_lower.translate(str.maketrans('', '', string.punctuation))
        sentence_words_list = sentence_cleaned_for_comparison.split() # Get all words in a list
        sentence_words_set = set(sentence_words_list) # Unique words for direct keyword matching
        
        # Filter out very short sentences (e.g., less than 3 total words after cleaning) 
        # or sentences that are just punctuation, as these are often not informative.
        if len(sentence_words_list) < 3:
            continue

        raw_score = 0
        # Calculate a score based on how many relevant question keywords are in the sentence
        for q_word in relevant_question_words:
            if q_word in sentence_words_set: # Check against the set of unique words
                raw_score += 1
        
        if raw_score > 0:  # Only consider sentences that contain at least one matching keyword
            # Calculate the number of content words in the sentence for normalization.
            # This makes the score density-based, favoring sentences with a higher proportion of relevant keywords.
            num_content_words_in_sentence = len({word for word in sentence_words_set if word not in stop_words and len(word) > 2})
            
            # If a sentence has a raw_score > 0, it means it contains at least one relevant keyword.
            # Such a keyword must itself be a content word. Thus, num_content_words_in_sentence must be >= 1.
            # Use max(1, ...) to robustly handle cases where denominator might theoretically be zero (though unlikely with raw_score > 0).
            normalized_score = raw_score / max(1, num_content_words_in_sentence)
            
            # Store the normalized score along with the original-cased sentence
            scored_sentences.append((normalized_score, original_sentence))

    # 3. Construct Answer from relevant snippets
    if not scored_sentences:
        # If no sentences in the knowledge base contained any relevant keywords (after filtering/scoring)
        return "I apologize, but I couldn't find information directly matching your question in the knowledge base. Please try rephrasing your question or consult our detailed product documentation."

    # Sort sentences by their score in descending order
    # For ties, Python's sort is stable, maintaining the original order which is acceptable.
    scored_sentences.sort(key=lambda x: x[0], reverse=True)

    relevant_snippets = []
    # Use a set to track added sentences (by their lowercase, cleaned text) to avoid near-duplicates.
    # This helps improve conciseness by not including highly similar pieces of information.
    added_sentence_texts_cleaned = set()

    for score, original_sentence_text in scored_sentences:
        # Ensure the sentence is not empty after stripping whitespace
        processed_sentence = original_sentence_text.strip()
        if not processed_sentence:
            continue
        
        # Create a cleaned, lowercased version for duplicate checking
        # This ignores differences in casing and punctuation for duplication.
        cleaned_for_dup_check = processed_sentence.lower().translate(str.maketrans('', '', string.punctuation))
        if cleaned_for_dup_check in added_sentence_texts_cleaned:
            continue # Skip if a very similar sentence has already been added

        # Capitalize the first letter of the sentence for better readability,
        # ensuring consistency even if the original sentence started lowercase.
        processed_sentence = processed_sentence[0].upper() + processed_sentence[1:]

        # Ensure the sentence ends with proper punctuation
        if not processed_sentence.endswith(('.', '!', '?')):
            processed_sentence += '.'
        
        relevant_snippets.append(processed_sentence)
        added_sentence_texts_cleaned.add(cleaned_for_dup_check)
        
        # Limit the number of snippets to avoid overly long answers
        # A limit of 3 snippets is a good balance for providing enough information without being verbose.
        if len(relevant_snippets) >= 3:
            break

    if relevant_snippets:
        # Join the selected snippets to form the final answer
        # A prefix indicates that the answer is derived from the knowledge base,
        # providing context to the user.
        return "Based on our knowledge base: " + " ".join(relevant_snippets)
    else:
        # Fallback if, after all processing and filtering (e.g., short sentence filter, duplicate filter),
        # no suitable snippets are left.
        return "I couldn't find a direct answer to your question in the provided knowledge base. Please check our website or contact support."