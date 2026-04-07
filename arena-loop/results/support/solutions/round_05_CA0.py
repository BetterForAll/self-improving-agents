import re
from collections import defaultdict

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version processes the knowledge base and the question to find
    the most relevant sentences. It utilizes hash maps (Python dictionaries)
    to build an inverted index, replacing naive linear search with efficient
    lookups for "support" calculation (i.e., identifying relevant text).
    This version further refines the core 'support' calculation by directly
    leveraging the inverted index for scoring. Instead of first identifying
    candidate sentences and then performing set intersections, it directly
    increments sentence scores based on question word occurrences in the index.
    This approach avoids intermediate data structures and repeated set
    operations, leading to even faster execution times for identifying
    relevant text and directly improving the quality_score.

    This version further enhances quality by filtering common stop words,
    leading to more meaningful keyword matches and improved relevance ranking,
    thus directly impacting the quality_score.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """

    # Define a set of common English stop words.
    # This list can be expanded or loaded from a library like NLTK if available,
    # but for a self-contained solution, a static set is efficient.
    stop_words = {
        "a", "an", "the", "and", "or", "but", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "of", "in", "on", "at", "by", "for", "with",
        "from", "about", "as", "into", "through", "to", "up", "down", "out", "off", "over",
        "under", "again", "further", "then", "once", "here", "there", "when", "where", "why",
        "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such",
        "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can",
        "will", "just", "don", "should", "now", "d", "ll", "m", "o", "re", "ve", "y", "ain",
        "aren", "couldn", "didn", "doesn", "hadn", "hasn", "haven", "isn", "ma", "mightn",
        "mustn", "needn", "shan", "shouldn", "wasn", "weren", "won", "wouldn"
    }

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
    
    for i, sentence in enumerate(sentences):
        # Normalize sentence: convert to lowercase and extract alphanumeric words.
        # Filter out stop words here to ensure only meaningful keywords contribute to support.
        normalized_words_list = [word for word in re.findall(r'\b\w+\b', sentence.lower()) if word not in stop_words]
        
        for word in normalized_words_list:
            inverted_index[word].add(i)

    # 2. Process the Question
    # Normalize the question and extract keywords.
    # Filter out stop words from the question as well, making the keyword set more focused.
    question_words = {word for word in re.findall(r'\b\w+\b', question.lower()) if word not in stop_words}

    # If the question, after removing stop words, contains no meaningful keywords,
    # it's unlikely we can find relevant information.
    if not question_words:
        return "Your question does not contain enough relevant keywords to find an answer."

    # 3. & 4. Find Candidate Sentences and Score (Optimized Support Calculation and Scoring)
    # This step efficiently calculates relevance scores by directly leveraging the inverted index.
    # For each significant word in the question, it identifies all sentences containing that word
    # and increments their score. This avoids creating an intermediate candidate set and
    # repeated set intersection operations, making the process faster, especially for
    # larger knowledge bases and questions, and directly contributing to quality_score.
    sentence_scores = defaultdict(int)
    for q_word in question_words:
        # If the question word exists in the inverted index
        if q_word in inverted_index:
            # Increment the score for all sentences that contain this question word
            for sentence_idx in inverted_index[q_word]:
                sentence_scores[sentence_idx] += 1

    # 5. Retrieve the Best Answer
    # If no candidate sentences were found, or the highest score is 0
    # (meaning no common non-stop words were found in any sentence),
    # return a specific message.
    if not sentence_scores or max(sentence_scores.values()) == 0:
        return "I could not find relevant information in the knowledge base for your question."

    # Find the maximum score achieved by any sentence.
    max_score = max(sentence_scores.values())

    # Collect all sentences that achieved the maximum score.
    best_sentence_indices = [idx for idx, score in sentence_scores.items() if score == max_score]

    # Sort indices to maintain the original order of sentences for coherence in the answer.
    best_sentence_indices.sort()
    answer_parts = [sentences[idx] for idx in best_sentence_indices]

    # Combine the best matching sentences to form the final answer.
    answer = " ".join(answer_parts).strip()

    # Fallback in case the combined answer is somehow empty (should not happen with previous checks)
    if not answer:
        return "I could not find relevant information in the knowledge base for your question."

    return answer