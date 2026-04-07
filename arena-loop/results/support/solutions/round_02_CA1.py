def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    This function orchestrates a multi-step process to generate a supported answer,
    delegating specific tasks to well-defined helper functions.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """
    # Helper functions (_analyze_question, _retrieve_relevant_sections,
    # _generate_draft_answer, _assess_answer_support, _format_final_answer)
    # are assumed to be defined elsewhere in the module or class.

    # 1. Analyze the question to understand user intent and extract key entities/keywords.
    # This step typically involves Natural Language Processing (NLP) techniques.
    question_analysis = _analyze_question(question)

    # 2. Retrieve relevant sections or snippets from the knowledge base.
    # This helper function would use the question analysis to perform a targeted search
    # or semantic retrieval from the provided knowledge base.
    relevant_sections = _retrieve_relevant_sections(question_analysis, knowledge_base)

    # 3. Generate a preliminary or 'draft' answer based on the retrieved information.
    # This step synthesizes the content of the relevant sections into a coherent response
    # to the original question, potentially using a language model.
    draft_answer = _generate_draft_answer(relevant_sections, question)

    # 4. Assess how well the draft answer is supported by the retrieved knowledge.
    # This is the core 'support' calculation step, evaluating factual consistency, completeness,
    # and confidence based on the provided source materials. It might return a score and/or specific supporting facts.
    support_score, supporting_facts = _assess_answer_support(draft_answer, relevant_sections)

    # 5. Format the final answer for presentation to the user.
    # This step refines the draft, potentially incorporates the support score or references,
    # and ensures the answer is user-friendly and complete.
    final_answer = _format_final_answer(draft_answer, support_score, supporting_facts)

    return final_answer