import re
from collections import defaultdict

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version leverages an inverted index (hash-based lookup)
    to efficiently find sentences in the knowledge base that are most
    relevant to the customer's question.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    # 1. Preprocessing and Building Inverted Index for the knowledge_base
    # Split the knowledge base into individual sentences.
    # The regex looks for sentence-ending punctuation followed by whitespace.
    sentences = re.split(r'(?<=[.!?])\s+', knowledge_base.strip())
    # Clean up sentences (remove leading/trailing whitespace, filter out empty strings)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return "Thank you for contacting us. No information found in the knowledge base."

    # inverted_index: maps a word to a set of indices of sentences containing that word.
    inverted_index = defaultdict(set)
    # normalized_sentence_token_sets: stores tokenized and normalized words for each sentence,
    # allowing for efficient keyword lookup during scoring.
    normalized_sentence_token_sets = []

    for i, sentence in enumerate(sentences):
        # Normalize the sentence: convert to lowercase and remove non-alphanumeric characters.
        normalized_sentence = re.sub(r'[^\w\s]', '', sentence).lower()
        tokens = normalized_sentence.split()
        
        current_sentence_tokens_set = set()
        for token in tokens:
            if token: # Ensure token is not empty
                inverted_index[token].add(i)
                current_sentence_tokens_set.add(token)
        normalized_sentence_token_sets.append(current_sentence_tokens_set)

    # 2. Process the question
    # Normalize the question in the same way as sentences.
    normalized_question = re.sub(r'[^\w\s]', '', question).lower()
    question_keywords = set(normalized_question.split())

    if not question_keywords:
        return "Thank you for contacting us. Please rephrase your question with more specific terms."

    # 3. Find relevant sentences and score them
    # Use the inverted index to quickly identify potential candidate sentences.
    # This significantly reduces the number of sentences to check for relevance.
    candidate_sentence_indices = set()
    for keyword in question_keywords:
        if keyword in inverted_index:
            candidate_sentence_indices.update(inverted_index[keyword])

    if not candidate_sentence_indices:
        # If no keywords from the question are found in the knowledge base,
        # return a polite fallback message.
        return "Thank you for contacting us. We couldn't find a direct answer to your question in our knowledge base. Please visit our website for more information."

    # Score only the candidate sentences. The score is the number of question keywords
    # that appear in a given sentence.
    sentence_scores = {}
    for idx in candidate_sentence_indices:
        score = len(question_keywords.intersection(normalized_sentence_token_sets[idx]))
        if score > 0: # Only store sentences with at least one matching keyword
            sentence_scores[idx] = score

    # 4. Select and return the best answer
    max_score = 0
    best_sentence_index = -1

    if sentence_scores:
        # Find the sentence with the highest score.
        # If multiple sentences have the same highest score, `max` will return one of them.
        best_sentence_index = max(sentence_scores, key=sentence_scores.get)
        max_score = sentence_scores[best_sentence_index]

    if max_score > 0:
        return sentences[best_sentence_index]
    else:
        # This fallback handles cases where candidate_sentence_indices had elements,
        # but all their scores turned out to be 0 (e.g., due to stop words not being filtered).
        return "Thank you for contacting us. We couldn't find a direct answer to your question in our knowledge base. Please visit our website for more information."