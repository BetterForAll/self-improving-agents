import re
import string

def answer_question(question, knowledge_base):
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
        Enhancements include stripping punctuation and using a more comprehensive stop word list.
        """
        # Using frozenset for immutable and slightly faster lookup of stop words.
        stop_words = frozenset({
            "a", "an", "the", "is", "are", "what", "how", "can", "i", "my", "about",
            "for", "of", "do", "you", "does", "which", "where", "when", "please",
            "could", "would", "should", "will", "may", "might", "your", "its"
        })
        
        cleaned_words = []
        # Process each word: strip punctuation, lowercase, and filter based on stop words and length.
        for word in q.split():
            cleaned_word = word.strip(string.punctuation).lower()
            if cleaned_word and cleaned_word not in stop_words and len(cleaned_word) > 2:
                cleaned_words.append(cleaned_word)
        # Return unique, sorted terms for consistency and predictability.
        return sorted(list(set(cleaned_words)))

    def _find_relevant_information(terms: list[str], kb: str) -> list[str]:
        """
        Finds passages in the knowledge base that are relevant to the query terms.
        This is a placeholder for advanced retrieval mechanisms (e.g., inverted index search,
        semantic search with embeddings, document chunking).
        The sentence splitting is made more robust to handle various punctuation and abbreviations.
        """
        relevant_snippets = []
        
        # Robust sentence splitting using regex, handling common terminators and abbreviations.
        # This regex splits on periods, question marks, or exclamation points followed by whitespace,
        # but avoids splitting after single uppercase letters (initials) or common abbreviations.
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s+', kb.replace('\n', ' '))
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            # If any extracted term is found in the lowercased sentence, consider it relevant.
            if any(term in sentence_lower for term in terms):
                relevant_snippets.append(sentence.strip())
        return relevant_snippets

    def _synthesize_answer(info: list[str], original_q: str) -> str:
        """
        Synthesizes a coherent, human-readable answer from the relevant information.
        This is a placeholder for sophisticated answer generation (e.g., summarization,
        fact extraction, integration with large language models).
        Improved formatting ensures consistent punctuation and clearer messaging.
        """
        def _ensure_punctuation(text: str) -> str:
            """Ensures the given text ends with a period if it doesn't already have end punctuation."""
            stripped_text = text.strip()
            if not stripped_text:
                return ""
            if not stripped_text.endswith(('.', '?', '!')):
                return stripped_text + '.'
            return stripped_text

        if not info:
            # More specific fallback message if no info is found.
            return "I couldn't find specific information in our knowledge base that directly addresses your question. Please try rephrasing or search our official documentation for more details."
        
        if len(info) == 1:
            # Format a single relevant snippet as a direct answer with proper punctuation.
            return f"According to our knowledge base: {_ensure_punctuation(info[0])}"
        else:
            # Format multiple snippets as a bulleted list for readability.
            response_parts = [f"Here's what I found that might help with your question, '{original_q}':"]
            for passage in info:
                response_parts.append(f"- {_ensure_punctuation(passage)}")
            response_parts.append("For more specific details or further assistance, please refer to our full documentation or contact support.")
            return "\n".join(response_parts).strip()

    # --- Main logic of the answer_question function ---

    # Step 1: Process the question to identify key terms or intent.
    query_terms = _extract_query_terms(question)

    # Early exit: If no meaningful terms are extracted, return an immediate and informative response.
    if not query_terms:
        return "I'm sorry, I couldn't understand your question. Could you please rephrase it with more specific keywords?"

    # Step 2: Retrieve relevant information from the knowledge base using the extracted terms.
    relevant_information = _find_relevant_information(query_terms, knowledge_base)

    # Step 3: Synthesize a coherent answer from the retrieved information.
    answer = _synthesize_answer(relevant_information, question)

    return answer