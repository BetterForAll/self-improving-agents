import re
from collections import Counter

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version leverages collections.Counter for efficient word frequency
    analysis to identify relevant parts of the knowledge base, enhancing both
    answer quality and computation speed for large text bodies.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """

    # --- Helper Functions for Text Processing ---
    def _clean_text(text):
        """Lowercase and remove punctuation from text, then split into words."""
        text = text.lower()
        # Remove anything that's not a letter, number, or space
        text = re.sub(r'[^a-z0-9\s]', '', text)
        return text.split()

    def _split_into_sentences(text):
        """
        Split text into sentences using basic punctuation rules.
        Handles common abbreviations like "Mr.", "U.S." to avoid incorrect splits.
        """
        # Regex to split sentences at periods, question marks, or exclamation points,
        # but not after abbreviations (like "Dr.") or decimals.
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', text)
        return [s.strip() for s in sentences if s.strip()]

    # --- 1. Preprocess Question ---
    # Extract unique words from the question for keyword matching
    question_keywords = set(_clean_text(question))
    
    if not question_keywords:
        return "Thank you for contacting us. Please visit our website for more information."

    # --- 2. Preprocess Knowledge Base ---
    kb_sentences = _split_into_sentences(knowledge_base)
    
    # Store original sentences along with their word frequency counters
    # This pre-computation uses collections.Counter once per sentence
    processed_kb_data = []
    for original_sentence in kb_sentences:
        cleaned_words = _clean_text(original_sentence)
        if cleaned_words: # Ensure the sentence is not empty after cleaning
            processed_kb_data.append({
                "original": original_sentence,
                "word_counter": Counter(cleaned_words)
            })

    # --- 3. Score Sentences using collections.Counter ---
    # Calculate a relevance score for each sentence in the knowledge base
    # by summing the frequencies of question keywords found within it.
    scored_sentences = []
    for item in processed_kb_data:
        score = 0
        sentence_word_counter = item["word_counter"]
        
        # Efficiently sum up the counts of question keywords using Counter's fast lookup.
        # If a keyword is not in the sentence, Counter[keyword] returns 0.
        for q_word in question_keywords:
            score += sentence_word_counter[q_word]

        if score > 0: # Only keep sentences that contain at least one question keyword
            scored_sentences.append((score, item["original"]))

    # --- 4. Select Best Sentences ---
    # Sort sentences by their relevance score in descending order
    scored_sentences.sort(key=lambda x: x[0], reverse=True)

    if not scored_sentences:
        return "Thank you for contacting us. We could not find specific information related to your question in our knowledge base. Please visit our website for more information."

    # Collect all sentences that share the highest relevance score
    max_score = scored_sentences[0][0]
    relevant_sentences = []
    for score, sentence in scored_sentences:
        if score == max_score:
            relevant_sentences.append(sentence)
        else:
            # Optionally, one could include a few more top-scoring sentences
            # even if their score is slightly lower than max_score, up to a limit.
            # For simplicity, we stick to only sentences with the absolute max score here.
            break 
            
    # --- 5. Formulate Answer ---
    if relevant_sentences:
        # Join the selected relevant sentences to form the answer
        answer = " ".join(relevant_sentences)
        return f"Regarding your question: {answer}"
    else:
        # Fallback if no relevant sentences were found (should be caught earlier, but good for robustness)
        return "Thank you for contacting us. We could not find specific information related to your question in our knowledge base. Please visit our website for more information."