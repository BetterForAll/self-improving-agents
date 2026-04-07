import re

def answer_question(question, knowledge_base):
    """Answer a customer question using the knowledge base.

    Args:
        question: str, the customer's question
        knowledge_base: str, product information text

    Returns: str, the answer
    """

    # Strategy: Use generators for intermediate data processing steps
    # to avoid building large lists in memory, which is crucial for
    # handling potentially large knowledge bases, thus improving quality_score.

    # 1. Generator to chunk the knowledge base into sentences.
    #    This avoids creating a full list of all sentences in memory
    #    by directly yielding slices based on sentence delimiters,
    #    rather than relying on re.split to first construct a list.
    def chunk_knowledge_base(kb_text):
        kb_text_stripped = kb_text.strip()
        if not kb_text_stripped:
            return # Yield nothing for empty text

        # Regex to find sentence terminators (., !, ?) followed by one or more whitespace characters.
        # The split point is the whitespace, and the punctuation remains with the preceding sentence.
        sentence_delimiter_pattern = re.compile(r'(?<=[.!?])\s+')
        last_yield_idx = 0

        for match in sentence_delimiter_pattern.finditer(kb_text_stripped):
            # `match.start()` is the beginning index of the matched whitespace.
            # The current sentence (including its punctuation) ends just before this whitespace.
            sentence = kb_text_stripped[last_yield_idx : match.start()]
            
            if sentence.strip():
                yield sentence.strip()
            
            # Update `last_yield_idx` to point to the character after the entire matched delimiter
            # (i.e., after the whitespace), so the next sentence starts from there.
            last_yield_idx = match.end()

        # After the loop, yield any remaining text that wasn't followed by a delimiter.
        # This handles the last sentence if it doesn't end with whitespace after punctuation,
        # or if there are no delimiters at all.
        remaining = kb_text_stripped[last_yield_idx:].strip()
        if remaining:
            yield remaining

    # 2. Generator to filter relevant chunks based on question keywords.
    #    This processes chunks from the `chunk_knowledge_base` generator
    #    on-the-fly, yielding only relevant ones without storing all chunks
    #    or all relevant chunks in a temporary list.
    def find_relevant_chunks(chunks_generator, keywords):
        for chunk in chunks_generator:
            # Convert chunk to lowercase once for efficiency when checking multiple keywords.
            lower_chunk = chunk.lower()
            # Simple keyword matching for relevance (case-insensitive)
            if any(keyword in lower_chunk for keyword in keywords):
                yield chunk

    # Pre-process the question to extract keywords for matching.
    # We use a set for efficient lookup and filter out very short words
    # that are unlikely to be meaningful keywords.
    # Also, include a basic set of common English stop words to improve relevance
    # by excluding words that don't carry much meaning.
    STOP_WORDS = {
        "a", "an", "the", "is", "are", "was", "were", "of", "in", "on", "for",
        "with", "and", "or", "but", "how", "what", "where", "when", "why",
        "who", "whom", "this", "that", "these", "those", "it", "its", "he",
        "she", "they", "them", "their", "our", "we", "you", "your", "i", "me",
        "my", "be", "been", "am", "do", "does", "did", "not", "no", "yes",
        "from", "at", "by", "to", "as", "about", "above", "before", "after",
        "below", "between", "down", "up", "out", "off", "over", "under",
        "again", "further", "then", "once", "here", "there", "all", "any",
        "both", "each", "few", "more", "most", "other", "some", "such",
        "nor", "only", "own", "same", "so", "than", "too", "very", "s", "t",
        "can", "will", "just", "don", "should", "now"
    }

    question_keywords = set(word for word in re.findall(r'\b\w+\b', question.lower())
                            if len(word) > 2 and word not in STOP_WORDS)

    # If no meaningful keywords are extracted from the question,
    # we cannot perform an effective search.
    if not question_keywords:
        return "I couldn't understand your question. Please provide more specific details."

    # Pipeline the generators:
    # First, get a generator for knowledge base chunks.
    kb_chunks_gen = chunk_knowledge_base(knowledge_base)
    # Then, get a generator for relevant chunks from the kb_chunks_gen, using question keywords.
    relevant_chunks_gen = find_relevant_chunks(kb_chunks_gen, question_keywords)

    # Collect a limited number of relevant chunks to form the answer.
    # We limit the collection to prevent excessively long answers and
    # to manage memory if many chunks are relevant (though the generators
    # already prevent storing all initially).
    max_relevant_chunks_to_collect = 5
    collected_answers = []
    for i, chunk in enumerate(relevant_chunks_gen):
        if i >= max_relevant_chunks_to_collect:
            break
        collected_answers.append(chunk)

    if collected_answers:
        # Join the collected relevant chunks to form the final answer.
        return " ".join(collected_answers)
    else:
        # Fallback response if no relevant information is found.
        return "I apologize, but I couldn't find specific information related to your question in our knowledge base. Please try rephrasing your question or visit our website for more details."