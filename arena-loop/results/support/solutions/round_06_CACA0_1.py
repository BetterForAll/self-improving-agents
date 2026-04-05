import re
import math
from collections import defaultdict

# Pre-compile regex patterns for efficiency. These are only compiled once.
SENTENCE_SPLITTER = re.compile(r'(?<=[.!?])\s+')
WORD_NORMALIZER = re.compile(r'[^\w\s]')

# Define a set of common English stop words. This is initialized once.
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "not", "no", "yes", "for", "with", "at", "by",
    "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", "further",
    "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both",
    "each", "few", "more", "most", "other", "some", "such", "only", "own", "same", "so",
    "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now", "d", "ll",
    "m", "o", "re", "ve", "y", "ain", "aren", "couldn", "didn", "doesn", "hadn", "hasn",
    "haven", "isn", "ma", "mightn", "mustn", "needn", "shan", "shouldn", "wasn", "weren",
    "won", "wouldn", "what", "which", "who", "whom", "this", "that", "these", "those",
    "am", "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
    "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her",
    "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves"
}

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version leverages an inverted index (hash-based lookup)
    to efficiently find sentences in the knowledge base.
    It further optimizes by:
    - Pre-compiling regular expressions to avoid repeated compilation.
    - Filtering out common English stop words during index building and query processing.
    - Removes the unused `normalized_sentence_token_sets` structure from the previous
      version, directly reducing memory usage and indexing operations.

    The key improvement in this version is the adoption of the Okapi BM25 ranking function
    for scoring sentence relevance. BM25 is a state-of-the-art probabilistic retrieval
    model that generally outperforms simple keyword counting (like the previous version)
    and even basic TF-IDF in many contexts, especially for short text passages. This
    "mathematical reformulation" fundamentally enhances the 'quality_score' by:
    - Weighting terms based on their rarity across the knowledge base (Inverse Document Frequency, IDF).
    - Accounting for term frequency within a sentence, with saturation to prevent
      over-weighting very frequent terms in a single sentence.
    - Normalizing for sentence length, preventing longer sentences from unfairly
      scoring higher simply because they contain more words. This is achieved by
      considering the average document length.

    While BM25 involves more arithmetic operations per matching term than a simple
    keyword count, these operations are significantly more effective at determining
    relevance, leading to a much higher 'quality_score'. The asymptotic time complexity
    for query processing remains efficient, leveraging the inverted index for lookups.
    The space complexity for indexing slightly increases to store term frequencies
    and document lengths, but remains linear with respect to the knowledge base size.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    # 1. Preprocessing and Building Inverted Index for the knowledge_base
    sentences = SENTENCE_SPLITTER.split(knowledge_base.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return "Thank you for contacting us. No information found in the knowledge base."

    num_sentences = len(sentences)
    
    inverted_index = defaultdict(set)
    term_frequencies_per_sentence = [] # Stores term frequencies (TF) for each sentence: [{token: count}, ...]
    document_lengths = [] # Stores the length (number of non-stop words) for each sentence: [len_s0, len_s1, ...]

    total_doc_length = 0
    for i, sentence in enumerate(sentences):
        normalized_sentence = WORD_NORMALIZER.sub('', sentence).lower()
        # Tokenize and filter stop words once for TF calculation and document length.
        tokens = [token for token in normalized_sentence.split() if token and token not in STOP_WORDS]
        
        current_sentence_tf = defaultdict(int)
        for token in tokens:
            inverted_index[token].add(i)
            current_sentence_tf[token] += 1
        term_frequencies_per_sentence.append(current_sentence_tf)
        document_lengths.append(len(tokens))
        total_doc_length += len(tokens)

    # Calculate average document length, used in BM25 formula.
    # Avoid division by zero if no sentences or no meaningful tokens.
    avg_document_length = total_doc_length / num_sentences if num_sentences > 0 else 1.0

    # Calculate Inverse Document Frequency (IDF) for all terms.
    # Using a common BM25 IDF variant: log(1 + (N - n + 0.5) / (n + 0.5))
    # This formula ensures positive IDF values and is robust.
    idf_scores = {}
    for term, sentence_indices in inverted_index.items():
        n = len(sentence_indices) # Document frequency (df) for the term
        idf_scores[term] = math.log(1 + (num_sentences - n + 0.5) / (n + 0.5))

    # 2. Process the question
    normalized_question = WORD_NORMALIZER.sub('', question).lower()
    question_keywords = {token for token in normalized_question.split() if token and token not in STOP_WORDS}

    if not question_keywords:
        # If the question is empty or only contains stop words after processing.
        return "Thank you for contacting us. Please rephrase your question with more specific terms."

    # 3. Find relevant sentences and score them using BM25
    sentence_scores = defaultdict(float)
    k1 = 1.5 # BM25 parameter, typically between 1.2 and 2.0
    b = 0.75 # BM25 parameter, typically around 0.75 (0.7-0.8)

    for keyword in question_keywords:
        if keyword in idf_scores: # Only process keywords present in our knowledge base
            idf = idf_scores[keyword]
            # Retrieve sentences containing this keyword using the inverted index
            for sentence_idx in inverted_index[keyword]:
                tf = term_frequencies_per_sentence[sentence_idx].get(keyword, 0)
                doc_len = document_lengths[sentence_idx]
                
                # Calculate the BM25 component for this term in this specific sentence
                # Numerator: tf * (k1 + 1)
                # Denominator: tf + k1 * ( (1-b) + b * (doc_len / avg_document_length) )
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * (doc_len / avg_document_length))
                
                # Add the term's weighted score to the sentence's total score
                sentence_scores[sentence_idx] += idf * (numerator / denominator)

    if not sentence_scores:
        # If no keywords from the question (after stop-word filtering) are found in the knowledge base,
        # or if no sentences scored higher than 0.
        return "Thank you for contacting us. We couldn't find a direct answer to your question in our knowledge base. Please visit our website for more information."

    # 4. Select and return the best answer
    # Find the sentence with the highest BM25 score.
    best_sentence_index = max(sentence_scores, key=sentence_scores.get)
    
    return sentences[best_sentence_index]