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
        # A basic sentence splitter. In a more sophisticated system,
        # one might use an NLP library (e.g., NLTK, spaCy) for better accuracy.
        # This regex splits by common sentence terminators followed by whitespace,
        # keeping the terminator with the sentence.
        sentences = re.split(r'(?<=[.!?])\s+', kb_text.strip())
        for sentence in sentences:
            if sentence.strip():
                yield sentence.strip()

    # 2. Generator to filter and score relevant chunks based on question keywords.
    #    This processes chunks from the `chunk_knowledge_base` generator
    #    on-the-fly, yielding only relevant ones along with a simple relevance score,
    #    without storing all chunks or all relevant chunks in a temporary list.
    def find_relevant_chunks(chunks_generator, keywords):
        for chunk in chunks_generator:
            # Convert chunk to lowercase once for efficiency when checking multiple keywords.
            lower_chunk = chunk.lower()
            # Calculate a simple relevance score: count of unique keywords found in the chunk.
            score = sum(1 for keyword in keywords if keyword in lower_chunk)
            if score > 0: # Only yield chunks that contain at least one question keyword.
                yield (score, chunk) # Yield a tuple of (relevance_score, chunk_text)

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
    # Then, get a generator for relevant chunks (with scores) from the kb_chunks_gen.
    relevant_chunks_scored_gen = find_relevant_chunks(kb_chunks_gen, question_keywords)

    # Collect a limited number of the most relevant chunks using a min-heap (priority queue).
    # This ensures only the top N chunks (by score) are kept in memory, regardless
    # of how many total relevant chunks are generated, significantly optimizing memory footprint.
    max_relevant_chunks_to_collect = 5
    # The heap stores (score, chunk) tuples. heapq is a min-heap, so it always
    # keeps the smallest element at index 0. To get the N highest scores,
    # we push items onto the heap and remove the smallest if the heap grows too large.
    top_n_chunks_heap = [] # stores (score, chunk) tuples

    for score, chunk in relevant_chunks_scored_gen:
        if len(top_n_chunks_heap) < max_relevant_chunks_to_collect:
            heapq.heappush(top_n_chunks_heap, (score, chunk))
        elif score > top_n_chunks_heap[0][0]: # If current chunk's score is higher than the lowest in the heap
            heapq.heapreplace(top_n_chunks_heap, (score, chunk)) # Replace the lowest with the new one

    # Extract chunks from the heap. Sort them by score in descending order
    # to present the most relevant information first in the final answer.
    collected_answers_with_scores = sorted(top_n_chunks_heap, key=lambda x: x[0], reverse=True)
    collected_answers = [chunk for score, chunk in collected_answers_with_scores]

    if collected_answers:
        # Join the collected relevant chunks to form the final answer.
        return " ".join(collected_answers)
    else:
        # Fallback response if no relevant information is found.
        return "I apologize, but I couldn't find specific information related to your question in our knowledge base. Please try rephrasing your question or visit our website for more details."