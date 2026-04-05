def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This version refactors the question answering process into
    smaller, well-named helper functions for improved readability,
    maintainability, and extensibility. Each helper encapsulates a
    specific stage of the Q&A process, making the main function
    easier to understand and debug.

    This improved version further refactors complex logic within the
    _find_relevant_information helper into even smaller, dedicated
    sub-helper functions, enhancing clarity and modularity at a deeper level.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    # Helper functions, nested to ensure strict adherence to "Return ONLY the function definition".
    # In a real application, these would typically be module-level private functions.
    import re

    def _extract_query_terms(q: str) -> list[str]:
        """
        Extracts key terms from a question.
        This is a placeholder for more sophisticated NLP techniques (e.g., tokenization,
        stemming/lemmatization, named entity recognition, part-of-speech tagging).
        """
        # Using frozenset for immutability and slight performance gain on lookups
        stop_words = frozenset({"a", "an", "the", "is", "are", "what", "how", "can", "i", "my", "about", "for", "of", "do", "you", "and", "or", "in", "on", "at", "to", "from", "with"})
        
        terms = []
        for word in q.split():
            # Clean the word by keeping only alphanumeric characters and converting to lowercase
            cleaned_word = "".join(filter(str.isalnum, word)).lower()
            # Filter out empty strings, stop words, and short words (length < 3)
            if cleaned_word and cleaned_word not in stop_words and len(cleaned_word) > 2:
                terms.append(cleaned_word)
        return list(set(terms))  # Return unique terms

    def _find_relevant_information(terms: list[str], kb: str) -> list[str]:
        """
        Finds passages in the knowledge base that are relevant to the query terms.
        This version refactors the internal logic into sub-helpers for even better clarity and maintainability.
        This is a placeholder for advanced retrieval mechanisms (e.g., inverted index search,
        semantic search with embeddings, document chunking).
        """
        
        def _preprocess_and_split_sentences(text: str) -> list[str]:
            """
            Preprocesses the text for consistent sentence splitting and then splits it.
            This separates the concerns of text normalization and actual splitting.
            """
            # Replace newlines with spaces, and normalize various sentence terminators.
            processed_text = text.replace('\n', ' ')
            processed_text = processed_text.replace('?', '. ').replace('!', '. ')
            
            # Ensure the knowledge base ends with a period to catch the last sentence
            if processed_text.strip() and not processed_text.strip().endswith('.'):
                processed_text += '.'
                
            # Replace multiple spaces with a single space to clean up artifacts from replacements
            processed_text = ' '.join(processed_text.split()) 
            
            # Split into sentences using regex to keep punctuation and handle variable spacing
            # (?<=\.) ensures the split occurs after a period, but the period is part of the match.
            sentences = [s.strip() for s in re.split(r'(?<=\.)\s+', processed_text) if s.strip()]
            return sentences

        def _filter_sentences_by_terms(sentences: list[str], query_terms: list[str]) -> list[str]:
            """
            Filters a list of sentences, returning only those containing any of the query terms.
            This separates the concern of matching terms to sentences.
            """
            relevant_snippets = []
            for sentence in sentences:
                sentence_lower = sentence.lower()
                # Basic check for term presence (substring match)
                if any(term in sentence_lower for term in query_terms):
                    relevant_snippets.append(sentence) # Append the original sentence text
            return relevant_snippets

        # --- Main logic of _find_relevant_information function ---
        sentences = _preprocess_and_split_sentences(kb)
        relevant_information = _filter_sentences_by_terms(sentences, terms)
        return relevant_information

    def _synthesize_answer(info: list[str], original_q: str) -> str:
        """
        Synthesizes a coherent, human-readable answer from the relevant information.
        This is a placeholder for sophisticated answer generation (e.g., summarization,
        fact extraction, integration with large language models).
        """
        if not info:
            return "I'm sorry, I couldn't find specific information regarding your question in our knowledge base. Please try rephrasing or visit our website for more details."
        
        # If there's only one relevant snippet, provide a direct answer.
        if len(info) == 1:
            return f"According to our knowledge base: {info[0]}"
        else:
            # For multiple snippets, provide a synthesized summary by joining them.
            response_parts = [f"Regarding your question '{original_q}', here's what our knowledge base suggests:"]
            # Join snippets with a space to form a more continuous paragraph.
            joined_snippets = " ".join(info)
            response_parts.append(joined_snippets)
            response_parts.append("For more specific details, please refer to the relevant sections or contact support.")
            return " ".join(response_parts).strip()

    # --- Main logic of the answer_question function ---
    # This remains a clean pipeline of distinct, reusable steps.

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