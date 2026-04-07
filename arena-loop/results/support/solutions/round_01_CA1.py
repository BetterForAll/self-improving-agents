def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This function orchestrates the process of answering a question by
    preprocessing the question, retrieving relevant supporting information
    from the knowledge base, and then synthesizing an answer based on that support.
    It leverages several helper functions to break down the complex task
    into smaller, manageable, and testable logical steps.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    processed_question = _preprocess_question(question)
    supporting_evidence = _retrieve_supporting_evidence(processed_question, knowledge_base)

    if not supporting_evidence:
        return _get_fallback_response()

    final_answer = _synthesize_answer_from_support(processed_question, supporting_evidence)
    return final_answer


def _preprocess_question(question: str) -> str:
    """Preprocesses the customer's question for better retrieval or understanding.

    This might include cleaning, tokenization, lowercasing, or converting to an embedding.
    For now, it returns the question after basic stripping.

    Args:
        question: The raw customer question.

    Returns:
        The processed question.
    """
    # Placeholder for actual preprocessing logic
    return question.strip()


def _retrieve_supporting_evidence(processed_question: str, knowledge_base: str) -> list[str]:
    """Retrieves relevant passages or documents from the knowledge base that support the question.

    This is a critical step for "calculating support". It would typically involve
    search algorithms (e.g., keyword matching, semantic search using embeddings)
    to find chunks of the knowledge base that are most relevant to the processed question.
    For this improved version, it simulates finding specific support based on keywords.

    Args:
        processed_question: The question after preprocessing.
        knowledge_base: The entire product information text.

    Returns:
        A list of strings, where each string is a piece of supporting evidence
        (e.g., a relevant paragraph or document chunk). Returns an empty list
        if no relevant support is found to trigger the fallback.
    """
    # In a real implementation, this would involve complex logic:
    # 1. Chunking the knowledge_base
    # 2. Indexing chunks (e.g., with a vector database)
    # 3. Performing a similarity search using the processed_question
    # 4. Filtering and ranking the top-k relevant chunks

    # --- SIMULATION for demonstrating structure ---
    lower_question = processed_question.lower()
    relevant_chunks = []

    # Example: If question mentions "website" or "support", find related info.
    if "website" in lower_question or "info" in lower_question or "more information" in lower_question:
        if "example.com/support" in knowledge_base: # Simulate finding specific URL
            relevant_chunks.append("Our official website is example.com/support, where you can find detailed FAQs and product manuals.")
        elif "contact us" in knowledge_base:
            relevant_chunks.append("For more information, please visit our website's contact us page.")
        else: # General website information if not specific
            relevant_chunks.append("Please visit our main website for comprehensive product details and support resources.")
            
    # If specific support wasn't found based on the simple simulation, return nothing
    # so the fallback response is triggered.
    return relevant_chunks


def _synthesize_answer_from_support(question: str, supporting_evidence: list[str]) -> str:
    """Synthesizes a coherent answer based on the original question and retrieved supporting evidence.

    This step typically involves a generation model (e.g., an LLM) or rule-based
    extraction and summarization to formulate a concise and relevant answer from
    the provided support.

    Args:
        question: The original customer question.
        supporting_evidence: A list of relevant knowledge base passages.

    Returns:
        A synthesized answer string.
    """
    # Placeholder for actual answer generation logic (e.g., LLM prompting and response parsing)
    if supporting_evidence:
        # A very basic synthesis: combine the support into a user-friendly message.
        # In a real system, an LLM would read the support and the question to generate a precise answer.
        combined_support_text = "\n".join(supporting_evidence)
        return f"Regarding your question about '{question}', we found the following information: {combined_support_text}"
    else:
        # This branch should ideally not be reached if `_get_fallback_response`
        # is called when no support is found. Included for completeness.
        return "We couldn't generate a specific answer from the available context."


def _get_fallback_response() -> str:
    """Returns a generic fallback response when specific support cannot be found."""
    return "Thank you for contacting us. Please visit our website for more information."