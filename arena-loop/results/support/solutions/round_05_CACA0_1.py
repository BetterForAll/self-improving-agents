import re
from collections import defaultdict

# Pre-compile regex patterns for efficiency. These are only compiled once.
SENTENCE_SPLITTER = re.compile(r'(?<=[.!?])\s+')
WORD_NORMALIZER = re.compile(r'[^\w\s]')

# Define a set of common English stop words. This is initialized once.
# Filtering these words reduces the size of the inverted index, the number of
# tokens processed, and improves the relevance of matches by focusing on
# more significant terms.
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
    to efficiently find sentences in the knowledge base that are most
    relevant to the customer's question. It further optimizes by:
    - Pre-compiling regular expressions to avoid repeated compilation, saving CPU cycles.
    - Filtering out common English stop words during index building and query processing.
      This fundamentally reduces the number of operations by:
        - Decreasing the number of entries in the inverted index.
        - Reducing the size of token sets stored for each sentence.
        - Minimizing the number of keywords to process from the question.
        - Leading to fewer candidate sentences and faster set intersections during scoring,
          which directly enhances execution speed.

    The key improvement in this version is a more efficient scoring mechanism during query time.
    Instead of first gathering all unique candidate sentence indices and then performing
    set intersections for scoring, this version directly tallies the number of matching
    keywords for each potential sentence using the inverted index. This eliminates the
    overhead of explicit set union operations for `candidate_sentence_indices` and
    the subsequent set intersection for each candidate, leading to a direct reduction
    in the total number of operations required for scoring.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    # 1. Preprocessing and Building Inverted Index for the knowledge_base
    # Use pre-compiled regex for splitting sentences.
    sentences = SENTENCE_SPLITTER.split(knowledge_base.strip())
    # Clean up sentences (remove leading/trailing whitespace, filter out empty strings)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return "Thank you for contacting us. No information found in the knowledge base."

    # inverted_index: maps a non-stop word to a set of indices of sentences containing that word.
    inverted_index = defaultdict(set)
    # normalized_sentence_token_sets: stores tokenized and normalized non-stop words for each sentence.
    # This is kept for consistency with the original structure, though the new scoring logic
    # primarily relies on the `inverted_index` for efficiency.
    normalized_sentence_token_sets = []

    for i, sentence in enumerate(sentences):
        # Normalize the sentence using pre-compiled regex.
        normalized_sentence = WORD_NORMALIZER.sub('', sentence).lower()
        tokens = normalized_sentence.split()
        
        current_sentence_tokens_set = set()
        for token in tokens:
            # Only add non-empty and non-stop words to the index and token set.
            if token and token not in STOP_WORDS:
                inverted_index[token].add(i)
                current_sentence_tokens_set.add(token)
        normalized_sentence_token_sets.append(current_sentence_tokens_set)

    # 2. Process the question
    # Normalize the question using pre-compiled regex.
    normalized_question = WORD_NORMALIZER.sub('', question).lower()
    # Filter out stop words from question keywords.
    question_keywords = {token for token in normalized_question.split() if token and token not in STOP_WORDS}

    if not question_keywords:
        # If the question is empty or only contains stop words after processing.
        return "Thank you for contacting us. Please rephrase your question with more specific terms."

    # 3. Find relevant sentences and score them
    # Use the inverted index to directly tally scores.
    # The score for a sentence is the count of how many unique question keywords
    # (non-stop words) appear in that sentence. This is more efficient than
    # first collecting candidate indices and then performing set intersections.
    sentence_scores = defaultdict(int)
    for keyword in question_keywords:
        # If a keyword from the question is found in our inverted index,
        # iterate through all sentences that contain this keyword.
        if keyword in inverted_index:
            for sentence_idx in inverted_index[keyword]:
                sentence_scores[sentence_idx] += 1

    if not sentence_scores:
        # If no keywords from the question (after stop-word filtering) are found in the knowledge base,
        # or if no sentences scored higher than 0.
        return "Thank you for contacting us. We couldn't find a direct answer to your question in our knowledge base. Please visit our website for more information."

    # 4. Select and return the best answer
    # Find the sentence with the highest score.
    # Since sentence_scores only contains entries for sentences with at least one match,
    # and all scores are positive integers due to the direct tallying, this will
    # correctly find the best match.
    best_sentence_index = max(sentence_scores, key=sentence_scores.get)
    
    return sentences[best_sentence_index]