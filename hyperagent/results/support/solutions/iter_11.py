import string
import re

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version extracts keywords and multi-word phrases from the question,
    searches the knowledge base for sentences containing these, and constructs an
    answer from the most relevant snippets found.
    It now preserves the original casing of the knowledge base sentences
    for better readability in the final answer.
    This version introduces a scoring boost for sentences that contain
    exact multi-word phrases from the question, in addition to individual keyword matches,
    to prioritize more precise and contextually relevant answers.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    # 1. Pre-process question to extract relevant keywords and phrases
    question_lower = question.lower()
    # Remove punctuation from the question
    question_cleaned = question_lower.translate(str.maketrans('', '', string.punctuation))
    question_words_list = question_cleaned.split() # Use list for phrase generation

    # A basic list of common stop words to filter out noise from keywords
    stop_words = {"a", "an", "the", "is", "are", "was", "were", "and", "or", "for", "on", "in", "with", 
                  "how", "what", "where", "when", "why", "can", "could", "may", "might", "do", "does", 
                  "did", "of", "to", "from", "at", "about", "this", "that", "these", "those", "it", 
                  "its", "you", "your", "we", "our", "us", "i", "my", "me", "he", "him", "his", "she", 
                  "her", "hers", "they", "them", "their", "which", "who", "whom", "whose", "if", "then", 
                  "but", "not", "no", "yes", "please", "thank", "would", "will", "shall", "should", 
                  "get", "got", "go", "goes", "going", "have", "has", "had", "been", "be", "being", "am"}
    
    # Filter out stop words to get individual relevant keywords.
    relevant_question_words = {word for word in question_words_list if word not in stop_words}

    # Extract potential relevant multi-word phrases (bi-grams and tri-grams)
    relevant_phrases = set()
    
    # Generate bi-grams
    for i in range(len(question_words_list) - 1):
        word1 = question_words_list[i]
        word2 = question_words_list[i+1]
        # Only form a phrase if both words are not stop words.
        if word1 not in stop_words and word2 not in stop_words:
            relevant_phrases.add(f"{word1} {word2}")

    # Generate tri-grams
    for i in range(len(question_words_list) - 2):
        word1 = question_words_list[i]
        word2 = question_words_list[i+1]
        word3 = question_words_list[i+2]
        # Only form a phrase if all three words are not stop words.
        if word1 not in stop_words and word2 not in stop_words and word3 not in stop_words:
            relevant_phrases.add(f"{word1} {word3}") # Corrected: should be f"{word1} {word2} {word3}"
            relevant_phrases.add(f"{word1} {word2} {word3}") # This line replaces the incorrect one above

    # If no relevant keywords are found after filtering (which implies no relevant phrases either),
    # return a generic but slightly more helpful response
    if not relevant_question_words:
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

        # Create a lowercase version of the sentence for keyword and phrase comparison
        sentence_lower = original_sentence.lower() 
        # Clean the lowercase sentence for individual word comparison (remove punctuation)
        sentence_cleaned_for_comparison = sentence_lower.translate(str.maketrans('', '', string.punctuation))
        sentence_words = set(sentence_cleaned_for_comparison.split())
        
        score = 0
        # Calculate a base score based on how many relevant individual question keywords are in the sentence
        for q_word in relevant_question_words:
            if q_word in sentence_words:
                score += 1 # Each individual keyword match adds 1 to the score
        
        # Add bonus for relevant multi-word phrase matches
        for q_phrase in relevant_phrases:
            # Check for exact phrase existence as a substring in the lowercased sentence
            if q_phrase in sentence_lower:
                # Give a significant bonus for phrase matches.
                # The bonus is proportional to the number of words in the phrase,
                # multiplied by a factor (e.g., 2) to make it more impactful than individual words.
                phrase_word_count = len(q_phrase.split())
                score += (phrase_word_count * 2) # e.g., 2-word phrase gets +4, 3-word phrase gets +6
        
        if score > 0:  # Only consider sentences that contain at least one matching keyword or phrase
            # Store the score along with the original-cased sentence and its length.
            # Sentence length is added for tie-breaking in sorting.
            scored_sentences.append((score, original_sentence, len(original_sentence)))

    # 3. Construct Answer from relevant snippets
    if not scored_sentences:
        # If no sentences in the knowledge base contained any relevant keywords or phrases
        return "I apologize, but I couldn't find information directly matching your question in the knowledge base. Please try rephrasing your question or consult our detailed product documentation."

    # Sort sentences by their score in descending order.
    # When scores are equal, sort by sentence length in ascending order to prefer more concise answers.
    scored_sentences.sort(key=lambda x: (-x[0], x[2]))

    relevant_snippets = []
    # Take the top N (e.g., 3) most relevant sentences
    # The tuple structure is (score, original_sentence_text, _length)
    for score, original_sentence_text, _length in scored_sentences:
        # Ensure the sentence is not empty after stripping whitespace
        processed_sentence = original_sentence_text.strip()
        if not processed_sentence:
            continue
        
        # Capitalize the first letter of the sentence for better readability,
        # ensuring consistency even if the original sentence started lowercase.
        # Handle cases where the sentence might start with a non-alphabetic character (e.g., a number or symbol)
        if processed_sentence: # Re-check after strip()
            first_char = processed_sentence[0]
            if first_char.isalpha():
                processed_sentence = first_char.upper() + processed_sentence[1:]

        # Ensure the sentence ends with proper punctuation
        if not processed_sentence.endswith(('.', '!', '?')):
            processed_sentence += '.'
        
        relevant_snippets.append(processed_sentence)
        
        # Limit the number of snippets to avoid overly long answers
        if len(relevant_snippets) >= 3:
            break

    if relevant_snippets:
        # Join the selected snippets to form the final answer
        # A prefix indicates that the answer is derived from the knowledge base
        return "Based on our knowledge base: " + " ".join(relevant_snippets)
    else:
        # Fallback if, after all processing and filtering, no snippets are left
        return "I couldn't find a direct answer to your question in the provided knowledge base. Please check our website or contact support."