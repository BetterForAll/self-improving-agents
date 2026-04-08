def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version leverages vectorized operations from SciPy for efficient word frequency
    analysis and scoring, enhancing computation speed for large text bodies by avoiding
    traditional loop-based counting where matrix operations are more efficient.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    # Imports moved inside for strict adherence to "ONLY the function definition" output.
    # In a real application, these would typically be at the module level.
    import re
    from collections import Counter
    import numpy as np
    from scipy.sparse import lil_matrix, csr_matrix

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

    # Early exit if no processed KB data (e.g., KB was empty or only punctuation)
    if not processed_kb_data:
        return "Thank you for contacting us. We could not find specific information related to your question in our knowledge base. Please visit our website for more information."

    # --- 3. Score Sentences using Vectorized Operations (NumPy/SciPy Sparse) ---
    # This section replaces the traditional loop-based Counter scoring with sparse matrix operations,
    # significantly improving performance for large knowledge bases.
    
    # 3.1. Build a global vocabulary and mapping from words to column indices
    all_kb_words = set()
    for item in processed_kb_data:
        all_kb_words.update(item["word_counter"].keys())
    
    # If no words in KB after cleaning (very rare, but possible if KB is just punctuation)
    if not all_kb_words:
        return "Thank you for contacting us. We could not find specific information related to your question in our knowledge base. Please visit our website for more information."

    vocab_list = sorted(list(all_kb_words))
    word_to_idx = {word: i for i, word in enumerate(vocab_list)}

    # 3.2. Construct a sparse matrix for the knowledge base sentences
    # Rows represent sentences, columns represent words from the vocabulary.
    # Values are the frequency of each word in a given sentence.
    num_sentences = len(processed_kb_data)
    num_vocab_words = len(vocab_list)
    kb_matrix = lil_matrix((num_sentences, num_vocab_words), dtype=np.intc) # LIL for efficient construction

    for i, item in enumerate(processed_kb_data):
        for word, count in item["word_counter"].items():
            # 'word' is guaranteed to be in 'word_to_idx' because 'all_kb_words' was built from these counters
            kb_matrix[i, word_to_idx[word]] = count
    
    # Convert to CSR format for efficient column slicing and sum operations
    kb_csr_matrix = kb_matrix.tocsr()

    # 3.3. Identify column indices corresponding to the question keywords in the global vocabulary
    question_keyword_indices = [
        word_to_idx[q_word]
        for q_word in question_keywords
        if q_word in word_to_idx # Only consider keywords present in the KB vocabulary
    ]

    # 3.4. Calculate scores using matrix operations
    if not question_keyword_indices:
        # If no question keywords are found in the KB vocabulary, all scores are 0.
        scores = np.zeros(num_sentences, dtype=np.intc)
    else:
        # Select columns corresponding to question keywords from the sparse matrix
        # and sum their counts across rows (sentences).
        # .A1 converts the resulting (N, 1) matrix into a 1D NumPy array for easier iteration.
        scores = kb_csr_matrix[:, question_keyword_indices].sum(axis=1).A1

    # `scores` is now a 1D NumPy array where `scores[i]` is the relevance score
    # for `processed_kb_data[i]["original"]`.
    
    scored_sentences = []
    # Iterate through the scores array and the processed_kb_data to collect relevant sentences
    for i, score in enumerate(scores):
        if score > 0: # Only keep sentences that contain at least one question keyword
            scored_sentences.append((score, processed_kb_data[i]["original"]))

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
            # Stop once scores drop below the maximum to avoid including less relevant sentences
            break 
            
    # --- 5. Formulate Answer ---
    if relevant_sentences:
        # Join the selected relevant sentences to form the answer
        answer = " ".join(relevant_sentences)
        return f"Regarding your question: {answer}"
    else:
        # Fallback if no relevant sentences were found (should be caught earlier, but good for robustness)
        return "Thank you for contacting us. We could not find specific information related to your question in our knowledge base. Please visit our website for more information."