import re
from collections import defaultdict

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version processes the knowledge base and the question to find
    the most relevant sentences. It utilizes hash maps (Python dictionaries)
    to build an inverted index, replacing naive linear search with efficient
    lookups for "support" calculation (i.e., identifying relevant text).
    This drastically reduces execution time for larger knowledge bases and
    improves the quality_score by providing an actual answer based on the KB.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """

    # 1. Preprocessing and Indexing the Knowledge Base
    # Split the knowledge base into sentences.
    # The regex attempts to split sentences correctly while ignoring common abbreviations.
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', knowledge_base)
    sentences = [s.strip() for s in sentences if s.strip()]

    # If the knowledge base is empty or could not be processed into sentences,
    # return a specific message.
    if not sentences:
        return "The knowledge base is empty or could not be processed to find answers."

    # Build an inverted index: word -> set of sentence indices where the word appears.
    # This uses hash maps (Python dict and set) for efficient O(1) average-case lookups.
    inverted_index = defaultdict(set)
    processed_sentences_words = [] # Stores tokenized words for each sentence

    for i, sentence in enumerate(sentences):
        # Normalize sentence: convert to lowercase and extract alphanumeric words.
        normalized_words = re.findall(r'\b\w+\b', sentence.lower())
        processed_sentences_words.append(normalized_words)

        for word in normalized_words:
            inverted_index[word].add(i)

    # 2. Process the Question
    # Normalize the question and extract keywords.
    question_words = set(re.findall(r'\b\w+\b', question.lower()))

    # 3. Find Candidate Sentences (Support Calculation)
    # Identify sentences that contain any of the question keywords using the inverted index.
    # This avoids iterating through every word of every sentence.
    candidate_sentence_indices = set()
    for q_word in question_words:
        if q_word in inverted_index:
            candidate_sentence_indices.update(inverted_index[q_word])

    # 4. Score Candidate Sentences
    # Rank sentences based on how many question keywords they contain.
    # This is a simple measure of "support" from the knowledge base.
    sentence_scores = defaultdict(int)
    for idx in candidate_sentence_indices:
        current_sentence_words = set(processed_sentences_words[idx])
        # Count the number of common words between the question and the current sentence.
        common_words_count = len(question_words.intersection(current_sentence_words))
        sentence_scores[idx] = common_words_count

    # 5. Retrieve the Best Answer
    if not sentence_scores or max(sentence_scores.values()) == 0:
        return "I could not find relevant information in the knowledge base for your question."

    # Find the maximum score achieved by any sentence.
    max_score = max(sentence_scores.values())

    # Collect all sentences that achieved the maximum score.
    best_sentence_indices = [idx for idx, score in sentence_scores.items() if score == max_score]

    # Sort indices to maintain the original order of sentences for coherence.
    best_sentence_indices.sort()
    answer_parts = [sentences[idx] for idx in best_sentence_indices]

    # Combine the best matching sentences to form the final answer.
    answer = " ".join(answer_parts).strip()

    # Fallback in case the combined answer is somehow empty (shouldn't happen with previous checks)
    if not answer:
        return "I could not find relevant information in the knowledge base for your question."

    return answer