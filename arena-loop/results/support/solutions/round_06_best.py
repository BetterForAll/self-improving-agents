def _extract_query_terms(q: str) -> list[str]:
    """
    Extracts key terms from a question.
    This is a placeholder for more sophisticated NLP techniques (e.g., tokenization,
    stemming/lemmatization, named entity recognition, part-of-speech tagging).
    """
    stop_words = {"a", "an", "the", "is", "are", "what", "how", "can", "i", "my", "about", "for", "of", "do", "you", "and", "or", "in", "on", "at", "to", "from", "with"}

    def _clean_word(word: str) -> str:
        """Helper to clean a single word by removing non-alphanumeric chars and lowercasing."""
        return "".join(filter(str.isalnum, word)).lower()

    # Split, convert to lowercase, filter out stop words and short words, and remove non-alphanumeric.
    processed_words = [_clean_word(word) for word in q.split()]
    terms = [
        word for word in processed_words
        if word not in stop_words and len(word) > 2
    ]
    return list(set(terms))  # Return unique terms

def _find_relevant_information(terms: list[str], kb: str) -> list[str]:
    """
    Finds passages in the knowledge base that are relevant to the query terms.
    This version improves sentence splitting heuristics and uses whole-word matching
    for better relevance without external NLP libraries.
    This is a placeholder for advanced retrieval mechanisms (e.g., inverted index search,
    semantic search with embeddings, document chunking).
    """
    import re # Import re here as it's only used in this function.

    relevant_snippets = []
    
    # Pre-process knowledge base to normalize sentence endings for more consistent splitting.
    # Ensure one space after punctuation and clean up multiple spaces.
    processed_kb = kb.replace('\n', ' ')
    # Replace common terminators with themselves followed by a single space to standardize
    processed_kb = re.sub(r'([.?!])\s*', r'\1 ', processed_kb)
    # Remove any excess whitespace (multiple spaces, leading/trailing)
    processed_kb = re.sub(r'\s{2,}', ' ', processed_kb).strip()

    # Split into sentences using a regex that handles common terminators.
    # This pattern splits on periods, question marks, or exclamation marks followed by a space.
    # Uses a positive lookbehind to keep the terminator with the sentence, then strips.
    sentences = re.split(r'(?<=[.?!])\s+', processed_kb)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Prepare regex patterns for whole-word matching to avoid partial matches (e.g., 'car' in 'carpet').
    # Using re.escape to handle special characters in terms correctly.
    term_patterns = [re.compile(r'\b' + re.escape(term) + r'\b') for term in terms]

    for sentence in sentences:
        sentence_lower = sentence.lower()
        # Check for whole word term presence using pre-compiled regex patterns
        if any(pattern.search(sentence_lower) for pattern in term_patterns):
            relevant_snippets.append(sentence) # Append the original sentence text
    return relevant_snippets

def _synthesize_answer(info: list[str], original_q: str) -> str:
    """
    Synthesizes a coherent, human-readable answer from the relevant information.
    This is a placeholder for sophisticated answer generation (e.g., summarization,
    fact extraction, integration with large language models).
    """
    if not info:
        return "I'm sorry, I couldn't find specific information regarding your question in our knowledge base. Please try rephrasing or visit our website for more details."
    
    # Basic example: concatenate relevant snippets
    if len(info) == 1:
        return f"According to our knowledge base: {info[0]}."
    else:
        response_parts = [f"Here's what I found related to your question '{original_q}':"]
        for i, passage in enumerate(info):
            response_parts.append(f"- {passage}")
        response_parts.append("Please let us know if you need more specific details.")
        return "\n".join(response_parts).strip()


def answer_question(question: str, knowledge_base: str) -> str:
    """Answer a customer question using the knowledge base.

    This version refactors the question answering process into
    smaller, well-named, module-level helper functions for improved
    readability, maintainability, extensibility, and crucially,
    independent testability and reusability. Each helper encapsulates
    a specific stage of the Q&A process, making the main function
    easier to understand and debug.

    The internal logic of `_extract_query_terms` and
    `_find_relevant_information` incorporates the specified improvements
    from previous iterations, such as cleaner word processing and
    enhanced sentence splitting with whole-word regex matching for
    more precise retrieval.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    # Step 1: Process the question to identify key terms or intent
    # This separates the concern of understanding the question.
    query_terms = _extract_query_terms(question)

    # Step 2: Retrieve relevant information from the knowledge base
    # This isolates the search/retrieval mechanism.
    relevant_information = _find_relevant_information(query_terms, knowledge_base)

    # Step 3: Synthesize a coherent answer from the retrieved information
    # This focuses on formulating the final user-facing response.
    answer = _synthesize_answer(relevant_information, question)

    return answer