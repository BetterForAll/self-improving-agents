import string
import re

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version extracts keywords and n-grams from the question, searches the
    knowledge base for sentences containing these terms, and constructs
    an answer from the most relevant snippets found.
    It now preserves the original casing of the knowledge base sentences
    for better readability in the final answer, and uses a more nuanced scoring
    mechanism that prioritizes phrase matches and considers term frequency for individual keywords.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    # Define a set of common stop words to filter out noise from keywords
    stop_words = {"a", "an", "the", "is", "are", "was", "were", "and", "or", "for", "on", "in", "with", 
                  "how", "what", "where", "when", "why", "can", "could", "may", "might", "do", "does", 
                  "did", "of", "to", "from", "at", "about", "this", "that", "these", "those", "it", 
                  "its", "you", "your", "we", "our", "us", "i", "my", "me", "he", "him", "his", "she", 
                  "her", "hers", "they", "them", "their", "which", "who", "whom", "whose", "if", "then", 
                  "but", "not", "no", "yes", "please", "thank", "would", "will", "shall", "should", 
                  "get", "got", "go", "goes", "going", "have", "has", "had", "been", "be", "being", "am"}

    # 1. Pre-process question to extract relevant keywords and n-grams
    question_lower = question.lower()
    # Remove punctuation from the question
    question_cleaned = question_lower.translate(str.maketrans('', '', string.punctuation))
    question_words_list = question_cleaned.split() # Keep as list for n-gram generation

    # Filter out stop words and keep content words (words longer than 2 characters) for single keywords
    relevant_question_words = {word for word in question_words_list if word not in stop_words and len(word) > 2}

    # Generate bigrams and trigrams from the question
    question_bigrams = set()
    question_trigrams = set()

    for i in range(len(question_words_list) - 1):
        word1 = question_words_list[i]
        word2 = question_words_list[i+1]
        
        # Include bigram if at least one word is a content word (not stop word and meaningful length)
        if (word1 not in stop_words and len(word1) > 2) or \
           (word2 not in stop_words and len(word2) > 2):
            bigram = " ".join([word1, word2])
            question_bigrams.add(bigram)

    for i in range(len(question_words_list) - 2):
        word1 = question_words_list[i]
        word2 = question_words_list[i+1]
        word3 = question_words_list[i+2]

        # Include trigram if at least two words are content words
        num_content_words_in_trigram = sum(1 for w in [word1, word2, word3] if w not in stop_words and len(w) > 2)
        if num_content_words_in_trigram >= 2:
            trigram = " ".join([word1, word2, word3])
            question_trigrams.add(trigram)

    # If no relevant terms (single words, bigrams, or trigrams) are found after filtering
    if not relevant_question_words and not question_bigrams and not question_trigrams:
        return "Thank you for your question. While I couldn't identify specific keywords or phrases, please visit our comprehensive FAQ page or contact customer support for more information."

    # 2. Pre-process knowledge base: Split into sentences and score them
    # Split the original knowledge base into sentences to preserve original casing.
    # The regex splits on '.', '!', '?' followed by a space, keeping the punctuation within the sentence string.
    original_sentences = re.split(r'(?<=[.!?])\s+', knowledge_base)

    scored_sentences = []

    for original_sentence in original_sentences:
        # Create a lowercase version of the sentence for keyword and n-gram comparison
        sentence_lower = original_sentence.lower() 
        # Clean the lowercase sentence for word comparison (remove punctuation)
        sentence_cleaned_for_comparison = sentence_lower.translate(str.maketrans('', '', string.punctuation))
        sentence_words_list = sentence_cleaned_for_comparison.split()
        
        score = 0
        
        # Calculate a score based on relevance: prioritize phrase matches and consider term frequency
        
        # 1. Trigram matches (highest weight)
        for t_gram in question_trigrams:
            if t_gram in sentence_lower: # Check for exact phrase match in the lowercased sentence
                score += 5 # High weight for exact trigram matches

        # 2. Bigram matches (medium weight)
        for b_gram in question_bigrams:
            if b_gram in sentence_lower: # Check for exact phrase match in the lowercased sentence
                score += 3 # Medium weight for exact bigram matches
        
        # 3. Individual relevant keyword matches (term frequency based)
        for q_word in relevant_question_words:
            # Add count of occurrences of the word in the cleaned sentence
            score += sentence_words_list.count(q_word)
        
        if score > 0:  # Only consider sentences that contain at least one matching term
            scored_sentences.append((score, original_sentence))

    # 3. Construct Answer from relevant snippets
    if not scored_sentences:
        # If no sentences in the knowledge base contained any relevant keywords or phrases
        return "I apologize, but I couldn't find information directly matching your question in the knowledge base. Please try rephrasing your question or consult our detailed product documentation."

    # Sort sentences by their score in descending order
    scored_sentences.sort(key=lambda x: x[0], reverse=True)

    relevant_snippets = []
    # To avoid overly long answers or repetitive content, limit the number of snippets
    # and attempt a basic deduplication.
    max_snippets = 3
    selected_sentences_lower_cleaned = set() # Store cleaned, lowercased versions for deduplication
    
    for score, original_sentence_text in scored_sentences:
        processed_sentence = original_sentence_text.strip()
        
        if not processed_sentence:
            continue
        
        # Basic deduplication: check if a very similar sentence (ignoring casing and punctuation)
        # has already been selected.
        temp_sentence_lower_cleaned = processed_sentence.lower().translate(str.maketrans('', '', string.punctuation))
        if temp_sentence_lower_cleaned in selected_sentences_lower_cleaned:
            continue # Skip if an almost identical sentence has already been added

        # Capitalize the first letter of the sentence for better readability,
        # ensuring consistency even if the original sentence started lowercase.
        processed_sentence = processed_sentence[0].upper() + processed_sentence[1:]

        # Ensure the sentence ends with proper punctuation
        if not processed_sentence.endswith(('.', '!', '?')):
            processed_sentence += '.'
        
        relevant_snippets.append(processed_sentence)
        selected_sentences_lower_cleaned.add(temp_sentence_lower_cleaned) # Add to deduplication set
        
        # Limit the number of snippets to avoid overly long answers
        if len(relevant_snippets) >= max_snippets:
            break

    if relevant_snippets:
        # Join the selected snippets to form the final answer
        # A prefix indicates that the answer is derived from the knowledge base
        return "Based on our knowledge base: " + " ".join(relevant_snippets)
    else:
        # Fallback if, after all processing and filtering (e.g., deduplication), no snippets are left
        return "I couldn't find a direct answer to your question in the provided knowledge base. Please check our website or contact support."