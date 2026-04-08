import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version leverages scikit-learn's TfidfVectorizer for efficient
    text representation and cosine similarity for relevance scoring. This approach
    significantly enhances both answer quality (via TF-IDF weighting and stop-word
    removal) and computation speed for large knowledge bases by utilizing vectorized
    operations from highly optimized libraries.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """

    # --- Helper Function for Sentence Splitting ---
    def _split_into_sentences(text):
        """
        Split text into sentences using basic punctuation rules.
        Handles common abbreviations like "Mr.", "U.S." to avoid incorrect splits.
        """
        # Regex to split sentences at periods, question marks, or exclamation points,
        # but not after abbreviations (like "Dr.") or decimals.
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', text)
        return [s.strip() for s in sentences if s.strip()]

    # --- TF-IDF Vectorizer Preprocessor ---
    # This preprocessor ensures text is consistently cleaned (lowercased, non-alphanumeric removed)
    # before TfidfVectorizer's internal tokenizer processes it.
    def tfidf_preprocessor(text):
        text = text.lower()
        # Remove anything that's not a letter, number, or space
        text = re.sub(r'[^a-z0-9\s]', '', text)
        return text

    # --- 1. Initial Question Check ---
    # A simple check for an empty or meaningless question before heavy processing.
    # We apply the same cleaning logic as our TFIDF preprocessor would.
    if not tfidf_preprocessor(question).strip():
        return "Thank you for contacting us. Please visit our website for more information."

    # --- 2. Preprocess Knowledge Base ---
    kb_sentences = _split_into_sentences(knowledge_base)
    
    # Filter out any empty sentences that might result from splitting or cleaning
    kb_sentences_cleaned = [s for s in kb_sentences if s.strip()]

    if not kb_sentences_cleaned:
        return "Thank you for contacting us. We could not find any readable sentences in our knowledge base. Please visit our website for more information."

    # --- 3. Vectorize Knowledge Base and Question using TF-IDF ---
    # Initialize TfidfVectorizer.
    # - `preprocessor`: Uses our custom function for consistent text cleaning.
    # - `token_pattern`: Matches sequences of alphanumeric characters, effectively treating
    #    anything else as a delimiter. This aligns with the original word definition.
    # - `stop_words='english'`: Removes common English stop words (e.g., "the", "is")
    #    to focus on more meaningful terms for relevance, enhancing quality.
    vectorizer = TfidfVectorizer(
        preprocessor=tfidf_preprocessor,
        token_pattern=r'\b\w+\b', 
        stop_words='english',
        max_features=5000 # Limit vocabulary size for very large KBs to manage memory/speed
    )

    # Fit the vectorizer on the knowledge base sentences and transform them.
    # This creates a sparse matrix where each row is a sentence and columns are TF-IDF weighted terms.
    kb_tfidf_matrix = vectorizer.fit_transform(kb_sentences_cleaned)

    # Transform the question into a TF-IDF vector using the *same* vectorizer.
    question_tfidf_vector = vectorizer.transform([question])

    # Check if the question contains any terms found in the KB vocabulary.
    # If not, the vector will be all zeros, indicating no relevant match.
    if question_tfidf_vector.nnz == 0:
        return "Thank you for contacting us. We could not find specific information related to your question in our knowledge base. Please visit our website for more information."

    # --- 4. Score Sentences using Cosine Similarity ---
    # Calculate cosine similarity between the question vector and each sentence vector
    # in the KB matrix. This is a highly efficient, vectorized operation.
    # The result is an array of scores, one for each sentence.
    similarity_scores = cosine_similarity(question_tfidf_vector, kb_tfidf_matrix).flatten()

    # --- 5. Select Best Sentences ---
    scored_sentences = []
    for i, score in enumerate(similarity_scores):
        if score > 0: # Only consider sentences with a positive similarity score
            scored_sentences.append((score, kb_sentences_cleaned[i]))

    # Sort sentences by their relevance score in descending order
    scored_sentences.sort(key=lambda x: x[0], reverse=True)

    if not scored_sentences:
        # Fallback if no relevant sentences were found after TF-IDF and similarity calculation.
        return "Thank you for contacting us. We could not find specific information related to your question in our knowledge base. Please visit our website for more information."

    # Collect sentences that are highly relevant.
    # We aim to provide a comprehensive answer by including sentences that are
    # sufficiently close in relevance to the top-scoring one, up to a limit.
    max_score = scored_sentences[0][0]
    
    # Define a relative threshold: include sentences that are at least 80% as relevant as the top one.
    # This helps capture supporting details.
    relevance_threshold = max_score * 0.8 if max_score > 0 else 0
    
    # Limit the number of sentences in the answer to avoid overly verbose responses.
    max_answer_sentences = 5 

    relevant_sentences = []
    seen_sentences = set() # To ensure unique sentences in the final answer

    for score, sentence in scored_sentences:
        # Include sentences if their score meets the threshold and we haven't reached the limit
        if score >= relevance_threshold and len(relevant_sentences) < max_answer_sentences:
            if sentence not in seen_sentences:
                relevant_sentences.append(sentence)
                seen_sentences.add(sentence)
        elif len(relevant_sentences) >= max_answer_sentences: # Stop if max sentences reached
            break
        elif score < relevance_threshold and len(relevant_sentences) > 0: # Stop if score drops below threshold and we have some sentences
            break
        elif max_score == 0: # If the max_score itself is 0, break early as no true relevance was found
            break

    # Final fallback if, after all filtering, no sentences were selected (e.g., due to a very high threshold)
    if not relevant_sentences and scored_sentences:
        # As a last resort, just take the absolute top-scoring sentence if available.
        if scored_sentences[0][0] > 0: # Only if it has some positive score
            relevant_sentences.append(scored_sentences[0][1])

    # --- 6. Formulate Answer ---
    if relevant_sentences:
        answer = " ".join(relevant_sentences)
        return f"Regarding your question: {answer}"
    else:
        # Final fallback if no relevant sentences could be constructed.
        return "Thank you for contacting us. We could not find specific information related to your question in our knowledge base. Please visit our website for more information."