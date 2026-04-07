import re

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This improved version uses keyword matching to find relevant sentences in the
    knowledge base and constructs an answer from them. It enhances preprocessing,
    refines the relevance scoring, and improves answer construction for clearer results.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    # Helper function to convert text to lowercase and remove most punctuation,
    # keeping alphanumeric characters. This ensures consistent keyword matching.
    def preprocess_text(text):
        text = text.lower()
        # Remove all non-alphanumeric characters (except spaces) for simplified matching.
        # This treats "Wi-Fi" and "wifi" as the same, and "anti-theft" and "antitheft" similarly.
        text = re.sub(r'[^\w\s]', '', text)
        return text

    # 1. Preprocessing and Keyword Extraction from the question
    processed_question = preprocess_text(question)
    # Convert to a set for faster lookup and to remove duplicate words
    question_words = set(processed_question.split())

    # A more comprehensive list of common English stop words to filter out less meaningful words.
    # Added common interrogative words and general question-related terms.
    stop_words = set([
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having",
        "and", "or", "but", "if", "then", "else", "when", "where", "why", "how", "what", "which", "who", "whom",
        "for", "at", "by", "from", "in", "on", "out", "over", "under", "up", "down", "to", "of", "with",
        "about", "above", "below", "before", "after", "through", "again", "further", "once", "here", "there",
        "this", "that", "these", "those", "am", "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
        "you", "your", "yours", "yourself", "he", "him", "his", "himself", "she", "her", "hers", "herself",
        "it", "its", "itself", "they", "them", "their", "theirs", "themselves", "do", "does", "did", "doing",
        "will", "would", "can", "could", "should", "may", "might", "must", "say", "said", "get", "got",
        "please", "thank", "could", "help", "me", "know", "want", "tell", "can", "i", "get", "info", "information",
        "about", "regarding", "concerning", "find", "out", "more", "tellme"
    ])

    # Filter out stop words and single-letter words from the question to get meaningful keywords.
    # We prioritize keywords that are longer than 1 character.
    keywords = {word for word in question_words if word not in stop_words and len(word) > 1}

    # Fallback 1: If all potential keywords were stop words or too short,
    # use all original non-empty question words as a fallback to avoid an empty keyword set.
    if not keywords and question_words:
        keywords = question_words
    # Fallback 2: If question_words itself was empty after processing (e.g., empty string question)
    elif not keywords:
        return "I apologize, but I couldn't understand your question. Please provide more details."

    # If keywords are still empty at this stage, it means even the fallback didn't yield useful terms.
    if not keywords:
        return "I apologize, but I couldn't extract enough meaningful keywords from your question. Please try rephrasing."


    # 2. Split knowledge_base into sentences
    # A robust regex for splitting text into sentences.
    # It handles common sentence endings (., ?, !) and tries to avoid splitting on abbreviations or decimal points.
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', knowledge_base)

    relevant_sentences = []
    # Score each sentence based on keyword overlap and density with the question
    for sentence_original in sentences:
        if not sentence_original.strip(): # Skip empty or whitespace-only sentences
            continue

        processed_sentence = preprocess_text(sentence_original)
        sentence_words = set(processed_sentence.split())

        # Calculate the number of overlapping keywords between the question and the sentence
        common_words_count = len(keywords.intersection(sentence_words))

        # Improved Scoring Mechanism:
        # A sentence is considered relevant if it shares at least one keyword.
        # The score is a combination of:
        # 1. Base count of common keywords.
        # 2. Bonus for keyword density within the sentence (more keywords in a shorter sentence is better).
        # 3. Bonus for coverage of the question's unique keywords (how many distinct question keywords appear).
        score = 0
        if common_words_count > 0:
            score = common_words_count  # Base score from common keywords

            # Add bonus for keyword density in the sentence.
            # Avoid division by zero: if common_words_count > 0, sentence_words cannot be empty.
            score += common_words_count / len(sentence_words)

            # Add bonus for covering a higher proportion of the original question's keywords.
            # `len(keywords)` is guaranteed to be > 0 at this point.
            score += common_words_count / len(keywords)

            # Store the relevance score and the original sentence (stripped for cleanliness)
            relevant_sentences.append((score, sentence_original.strip()))

    # Sort sentences by their relevance score in descending order
    relevant_sentences.sort(key=lambda x: x[0], reverse=True)

    # 3. Construct the answer from the most relevant sentences
    if relevant_sentences:
        answer_parts = []
        seen_sentences = set() # Use a set to prevent adding exact duplicate sentences to the answer

        # Define the maximum number of unique, relevant sentences to include in the answer for conciseness.
        max_sentences_in_answer = 3

        for score, sentence_text in relevant_sentences:
            cleaned_sentence = sentence_text.strip()
            # Ensure the sentence is not empty and hasn't been added before
            if cleaned_sentence and cleaned_sentence not in seen_sentences:
                answer_parts.append(cleaned_sentence)
                seen_sentences.add(cleaned_sentence)
            if len(answer_parts) >= max_sentences_in_answer:
                break

        final_answer = ""
        if answer_parts:
            # Add an introductory phrase to make the answer more natural and helpful
            intro_phrase = "Here is what I found regarding your question: "
            final_answer = intro_phrase + " ".join(answer_parts)

            # Ensure the final answer ends with a punctuation mark if it's a statement
            if final_answer and not final_answer.endswith(('.', '?', '!')):
                final_answer += "."
            return final_answer
        else:
            # Fallback if relevant_sentences had entries, but all selected sentences were empty after strip
            # or were duplicates that prevented reaching max_sentences_in_answer with unique content.
            return "I apologize, but I couldn't find a direct answer to your question in our knowledge base. Please try rephrasing your question or visit our website for more information."
    else:
        # Fallback response if no relevant information is found in the knowledge base at all
        return "I apologize, but I couldn't find a direct answer to your question in our knowledge base. Please try rephrasing your question or visit our website for more information."