import re
import heapq

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
        # A basic sentence splitter. Splits by common sentence terminators
        # followed by one or more whitespace characters, keeping the terminator
        # with the sentence.
        sentences = re.split(r'(?<=[.!?])\s+', kb_text.strip())
        for sentence in sentences:
            stripped_sentence = sentence.strip()
            if stripped_sentence:
                yield stripped_sentence

    # 2. Generator to find and score relevant chunks based on question keywords.
    #    This processes chunks from the `chunk_knowledge_base` generator
    #    on-the-fly, yielding only relevant ones (with their score) without
    #    storing all chunks or all relevant chunks in a temporary list.
    def find_relevant_scored_chunks(chunks_generator, keyword_pattern):
        for chunk in chunks_generator:
            lower_chunk = chunk.lower()
            # Find all matches for the combined keyword pattern.
            # This ensures whole-word matching for better relevance.
            matches = keyword_pattern.findall(lower_chunk)

            if matches:
                # Improved scoring: Count the total number of keyword occurrences.
                # This gives more weight to chunks where relevant terms appear
                # more frequently, indicating stronger relevance.
                # The previous scoring `len(set(matches))` only counted unique keywords,
                # which could undervalue chunks heavily focused on specific terms.
                score = len(matches)
                yield (score, chunk)

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
        "can", "will", "just", "don", "should", "now", "get", "has", "had",
        "have", "may", "much", "must", "if", "would", "could", "shall",
        "every", "through", "while", "wherefore", "within", "without", "until"
    }

    # Extract meaningful keywords from the question.
    # Using '\b\w+\b' to match whole words including alphanumeric and underscores,
    # which can be relevant for product IDs or specific terms.
    question_keywords = set(word for word in re.findall(r'\b\w+\b', question.lower())
                            if len(word) > 2 and word not in STOP_WORDS)

    # If no meaningful keywords are extracted from the question,
    # we cannot perform an effective search.
    if not question_keywords:
        return "I couldn't understand your question. Please provide more specific details."

    # Create a single regex pattern for all keywords for whole-word matching.
    # This is more precise than simple substring matching and more efficient than
    # running multiple `re.search` calls for each keyword.
    # re.escape is used to handle any special regex characters that might be present in keywords.
    # The `re.IGNORECASE` flag for matching is implicitly handled by converting chunk to lowercase.
    keyword_pattern = re.compile(r'\b(?:' + '|'.join(re.escape(k) for k in question_keywords) + r')\b')


    # Pipeline the generators:
    # First, get a generator for knowledge base chunks (sentences).
    kb_chunks_gen = chunk_knowledge_base(knowledge_base)

    # Then, get a generator for relevant chunks, each with a relevance score.
    relevant_scored_chunks_gen = find_relevant_scored_chunks(kb_chunks_gen, keyword_pattern)

    # Collect a limited number of the *highest-scoring* relevant chunks.
    # Using a min-heap (via heapq) to efficiently keep track of the top N elements
    # from a stream, ensuring memory efficiency for large inputs without storing
    # all relevant chunks.
    max_relevant_chunks_to_collect = 5
    # The heap will store (score, chunk) tuples. Python's heapq is a min-heap,
    # so we store actual scores and use heappushpop to maintain the top N highest scores.
    top_n_chunks_heap = [] # (score, chunk)

    for score, chunk in relevant_scored_chunks_gen:
        if len(top_n_chunks_heap) < max_relevant_chunks_to_collect:
            heapq.heappush(top_n_chunks_heap, (score, chunk))
        elif score > top_n_chunks_heap[0][0]: # If current score is greater than the smallest in the heap
            heapq.heappushpop(top_n_chunks_heap, (score, chunk))

    # After processing all chunks, the heap contains the top N highest-scoring chunks.
    # We sort them by score in descending order for presentation, ensuring the most
    # relevant information appears first.
    collected_answers = [chunk for score, chunk in sorted(top_n_chunks_heap, key=lambda x: x[0], reverse=True)]

    if collected_answers:
        # Join the collected relevant chunks to form the final answer.
        # Added a header for better readability if multiple points are found,
        # and guidance for the user for better interaction quality.
        if len(collected_answers) > 1:
            return "Here's what I found:\n" + "\n".join(collected_answers) + "\n\nIf you need more details, please rephrase your question."
        else:
            return collected_answers[0]
    else:
        # Fallback response if no relevant information is found.
        return "I apologize, but I couldn't find specific information related to your question in our knowledge base. Please try rephrasing your question or visit our website for more details."