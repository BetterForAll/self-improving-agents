def answer_question(question: str, knowledge_base: str) -> str:
    """Answer a customer question using the knowledge base.

    This version refactors the question answering process into
    smaller, well-named helper functions for improved readability,
    maintainability, and extensibility. Each helper encapsulates a
    specific stage of the Q&A process, making the main function
    easier to understand and debug.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    # Helper functions, nested to ensure strict adherence to "Return ONLY the function definition".
    # In a real application, these would typically be module-level private functions.

    def _extract_query_terms(q: str) -> list[str]:
        """
        Extracts key terms from a question.
        This is a placeholder for more sophisticated NLP techniques (e.g., tokenization,
        stemming/lemmatization, named entity recognition, part-of-speech tagging).
        """
        # Basic example: split by spaces, remove common stop words, and lowercase
        stop_words = {"a", "an", "the", "is", "are", "what", "how", "can", "i", "my", "about", "for", "of", "do", "you"}
        terms = [word.lower() for word in q.split() if word.lower() not in stop_words and len(word) > 2]
        return list(set(terms))  # Return unique terms

    def _find_relevant_information(terms: list[str], kb: str) -> list[str]:
        """
        Finds passages in the knowledge base that are relevant to the query terms.
        This is a placeholder for advanced retrieval mechanisms (e.g., inverted index search,
        semantic search with embeddings, document chunking).
        """
        relevant_snippets = []
        # Basic example: split knowledge base into sentences and check for term presence
        # A more robust solution would handle paragraphs, sections, or entire documents.
        sentences = kb.replace('\n', ' ').split('. ')
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(term in sentence_lower for term in terms):
                relevant_snippets.append(sentence.strip())
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
            response_parts = [f"Here's what I found regarding '{original_q}':"]
            for i, passage in enumerate(info):
                response_parts.append(f"- {passage}")
            response_parts.append("Please let us know if you need more specific details.")
            return "\n".join(response_parts).strip()

    # --- Main logic of the answer_question function ---

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