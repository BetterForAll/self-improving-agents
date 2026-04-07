import string
import re

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version extracts keywords and multi-word phrases from the question,
    searches the knowledge base for sentences containing these, and constructs an
    answer from the most relevant snippets found. It now prioritizes exact phrase
    matches for better relevance and includes a mechanism to avoid near-duplicate
    sentences in the final answer. Original casing of knowledge base sentences
    is preserved for readability.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    # Define punctuation to remove for cleaning text, optimized for single creation
    PUNCTUATION_TRANSLATION_TABLE = str.maketrans('', '', string.punctuation)

    # A basic list of common stop words to filter out noise from keywords
    stop_words = {"a", "an", "the", "is", "are", "was", "were", "and", "or", "for", "on", "in", "with", 
                  "how", "what", "where", "when", "why", "can", "could", "may", "might", "do", "does", 
                  "did", "of", "to", "from", "at", "about", "this", "that", "these", "those", "it", 
                  "its", "you", "your", "we", "our", "us", "i", "my", "me", "he", "him", "his", "she", 
                  "her", "hers", "they", "them", "their", "which", "who", "whom", "whose", "if", "then", 
                  "but", "not", "no", "yes", "please", "thank", "would", "will", "shall", "should", 
                  "get", "got", "go", "goes", "going", "have", "has", "had", "been", "be", "being", "am"}
    
    # 1. Pre-process question to extract relevant keywords and phrases
    question_lower = question.lower()
    question_cleaned = question_lower.translate(PUNCTUATION_TRANSLATION_TABLE)
    question_words_list = question_cleaned.split()

    # Filter out stop words and short words (length <= 2) to get content-rich words
    content_words_list = [word for word in question_words_list 
                          if word not in stop_words and len(word) > 2]

    # Set of individual relevant words from the question
    relevant_question_words = set(content_words_list)

    # Generate multi-word phrases (bi-grams and tri-grams) from content words
    relevant_question_phrases = set()
    
    # Bi-grams
    for i in range(len(content_words_list) - 1):
        phrase = f"{content_words_list[i]} {content_words_list[i+1]}"
        relevant_question_phrases.add(phrase)
    
    # Tri-grams
    for i in range(len(content_words_list) - 2):
        phrase = f"{content_words_list[i]} {content_words_list[i+1]} {content_words_list[i+2]}"
        relevant_question_phrases.add(phrase)

    # Sort phrases by length (descending) to prioritize matching longer phrases first during scoring.
    # This prevents shorter phrases from "covering" words that could be part of a more significant longer phrase.
    relevant_question_phrases_sorted = sorted(list(relevant_question_phrases), key=len, reverse=True)

    # If no relevant keywords or phrases are found after filtering, return a specific fallback message
    if not relevant_question_words and not relevant_question_phrases:
        return "Thank you for your question. While I couldn't identify specific keywords or phrases, please visit our comprehensive FAQ page or contact customer support for more information."

    # 2. Pre-process knowledge base: Split into sentences and score them
    # Use regex to split the original knowledge base into sentences, keeping punctuation with the sentence.
    original_sentences = re.split(r'(?<=[.!?])\s+', knowledge_base)
    
    scored_sentences = []
    
    # A multiplier to give phrases significantly more weight than individual keywords.
    # A 2-word phrase will score (2 words * PHRASE_WORD_MULTIPLIER) points.
    PHRASE_WORD_MULTIPLIER = 2 

    for original_sentence in original_sentences:
        sentence_lower = original_sentence.lower() 
        # Clean the lowercase sentence for word comparison (remove punctuation)
        sentence_cleaned_for_comparison = sentence_lower.translate(PUNCTUATION_TRANSLATION_TABLE)
        sentence_words_set = set(sentence_cleaned_for_comparison.split())
        
        score = 0
        # Tracks words already counted as part of a phrase to avoid double-counting with individual keywords
        covered_words = set() 

        # First, score based on multi-word phrase matches, prioritizing longer ones
        for phrase in relevant_question_phrases_sorted:
            # Check if the exact phrase exists in the lowercase sentence
            if phrase in sentence_lower:
                phrase_words = phrase.split()
                # Ensure none of the words in this phrase have already been 'covered' by a previous,
                # possibly overlapping, longer phrase match.
                if not any(word in covered_words for word in phrase_words):
                    # Award points for the phrase: length of phrase words * multiplier
                    score += len(phrase_words) * PHRASE_WORD_MULTIPLIER
                    covered_words.update(phrase_words) # Mark these words as covered
        
        # Then, score based on individual relevant keywords that were not part of any matched phrase
        for q_word in relevant_question_words:
            if q_word in sentence_words_set and q_word not in covered_words:
                score += 1
                covered_words.add(q_word) # Mark individual word as covered

        if score > 0:  # Only consider sentences that have a positive score
            scored_sentences.append((score, original_sentence))

    # 3. Construct Answer from relevant snippets
    if not scored_sentences:
        # If no sentences in the knowledge base contained any relevant keywords/phrases
        return "I apologize, but I couldn't find information directly matching your question in the knowledge base. Please try rephrasing your question or consult our detailed product documentation."

    # Sort sentences by their score in descending order to get the most relevant first
    scored_sentences.sort(key=lambda x: x[0], reverse=True)

    relevant_snippets = []
    # Use a set to store normalized content of snippets already added, to prevent near-duplicates
    added_snippets_normalized = set() 
    
    for score, original_sentence_text in scored_sentences:
        processed_sentence = original_sentence_text.strip()
        if not processed_sentence:
            continue
        
        # Normalize the snippet content for duplicate checking (lowercase, no punctuation)
        normalized_content = processed_sentence.lower().translate(PUNCTUATION_TRANSLATION_TABLE)
        if normalized_content in added_snippets_normalized:
            continue # Skip if this snippet (or a very similar one) has already been added

        # Capitalize the first letter of the sentence for better readability,
        # ensuring consistency even if the original sentence started lowercase.
        processed_sentence = processed_sentence[0].upper() + processed_sentence[1:]

        # Ensure the sentence ends with proper punctuation for consistent formatting
        if not processed_sentence.endswith(('.', '!', '?')):
            processed_sentence += '.'
        
        relevant_snippets.append(processed_sentence)
        added_snippets_normalized.add(normalized_content)
        
        # Limit the number of snippets to a reasonable maximum (e.g., 3) to avoid overly long answers
        if len(relevant_snippets) >= 3:
            break

    if relevant_snippets:
        # Join the selected snippets to form the final answer, adding a helpful prefix
        return "Based on our knowledge base: " + " ".join(relevant_snippets)
    else:
        # This is a fallback in case `relevant_snippets` becomes empty unexpectedly
        # after filtering (e.g., all top sentences were duplicates).
        return "I couldn't find a direct answer to your question in the provided knowledge base. Please check our website or contact support."