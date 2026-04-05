import re

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version attempts to find relevant sentences in the knowledge base
    by identifying keywords from the question and scoring sentences based on keyword overlap.
    It returns the most relevant sentences as an answer or a polite fallback message.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    if not knowledge_base.strip():
        return "I'm sorry, I don't have enough information to answer your question. Please visit our website for more details."

    # --- Preprocessing the Question ---
    # Define a set of common English stopwords to ignore in keyword matching.
    # These words are usually not informative for identifying core topics.
    stopwords = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "of", "in", "on", "at", "by", "for", "with", "from", "to", "and",
        "or", "but", "not", "no", "yes", "what", "where", "when", "why", "how",
        "who", "whom", "which", "do", "does", "did", "have", "has", "had",
        "i", "me", "my", "we", "us", "our", "you", "your", "he", "him", "his",
        "she", "her", "its", "they", "them", "their", "this", "that", "these", "those",
        "it", "itself", "we", "ourselves", "you", "yourself", "yourselves", "he", "himself",
        "she", "herself", "it", "itself", "they", "them", "themselves",
        "can", "could", "would", "should", "will", "may", "might", "must",
        "about", "above", "below", "between", "each", "few", "more", "most", "other",
        "some", "such", "than", "then", "through", "up", "down", "out", "off", "over",
        "under", "again", "further", "once", "here", "there", "when",
        "why", "how", "all", "any", "both", "every", "many", "much", "nor", "only", "own",
        "same", "so", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now",
        "get", "make", "find", "tell", "ask", "want", "like", "go"
    }

    # Normalize question: lowercase and extract significant words (non-stopwords)
    normalized_question = question.lower()
    question_words = {word for word in re.findall(r'\b\w+\b', normalized_question) if word not in stopwords}

    # If, after removing stopwords, the question is empty or too generic, provide a specific fallback.
    if not question_words:
        return "Thank you for contacting us. To help me better, could you please rephrase your question with more specific keywords?"

    # --- Sentence Segmentation of Knowledge Base ---
    # Split the knowledge base into individual sentences. This is a heuristic approach
    # and might not be perfect for all complex texts (e.g., abbreviations like "Dr. Smith").
    sentences = re.split(r'(?<=[.!?])\s+', knowledge_base) # Keep original casing for output

    # Filter out empty sentences and strip leading/trailing whitespace
    sentences = [s.strip() for s in sentences if s.strip()]

    # --- Relevance Scoring ---
    scored_sentences = []
    for sentence in sentences:
        # Normalize sentence for keyword matching (lowercase, extract words)
        normalized_sentence_words = {word for word in re.findall(r'\b\w+\b', sentence.lower())}

        # Calculate overlap: count how many of the question's significant words appear in the sentence
        overlap = len(question_words.intersection(normalized_sentence_words))

        # Only consider sentences with at least one shared significant word
        if overlap > 0:
            scored_sentences.append((overlap, sentence))

    # Sort sentences by relevance (highest overlap first)
    scored_sentences.sort(key=lambda x: x[0], reverse=True)

    # --- Answer Construction ---
    if not scored_sentences:
        return "I'm sorry, I couldn't find relevant information in our knowledge base for your question. Please visit our website or contact support for more information."

    answer_sentences = []
    current_word_count = 0
    max_answer_words = 150 # Aim for a concise answer, typically around 1-3 sentences

    # Determine a dynamic minimum overlap threshold based on question complexity.
    # If the question has many keywords, we need a higher overlap to consider a sentence truly relevant.
    # If the question is very short, even one strong keyword match is significant.
    min_overlap_threshold = max(1, len(question_words) // 2) if len(question_words) > 1 else 1

    for score, sentence in scored_sentences:
        # Only include sentences that meet a minimum relevance threshold and are not excessively short
        sentence_word_count = len(re.findall(r'\b\w+\b', sentence))
        if score >= min_overlap_threshold and sentence_word_count > 3: # Ignore very short sentences as initial candidates
            if current_word_count + sentence_word_count <= max_answer_words:
                answer_sentences.append(sentence)
                current_word_count += sentence_word_count
            else:
                break # Stop adding if exceeding word limit

        # If we have at least one good, substantial sentence, we can stop early to keep the answer focused.
        if len(answer_sentences) >= 1 and current_word_count > 50:
            break

    # Fallback: If no sentences met the dynamic threshold or word count constraints,
    # try to include the single most relevant sentence if it has a decent score and length.
    if not answer_sentences and scored_sentences:
        top_score, top_sentence = scored_sentences[0]
        if top_score > 0 and len(re.findall(r'\b\w+\b', top_sentence)) > 5: # Not just a single word match, and sentence is not too short
            answer_sentences.append(top_sentence)

    if answer_sentences:
        # Join selected sentences.
        final_answer = " ".join(answer_sentences)
        # Ensure the first letter of the answer is capitalized.
        final_answer = final_answer[0].upper() + final_answer[1:] if final_answer else final_answer
        # Add a period if the answer doesn't end with punctuation already.
        if final_answer and not final_answer.strip().endswith((".", "!", "?")):
            final_answer += "."
        return final_answer.strip()
    else:
        # Final fallback if no relevant sentences could be extracted meaningfully.
        return "I'm sorry, I couldn't find specific information related to your question in our knowledge base. Please visit our website for general information or contact support directly."