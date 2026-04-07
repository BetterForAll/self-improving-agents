import re

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version uses keyword matching to find relevant sentences in the
    knowledge base and constructs an answer from them.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    # 1. Preprocessing and Keyword Extraction
    # Helper function to convert text to lowercase and remove most punctuation, keeping alphanumeric characters.
    def preprocess_text(text):
        text = text.lower()
        # Remove punctuation, keeping only letters, numbers, and spaces.
        text = re.sub(r'[^\w\s]', '', text)
        return text

    processed_question = preprocess_text(question)
    # Convert to a set for faster lookup and to remove duplicate words
    question_words = set(processed_question.split())

    # A basic list of common English stop words to filter out less meaningful words
    stop_words = set([
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "and", "or", "but", "if", "then", "else", "when", "where", "why", "how",
        "for", "at", "by", "from", "in", "on", "out", "over", "under", "up", "down",
        "to", "of", "with", "about", "above", "below", "before", "after", "through",
        "again", "further", "then", "once", "here", "there", "what", "which", "who",
        "whom", "this", "that", "these", "those", "am", "i", "me", "my", "myself",
        "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself",
        "he", "him", "his", "himself", "she", "her", "hers", "herself",
        "it", "its", "itself", "they", "them", "their", "theirs", "themselves",
        "do", "does", "did", "doing", "have", "has", "had", "having", "will", "would",
        "can", "could", "should", "may", "might", "must", "say", "said", "get", "got",
        "please", "thank", "you", "could", "help", "me", "know", "want", "tell"
    ])

    # Filter out stop words and single-letter words from the question to get meaningful keywords
    keywords = {word for word in question_words if word not in stop_words and len(word) > 1}

    # If all potential keywords were stop words or too short, or the question was very short/empty,
    # use all original question words as a fallback to avoid an empty keyword set.
    if not keywords and question_words:
        keywords = question_words
    elif not keywords: # If question_words itself was empty after processing (e.g., empty string question)
        return "I apologize, but I couldn't understand your question. Please provide more details."


    # 2. Split knowledge_base into sentences
    # A robust regex for splitting text into sentences.
    # It handles common sentence endings (., ?, !) and tries to avoid splitting on abbreviations or decimal points.
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', knowledge_base)

    relevant_sentences = []
    # Score each sentence based on keyword overlap with the question
    for sentence_original in sentences:
        if not sentence_original.strip(): # Skip empty or whitespace-only sentences
            continue

        processed_sentence = preprocess_text(sentence_original)
        sentence_words = set(processed_sentence.split())

        # Calculate the number of overlapping keywords between the question and the sentence
        common_words_count = len(keywords.intersection(sentence_words))

        # A sentence is considered relevant if it shares at least one keyword.
        # More sophisticated scoring could involve TF-IDF or word embeddings, but this is a simple baseline improvement.
        if common_words_count > 0:
            # Store the relevance score and the original sentence (to preserve its casing and punctuation)
            relevant_sentences.append((common_words_count, sentence_original))

    # Sort sentences by their relevance score in descending order
    relevant_sentences.sort(key=lambda x: x[0], reverse=True)

    # 3. Construct the answer from the most relevant sentences
    if relevant_sentences:
        answer_parts = []
        seen_sentences = set() # Use a set to prevent adding duplicate sentences to the answer

        # Take the top N most relevant and unique sentences to form the answer.
        # Limiting to 3 sentences to keep the answer concise.
        for score, sentence_text in relevant_sentences:
            cleaned_sentence = sentence_text.strip()
            if cleaned_sentence and cleaned_sentence not in seen_sentences:
                answer_parts.append(cleaned_sentence)
                seen_sentences.add(cleaned_sentence)
            if len(answer_parts) >= 3: # Stop after collecting the top 3 unique sentences
                break

        final_answer = " ".join(answer_parts).strip()

        # Ensure the final answer ends with a punctuation mark if it's a statement
        if final_answer and not final_answer.endswith(('.', '?', '!')):
            final_answer += "."
        return final_answer
    else:
        # Fallback response if no relevant information is found in the knowledge base
        return "I apologize, but I couldn't find a direct answer to your question in our knowledge base. Please try rephrasing your question or visit our website for more information."