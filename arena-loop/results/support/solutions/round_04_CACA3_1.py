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
    #    This avoids creating a full list of all sentences in memory.
    def chunk_knowledge_base(kb_text):
        # A basic sentence splitter. In a more sophisticated system,
        # one might use an NLP library (e.g., NLTK, spaCy) for better accuracy.
        # This regex splits by common sentence terminators followed by whitespace,
        # keeping the terminator with the sentence.
        sentences = re.split(r'(?<=[.!?])\s+', kb_text.strip())
        for sentence in sentences:
            if sentence.strip():
                yield sentence.strip()

    # 2. Generator to filter relevant chunks based on question keywords.
    #    This processes chunks from the `chunk_knowledge_base` generator
    #    on-the-fly, yielding only relevant ones without storing all chunks
    #    or all relevant chunks in a temporary list.
    def find_relevant_chunks(chunks_generator, keywords):
        # Improvement: Use whole-word matching for keywords to increase relevance quality.
        # This avoids matching substrings like "car" in "carpet" when "car" is the keyword.
        if not keywords: # If no keywords, no chunk can be considered relevant.
            return

        # Escape keywords to handle potential regex special characters within them,
        # ensuring they are treated as literal strings in the pattern.
        escaped_keywords = [re.escape(keyword) for keyword in keywords]
        
        # Build a regex pattern for whole-word matching (e.g., r'\b(keyword1|keyword2)\b')
        # Compile the pattern once for efficiency during iteration, as it will be reused for each chunk.
        # re.IGNORECASE makes the matching case-insensitive, similar to the original approach.
        keywords_pattern = re.compile(r'\b(' + '|'.join(escaped_keywords) + r')\b', re.IGNORECASE)

        for chunk in chunks_generator:
            # Use re.search() to find the pattern anywhere in the chunk.
            # This is generally more efficient than iterating through `any(keyword in lower_chunk for keyword in keywords)`
            # for multiple keywords, and crucially, it ensures whole-word matching.
            if keywords_pattern.search(chunk):
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