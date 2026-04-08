import re
from collections import Counter

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version leverages collections.Counter for efficient word frequency
    analysis to identify relevant parts of the knowledge base, enhancing both
    answer quality and computation speed for large text bodies.

    Improvements for answer quality and precision:
    1.  **Stop Word Removal**: Common stop words (e.g., "the", "is", "a") are removed from
        both the question and knowledge base sentences. This focuses keyword matching
        and frequency analysis on content-rich words, leading to more relevant scores.
    2.  **Refined Scoring Metric**: The relevance score for each sentence now combines:
        -   The sum of frequencies of matching question keywords (term frequency).
        -   A weighted bonus for each *unique* question keyword present in the sentence.
            This prioritizes sentences that cover a broader range of the question's topics.
        -   Normalization by the square root of the number of content words in the sentence.
            This helps to favor concise, highly relevant sentences over long sentences
            that might coincidentally contain many keywords but are less focused.
    3.  **Multiple Top Sentences**: Instead of returning only sentences with the
        absolute highest score, the function now selects a fixed number of top-scoring
        sentences (e.g., 3). This provides a more comprehensive answer when multiple
        highly relevant pieces of information exist.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    
    # Define a set of common English stop words as an internal constant.
    # Using a frozenset for immutability and O(1) average time complexity for lookups.
    # Note: For very high-performance or frequent calls, this constant would ideally
    # be defined at the module level to avoid recreation on each function call.
    _STOP_WORDS = frozenset([
        "a", "an", "the", "and", "but", "or", "nor", "for", "so", "yet", "at",
        "by", "in", "of", "on", "to", "up", "down", "with", "from", "about",
        "above", "after", "before", "between", "during", "through", "under",
        "over", "is", "am", "are", "was", "were", "be", "being", "been", "have",
        "has", "had", "do", "does", "did", "can", "will", "would", "shall",
        "should", "may", "might", "must", "it", "its", "he", "him", "his", "she",
        "her", "hers", "we", "us", "our", "ours", "you", "your", "yours", "they",
        "them", "their", "theirs", "this", "that", "these", "those", "what",
        "where", "when", "why", "how", "who", "whom", "whose", "which", "if",
        "then", "else", "once", "again", "further", "here", "there", "all", "any",
        "both", "each", "few", "more", "most", "other", "some", "such", "no",
        "not", "only", "own", "same", "so", "than", "too", "very", "s", "t",
        "just", "don", "now", "i", "me", "my", "myself", "yourself", "yourselves",
        "himself", "herself", "itself", "themselves", "having", "doing", "against",
        "also", "however", "therefore", "always", "usually", "often", "seldom",
        "never", "ever"
    ])

    # --- Helper Functions for Text Processing ---
    def _clean_text(text):
        """Lowercase and remove punctuation from text, then split into words.
        Removes common stop words."""
        text = text.lower()
        # Remove anything that's not a letter, number, or space
        text = re.sub(r'[^a-z0-9\s]', '', text)
        words = text.split()
        # Filter out stop words and empty strings
        return [word for word in words if word and word not in _STOP_WORDS]

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
    # Extract unique content words from the question for keyword matching
    question_keywords = set(_clean_text(question))
    
    if not question_keywords:
        return "Thank you for contacting us. Please visit our website for more information."

    # --- 2. Preprocess Knowledge Base ---
    kb_sentences = _split_into_sentences(knowledge_base)
    
    # Store original sentences along with their word frequency counters
    # Pre-computation uses collections.Counter once per sentence after cleaning and stop word removal
    processed_kb_data = []
    for original_sentence in kb_sentences:
        cleaned_words = _clean_text(original_sentence)
        if cleaned_words: # Ensure the sentence is not empty after cleaning
            processed_kb_data.append({
                "original": original_sentence,
                "word_counter": Counter(cleaned_words),
                "num_cleaned_words": len(cleaned_words) # Store count of content words for normalization
            })

    # --- 3. Score Sentences using collections.Counter ---
    # Calculate a relevance score for each sentence in the knowledge base.
    # The score now considers both frequency of keywords and presence of unique keywords,
    # and is normalized by sentence length to favor concise, relevant sentences.
    scored_sentences = []
    for item in processed_kb_data:
        score = 0
        sentence_word_counter = item["word_counter"]
        num_cleaned_words = item["num_cleaned_words"]
        
        # Calculate base score by summing frequencies of question keywords
        # Counter handles missing keys by returning 0, so .get() is not strictly necessary here.
        for q_word in question_keywords:
            score += sentence_word_counter[q_word]

        # Add a bonus for each unique question keyword present in the sentence.
        # This helps prioritize sentences that cover more aspects of the question.
        unique_keywords_found = len(question_keywords.intersection(sentence_word_counter.keys()))
        score += unique_keywords_found * 0.75 # Weighted bonus for unique keyword presence (tunable)

        # Normalize score by the square root of the number of content words in the sentence.
        # This helps prevent very long sentences with low keyword density from dominating.
        # Add a small constant to the denominator for robustness against extremely short sentences.
        if num_cleaned_words > 0:
            score /= (num_cleaned_words ** 0.5) 
        # Sentences with no content words would have num_cleaned_words = 0, score would remain 0,
        # and not be added to scored_sentences, which is desired.

        if score > 0: # Only keep sentences that contain at least one relevant keyword (after scoring)
            scored_sentences.append((score, item["original"]))

    # --- 4. Select Best Sentences ---
    # Sort sentences by their relevance score in descending order
    scored_sentences.sort(key=lambda x: x[0], reverse=True)

    if not scored_sentences:
        return "Thank you for contacting us. We could not find specific information related to your question in our knowledge base. Please visit our website for more information."

    # Select a fixed number of top-scoring sentences for a more comprehensive answer.
    # This prevents returning only one sentence if many are highly relevant.
    MAX_ANSWER_SENTENCES = 3 
    final_relevant_sentences = [sentence for score, sentence in scored_sentences[:MAX_ANSWER_SENTENCES]]

    # --- 5. Formulate Answer ---
    if final_relevant_sentences:
        # Join the selected relevant sentences to form the answer
        answer = " ".join(final_relevant_sentences)
        return f"Regarding your question: {answer}"
    else:
        # Fallback (should ideally be caught by 'if not scored_sentences' earlier, but good for robustness)
        return "Thank you for contacting us. We could not find specific information related to your question in our knowledge base. Please visit our website for more information."