import string
import re

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version extracts keywords from the question, searches the
    knowledge base for sentences containing these keywords, and constructs
    an answer from the most relevant snippets found.
    It now preserves the original casing of the knowledge base sentences
    for better readability in the final answer.
    This version enhances relevance by incorporating trigram matching, giving
    more specific phrases a higher priority in scoring.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    # 1. Pre-process question to extract relevant keywords, bigrams, and trigrams
    question_lower = question.lower()
    # Remove punctuation from the question
    question_cleaned = question_lower.translate(str.maketrans('', '', string.punctuation))
    
    # Split cleaned question into words for both single word set and an ordered list for bigrams/trigrams
    question_word_list_ordered = question_cleaned.split()
    question_words_set = set(question_word_list_ordered)

    # A basic list of common stop words to filter out noise from keywords
    stop_words = {"a", "an", "the", "is", "are", "was", "were", "and", "or", "for", "on", "in", "with", 
                  "how", "what", "where", "when", "why", "can", "could", "may", "might", "do", "does", 
                  "did", "of", "to", "from", "at", "about", "this", "that", "these", "those", "it", 
                  "its", "you", "your", "we", "our", "us", "i", "my", "me", "he", "him", "his", "she", 
                  "her", "hers", "they", "them", "their", "which", "who", "whom", "whose", "if", "then", 
                  "but", "not", "no", "yes", "please", "thank", "would", "will", "shall", "should", 
                  "get", "got", "go", "goes", "going", "have", "has", "had", "been", "be", "being", "am"}
    
    # Filter out stop words to get relevant single keywords.
    relevant_question_words = {word for word in question_words_set if word not in stop_words}

    # Generate relevant bigrams from the question
    relevant_question_bigrams = set()
    for i in range(len(question_word_list_ordered) - 1):
        word1 = question_word_list_ordered[i]
        word2 = question_word_list_ordered[i+1]
        # A bigram is considered relevant if both its constituent words are not stop words.
        if word1 not in stop_words and word2 not in stop_words:
            relevant_question_bigrams.add(f"{word1} {word2}")

    # Generate relevant trigrams from the question
    relevant_question_trigrams = set()
    for i in range(len(question_word_list_ordered) - 2):
        word1 = question_word_list_ordered[i]
        word2 = question_word_list_ordered[i+1]
        word3 = question_word_list_ordered[i+2]
        # A trigram is considered relevant if all three constituent words are not stop words.
        if word1 not in stop_words and word2 not in stop_words and word3 not in stop_words:
            relevant_question_trigrams.add(f"{word1} {word2} {word3}")

    # If no relevant keywords, bigrams, or trigrams are found after filtering, return a generic response
    if not relevant_question_words and not relevant_question_bigrams and not relevant_question_trigrams:
        return "Thank you for your question. While I couldn't identify specific keywords, please visit our comprehensive FAQ page or contact customer support for more information."

    # 2. Pre-process knowledge base: Split into sentences and score them
    # Split the original knowledge base into sentences to preserve original casing.
    # The regex splits on '.', '!', '?' followed by a space, keeping the punctuation within the sentence string.
    original_sentences = re.split(r'(?<=[.!?])\s+', knowledge_base)

    scored_sentences = []

    for original_sentence in original_sentences:
        # Skip empty strings that might result from re.split on malformed KB text
        if not original_sentence.strip():
            continue

        # Create a lowercase version of the sentence for keyword comparison
        sentence_lower = original_sentence.lower() 
        # Clean the lowercase sentence for word comparison (remove punctuation)
        sentence_cleaned_for_comparison = sentence_lower.translate(str.maketrans('', '', string.punctuation))
        sentence_words_set = set(sentence_cleaned_for_comparison.split()) # Use set for efficient single word lookup
        
        score = 0
        # Calculate a score based on how many relevant single keywords are in the sentence
        for q_word in relevant_question_words:
            if q_word in sentence_words_set:
                score += 1 # Base score for single word match
        
        # Add score for relevant bigrams (higher weight for sequence match)
        for q_bigram in relevant_question_bigrams:
            # Check if the bigram (as a phrase) exists as a substring in the cleaned sentence.
            if q_bigram in sentence_cleaned_for_comparison:
                score += 2 # Give a higher score for a bigram match
            
        # Add score for relevant trigrams (even higher weight for longer sequence match)
        # This provides a strong boost for sentences containing very specific phrases from the question.
        for q_trigram in relevant_question_trigrams:
            # Check if the trigram (as a phrase) exists as a substring in the cleaned sentence.
            if q_trigram in sentence_cleaned_for_comparison:
                score += 3 # Give an even higher score for a trigram match
                               
        if score > 0:  # Only consider sentences that contain at least one matching keyword/n-gram
            # Store the score along with the original-cased sentence and its length.
            # Sentence length is added for tie-breaking in sorting (preferring more concise).
            scored_sentences.append((score, original_sentence, len(original_sentence)))

    # 3. Construct Answer from relevant snippets
    if not scored_sentences:
        # If no sentences in the knowledge base contained any relevant keywords or n-grams
        return "I apologize, but I couldn't find information directly matching your question in the knowledge base. Please try rephrasing your question or consult our detailed product documentation."

    # Sort sentences by their score in descending order.
    # When scores are equal, sort by sentence length in ascending order to prefer more concise answers.
    scored_sentences.sort(key=lambda x: (-x[0], x[2]))

    relevant_snippets = []
    # Take the top N (e.g., 3) most relevant sentences
    max_snippets = 3

    for score, original_sentence_text, _length in scored_sentences:
        # Ensure the sentence is not empty after stripping whitespace
        processed_sentence = original_sentence_text.strip()
        if not processed_sentence:
            continue
        
        # Capitalize the first letter of the sentence for better readability,
        # ensuring consistency even if the original sentence started lowercase.
        if len(processed_sentence) > 0:
            processed_sentence = processed_sentence[0].upper() + processed_sentence[1:]

        # Ensure the sentence ends with proper punctuation
        if not processed_sentence.endswith(('.', '!', '?')):
            processed_sentence += '.'
        
        relevant_snippets.append(processed_sentence)
        
        # Limit the number of snippets to avoid overly long answers
        if len(relevant_snippets) >= max_snippets:
            break

    if relevant_snippets:
        # Join the selected snippets to form the final answer
        # A prefix indicates that the answer is derived from the knowledge base
        return "Based on our knowledge base: " + " ".join(relevant_snippets)
    else:
        # Fallback if, after all processing and filtering, no snippets are left
        return "I couldn't find a direct answer to your question in the provided knowledge base. Please check our website or contact support."