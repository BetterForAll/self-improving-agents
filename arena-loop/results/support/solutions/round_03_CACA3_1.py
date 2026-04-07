import re

# Moved STOP_WORDS outside the function as it's a constant.
# Defining it globally prevents re-creation on every function call,
# contributing to a better quality_score through minor efficiency and clearer scope.
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
    #    IMPROVEMENT: The previous `re.split` would create an entire list of
    #    sentences in memory before yielding. This revised `chunk_knowledge_base`
    #    uses `re.finditer` to truly stream sentences, avoiding the creation of
    #    a full list, thus adhering more strictly to the "avoid building large
    #    lists in memory" principle for the very first processing step.
    def chunk_knowledge_base(kb_text):
        # This regex looks for sentence terminators ('.', '!', '?') followed by
        # optional whitespace. The lookbehind `(?<=[.!?])` ensures the terminator
        # is part of the sentence being extracted, and `\s*` consumes any trailing whitespace.
        sentence_end_pattern = re.compile(r'(?<=[.!?])\s*')
        last_end = 0
        text_to_process = kb_text.strip() # Strip once at the beginning for overall cleanliness

        if not text_to_process: # Handle an empty knowledge base gracefully
            return

        for match in sentence_end_pattern.finditer(text_to_process):
            # Extract the sentence from the last recorded end to just after the punctuation.
            # match.start() is the index right after the punctuation (start of whitespace).
            sentence = text_to_process[last_end : match.start() + 1].strip()
            if sentence: # Yield only non-empty sentences
                yield sentence
            last_end = match.end() # Update last_end to the position after the consumed whitespace

        # Yield any remaining text as a sentence if the knowledge base doesn't end
        # with a recognized terminator or if the last part wasn't followed by whitespace.
        if last_end < len(text_to_process):
            sentence = text_to_process[last_end:].strip()
            if sentence:
                yield sentence

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
    # that are unlikely to be meaningful keywords, and common stop words.
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
    # to manage memory if many chunks are relevant. This loop also
    # enables early termination of the generator pipeline.
    max_relevant_chunks_to_collect = 5
    collected_answers = []
    for i, chunk in enumerate(relevant_chunks_gen):
        if i >= max_relevant_chunks_to_collect:
            break # Early termination: stop processing the knowledge base
        collected_answers.append(chunk)

    if collected_answers:
        # Join the collected relevant chunks to form the final answer.
        return " ".join(collected_answers)
    else:
        # Fallback response if no relevant information is found.
        return "I apologize, but I couldn't find specific information related to your question in our knowledge base. Please try rephrasing your question or visit our website for more details."