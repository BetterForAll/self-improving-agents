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
    # handling potentially large knowledge bases.
    # Additionally, improve the 'quality_score' by implementing a simple relevance
    # scoring mechanism and collecting the most relevant chunks using a min-heap,
    # ensuring the answer is composed of the best matching information.

    # 1. Generator to chunk the knowledge base into sentences.
    #    This avoids creating a full list of all sentences in memory.
    def chunk_knowledge_base(kb_text):
        # A basic sentence splitter. This regex splits by common sentence terminators
        # followed by whitespace, keeping the terminator with the sentence.
        # .strip() handles leading/trailing whitespace for the whole KB text.
        sentences = re.split(r'(?<=[.!?])\s+', kb_text.strip())
        for sentence in sentences:
            stripped_sentence = sentence.strip()
            if stripped_sentence:  # Ensure we don't yield empty strings
                yield stripped_sentence

    # 2. Generator to filter and score relevant chunks based on question keywords.
    #    This processes chunks from the `chunk_knowledge_base` generator on-the-fly,
    #    yielding only relevant ones along with a relevance score. This improves
    #    answer quality by allowing us to select the most pertinent information.
    def find_relevant_chunks_with_scores(chunks_generator, keywords):
        for chunk in chunks_generator:
            # Convert chunk to lowercase once for efficiency when checking multiple keywords.
            lower_chunk = chunk.lower()
            
            # Calculate a simple relevance score: count of unique keywords found in the chunk.
            # This helps prioritize chunks that contain more direct matches to the question.
            found_keywords_count = sum(1 for keyword in keywords if keyword in lower_chunk)

            if found_keywords_count > 0:
                yield chunk, found_keywords_count

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
        "can", "will", "just", "don", "should", "now", "could", "would"
    }

    # Extract keywords from the question, convert to lowercase, filter stop words and short words.
    question_keywords = set(word for word in re.findall(r'\b\w+\b', question.lower())
                            if len(word) > 2 and word not in STOP_WORDS)

    # If no meaningful keywords are extracted from the question,
    # we cannot perform an effective search.
    if not question_keywords:
        return "I couldn't understand your question. Please provide more specific details."

    # Pipeline the generators:
    # First, get a generator for knowledge base chunks (sentences).
    kb_chunks_gen = chunk_knowledge_base(knowledge_base)
    # Then, get a generator for relevant chunks and their calculated scores.
    relevant_chunks_with_scores_gen = find_relevant_chunks_with_scores(kb_chunks_gen, question_keywords)

    # Collect a limited number of the most relevant chunks using a min-heap (heapq).
    # This ensures memory efficiency by only storing up to `max_relevant_chunks_to_collect`
    # items at any given time, regardless of how many total relevant chunks exist.
    max_relevant_chunks_to_collect = 5
    # The heap stores (score, chunk) tuples. `heapq` is a min-heap, so it will keep
    # the 'smallest' scores at the top. We use this property to maintain the N largest scores seen so far.
    top_chunks_heap = []  # Stores (score, chunk)

    for chunk, score in relevant_chunks_with_scores_gen:
        if len(top_chunks_heap) < max_relevant_chunks_to_collect:
            heapq.heappush(top_chunks_heap, (score, chunk))
        else:
            # If the current chunk's score is higher than the lowest score currently in the heap,
            # replace the lowest-scoring chunk with the current one.
            if score > top_chunks_heap[0][0]:
                heapq.heapreplace(top_chunks_heap, (score, chunk))

    # Extract the chunks from the heap.
    # Sort them by score in descending order to present the most relevant first.
    collected_answers = [chunk for score, chunk in sorted(top_chunks_heap, key=lambda x: x[0], reverse=True)]

    if collected_answers:
        # Join the collected relevant chunks to form the final answer.
        return " ".join(collected_answers)
    else:
        # Fallback response if no relevant information is found.
        return "I apologize, but I couldn't find specific information related to your question in our knowledge base. Please try rephrasing your question or visit our website for more details."