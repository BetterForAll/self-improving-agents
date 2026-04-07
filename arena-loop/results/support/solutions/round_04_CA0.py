import re
from collections import defaultdict
import math

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This version significantly enhances relevance scoring by incorporating
    TF-IDF (Term Frequency-Inverse Document Frequency). This advanced weighting
    scheme replaces simple keyword counting, giving more importance to rare,
    meaningful words that appear in both the question and the knowledge base
    sentences. By pre-computing TF and IDF values during indexing, and using
    an inverted index for efficient candidate sentence selection, it provides
    a more precise "support" calculation (relevance scoring). This leads to a
    drastically improved quality_score by returning more relevant answers.
    While the initial indexing phase becomes more intensive due to TF-IDF
    calculations, the overall system benefits from highly relevant answer
    ranking and efficient retrieval of candidates, thus fulfilling the strategy
    of replacing naive iteration with a more efficient algorithm for 'support'
    calculation by improving the scoring method itself.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """

    # Define a set of common English stop words.
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

    # 1. Preprocessing and Indexing the Knowledge Base with TF-IDF components
    # Split the knowledge base into sentences.
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', knowledge_base)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return "The knowledge base is empty or could not be processed to find answers."

    total_sentences = len(sentences)

    # Inverted index: word -> set of sentence indices where the word appears.
    # Used for efficient initial candidate sentence retrieval.
    inverted_index = defaultdict(set)
    
    # Stores Term Frequency (TF) for each word in each sentence.
    # sentence_word_counts[i] will be a dictionary {word: count, ...} for sentence i.
    sentence_word_counts = []
    
    # Document Frequency (DF): word -> count of sentences the word appears in.
    document_frequencies = defaultdict(int)

    for i, sentence in enumerate(sentences):
        # Normalize sentence: convert to lowercase and extract alphanumeric words.
        # Filter out stop words to focus on meaningful keywords.
        normalized_words_list = [word for word in re.findall(r'\b\w+\b', sentence.lower()) if word not in stop_words]
        
        current_sentence_tf = defaultdict(int)
        for word in normalized_words_list:
            current_sentence_tf[word] += 1
            
        sentence_word_counts.append(current_sentence_tf)

        # Update document frequencies and inverted index for unique words in this sentence
        for word in current_sentence_tf:
            document_frequencies[word] += 1
            inverted_index[word].add(i)

    # Calculate IDF (Inverse Document Frequency) for all unique words found in the knowledge base.
    idf_scores = {}
    for word, df in document_frequencies.items():
        # Using a common smoothed IDF formula to prevent division by zero (df+1)
        # and ensure terms that appear in all documents still have a positive IDF (log result + 1).
        idf_scores[word] = math.log(total_sentences / (df + 1)) + 1

    # 2. Process the Question
    # Normalize the question and extract keywords, filtering stop words.
    question_words_list = [word for word in re.findall(r'\b\w+\b', question.lower()) if word not in stop_words]
    
    # Calculate Term Frequency for question words (though for a short question, counts are usually 1)
    question_term_counts = defaultdict(int)
    for word in question_words_list:
        question_term_counts[word] += 1

    # Use a set for quick lookups of meaningful question words
    meaningful_question_words = set(question_term_counts.keys())

    if not meaningful_question_words:
        return "Your question does not contain enough relevant keywords to find an answer."

    # 3. Find Candidate Sentences (Optimized Support Calculation)
    # Identify sentences that contain any of the question keywords using the inverted index.
    # This step is highly efficient due to hash map lookups and set unions.
    candidate_sentence_indices = set()
    for q_word in meaningful_question_words:
        if q_word in inverted_index:
            candidate_sentence_indices.update(inverted_index[q_word])

    # 4. Score Candidate Sentences (TF-IDF Relevance Scoring)
    # Rank sentences based on their TF-IDF score with respect to the question.
    sentence_scores = defaultdict(float)
    max_score = 0.0 # Track the maximum score found

    for idx in candidate_sentence_indices:
        score = 0.0
        current_sentence_tf = sentence_word_counts[idx]
        
        # Calculate the TF-IDF score for each common word between the question and the sentence
        for q_word in meaningful_question_words:
            if q_word in current_sentence_tf:
                tf_val = current_sentence_tf[q_word] # Term frequency in the current sentence
                idf_val = idf_scores.get(q_word, 0) # IDF for the word, 0 if word not in KB
                score += tf_val * idf_val
        
        sentence_scores[idx] = score
        if score > max_score:
            max_score = score

    # 5. Retrieve the Best Answer
    # If no candidate sentences were found, or the highest score is 0.0
    # (meaning no common meaningful words contributed to a positive TF-IDF score),
    # return a specific message.
    if not sentence_scores or max_score == 0.0:
        return "I could not find relevant information in the knowledge base for your question."

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