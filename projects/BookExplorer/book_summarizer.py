from amp_lib.amp_lib import AmpClient
import uuid
from tqdm import tqdm


class BookProcessor:
    def __init__(
        self,
        chunk_system_prompt: str,
        chunk_prompt: str,
        summary_system_prompt: str = None,
        summary_prompt: str = None,
        base_url: str = "http://localhost:17173",
        chunk_size: int = 30000,
    ):
        self.amp_client = AmpClient(base_url)
        self.chunk_size = chunk_size

        self.chunk_system_prompt = chunk_system_prompt
        self.chunk_prompt = chunk_prompt
        self.summary_system_prompt = summary_system_prompt
        self.summary_prompt = summary_prompt

    def process(self, file_name: str) -> str:
        book_content = self._read_book_content(file_name)
        chunks = self._chunk_text(book_content)

        processed_chunks = []
        with tqdm(total=len(chunks), desc="Processing chunks") as pbar:
            for chunk in chunks:
                processed_chunk = self._process_chunk(chunk)
                max_retries = 3
                retry_count = 0
                while processed_chunk is None and retry_count < max_retries:
                    pbar.set_postfix(
                        {
                            "status": f"Retrying... (Attempt {retry_count + 1}/{max_retries})"
                        }
                    )
                    processed_chunk = self._process_chunk(chunk)
                    retry_count += 1

                if processed_chunk is None:
                    error_message = (
                        f"Failed to process chunk after {max_retries} attempts."
                    )
                    pbar.set_postfix({"status": "Error"})
                    raise RuntimeError(error_message)

                processed_chunks.append(processed_chunk)
                pbar.update(1)

        if self.summary_system_prompt and self.summary_prompt:
            return self._create_final_summary(processed_chunks)
        else:
            return "\n\n".join(processed_chunks)

    def process_first_chunk(self, file_name: str) -> str:
        book_content = self._read_book_content(file_name)
        chunks = self._chunk_text(book_content)
        first_chunk = chunks[0]
        return self._process_chunk(first_chunk)

    def _process_chunk(self, chunk: str) -> str:
        prompt = self.chunk_prompt.format(text=chunk)
        conversation_id = self._generate_conversation_id()
        self.amp_client.add_system_message(conversation_id, self.chunk_system_prompt)
        return self.amp_client.generate_response(
            conversation_id, prompt, max_tokens=5000
        )

    def _create_final_summary(self, summaries: list[str]) -> str:
        tagged_summaries = []
        for i, summary in enumerate(summaries, 1):
            tagged_summary = f"<SUMMARY_{i}>\n{summary}\n</SUMMARY_{i}>"
            tagged_summaries.append(tagged_summary)

        combined_summary = "\n\n".join(tagged_summaries)
        conversation_id = self._generate_conversation_id()
        self.amp_client.add_system_message(conversation_id, self.summary_system_prompt)
        prompt = self.summary_prompt.format(text=combined_summary)
        return self.amp_client.generate_response(
            conversation_id, prompt, max_tokens=10000
        )

    def _generate_conversation_id(self) -> str:
        return f"book_summary__{str(uuid.uuid4())}"

    def _read_book_content(self, file_name: str) -> str:
        with open(file_name, "r", encoding="utf-8") as file:
            return file.read()

    def _chunk_text(self, text: str) -> list[str]:
        overlap = int(self.chunk_size * 0.1)  # 10% overlap
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        return chunks


def create_summary(
    file_name: str, base_url: str = "http://localhost:17173", chunk_size: int = 150000
) -> str:
    chunk_summary_system_prompt = "You are an expert at summarizing books. Your task is to create concise summaries that are easy to understand for beginners. Provide only the summary content without any introductory or concluding phrases."
    chunk_summary_prompt = (
        "Summarize the following text, providing only the summary content:\n\n{text}"
    )
    final_summary_system_prompt = "You are an expert at creating cohesive book summaries based on chapter summaries. Your task is to synthesize these summaries into a concise overview of the entire book, in a way that is easy to understand for beginners. Provide only the final summary without any introductory or concluding phrases."
    final_summary_prompt = "Create a cohesive and concise summary of the entire book based on these chapter summaries, providing only the summary content:\n\n{text}"

    summarizer = BookProcessor(
        chunk_summary_system_prompt,
        chunk_summary_prompt,
        final_summary_system_prompt,
        final_summary_prompt,
        base_url,
        chunk_size,
    )
    return summarizer.process(file_name)


def create_shortened_version(
    file_name: str, base_url: str = "http://localhost:17173", chunk_size: int = 150000
) -> str:
    # First, analyze the chapters
    chapters = analyze_chapters(file_name, base_url, chunk_size)

    shorten_system_prompt = """You are an expert at condensing books while preserving key information, context, and relationships between concepts. Your task is to create a shortened version optimized for AI language models to process and understand the book's content effectively."""

    shorten_prompt = """Condense the following text, which may be from a specific chapter or section of the book. The book contains the following chapters or main sections:

{chapters}

If you can identify which chapter or section this text is from, please include that information at the beginning of your condensed version.

Focus on:
1. Key concepts, ideas, and arguments
2. Essential plot points or main discussions
3. Important relationships between characters, events, or theories
4. Relevant examples or case studies that illustrate main points
5. Maintain the logical flow and structure of the original text

Aim to reduce the length to about 1/5 of the original while ensuring the condensed version remains coherent and informative for an AI language model. Provide only the condensed content without any introductory or concluding phrases:

{text}"""

    final_combine_system_prompt = """You are an expert at combining condensed text segments into a cohesive, shortened version of a book optimized for AI language model comprehension. Your task is to create a final version that maintains the book's structure, key information, and relationships between concepts."""

    final_combine_prompt = """Combine the following condensed text segments into a cohesive, shortened version of the entire book. The book contains the following chapters or main sections:

{chapters}

Ensure the final version:
1. Maintains the original structure and flow of ideas, using the provided chapter list as a guide
2. Preserves key concepts, arguments, and their relationships
3. Retains essential context and examples
4. Uses clear and concise language optimized for AI processing
5. Includes important terminology and definitions

Aim for a length of approximately 20,000 tokens. Provide only the final shortened version without any introductory or concluding phrases:

{text}

Your final version should read like a condensed book, not a summary. Focus on maintaining the logical structure and relationships between ideas to facilitate AI comprehension. Always include the provided chapter or section headings to clearly delineate different parts of the book."""

    # Format both prompts with the chapters information
    formatted_shorten_prompt = shorten_prompt.format(chapters=chapters, text="{text}")
    formatted_final_combine_prompt = final_combine_prompt.format(
        chapters=chapters, text="{text}"
    )

    shortener = BookProcessor(
        shorten_system_prompt,
        formatted_shorten_prompt,
        final_combine_system_prompt,
        formatted_final_combine_prompt,
        base_url,
        chunk_size,
    )

    return shortener.process(file_name)


def create_qa_pairs(
    file_name: str, base_url: str = "http://localhost:17173", chunk_size: int = 30000
) -> str:
    qa_system_prompt = """You are an expert at creating insightful questions and answers based on book content. Your task is to generate meaningful Q&A pairs that help readers understand and engage with the material. Follow these guidelines:
1. Make sure each question is self-contained and can be understood without additional context.
2. Provide answers that are as detailed as necessary to fully address the question. This can range from a single sentence to a paragraph, depending on the complexity of the question.
3. Output only the questions and answers in the format 'Q: [question]\nA: [answer]', with no additional text."""
    qa_prompt = """Based on the following text, create insightful question and answer pairs. Ensure that each question is self-contained and can be understood without additional context. Provide answers that are as detailed as necessary, which may range from a single sentence to a paragraph:

{text}"""

    qa_processor = BookProcessor(
        qa_system_prompt, qa_prompt, base_url=base_url, chunk_size=chunk_size
    )
    return qa_processor.process(file_name)


def create_rag_qa_pairs(
    file_name: str, base_url: str = "http://localhost:17173", chunk_size: int = 30000
) -> str:
    rag_qa_system_prompt = """You are an expert at creating question-answer pairs optimized for Retrieval Augmented Generation (RAG) systems. Your task is to generate diverse, informative, and context-rich Q&A pairs that will enhance the performance of RAG-based AI models. Follow these guidelines:
1. Create questions that are specific and detailed, covering various aspects of the text.
2. Ensure answers are comprehensive and include relevant context from the text.
3. Generate a mix of factual, conceptual, and analytical questions.
4. Include some questions that require synthesizing information from different parts of the text.
5. Avoid overly broad or generic questions.
6. Output only the questions and answers in the format 'Q: [question]\nA: [answer]', with no additional text."""

    rag_qa_prompt = """Based on the following text, create question and answer pairs optimized for Retrieval Augmented Generation (RAG) systems. Focus on generating diverse, specific, and context-rich Q&A pairs that cover various aspects of the content:

{text}"""

    rag_qa_processor = BookProcessor(
        rag_qa_system_prompt, rag_qa_prompt, base_url=base_url, chunk_size=chunk_size
    )
    return rag_qa_processor.process(file_name)


def create_best_takeaways(
    file_name: str, base_url: str = "http://localhost:17173", chunk_size: int = 30000
) -> str:
    takeaway_system_prompt = """You are an expert at extracting the most important and insightful takeaways from books. Your task is to identify and articulate the key lessons, ideas, or concepts that readers should remember from the given text. Provide only the takeaways without any introductory or concluding phrases."""
    takeaway_prompt = """Based on the following text, provide the 3-5 best takeaways or key insights. Each takeaway should be concise yet informative, capturing the most valuable lessons or ideas from the content. Present your response as a bullet list, with each takeaway starting with an asterisk (*) followed by a space. Do not include any other text, explanations, or introductory/concluding phrases:

{text}"""

    takeaway_processor = BookProcessor(
        takeaway_system_prompt,
        takeaway_prompt,
        base_url=base_url,
        chunk_size=chunk_size,
    )
    return takeaway_processor.process(file_name)


def analyze_chapters(
    file_name: str, base_url: str = "http://localhost:17173", chunk_size: int = 150000
) -> str:
    chapter_system_prompt = """You are an expert in analyzing book structures. Your task is to identify the chapters or main sections of a book based on its opening content."""

    chapter_prompt = """Based on the following text, which represents the opening of a book, identify the chapters or main sections of the book. If exact chapter titles are not available, provide your best estimate of the book's structure:

{text}

Format your response as a Python list of strings, where each string represents a chapter or main section title. For example:
["Chapter 1: Introduction", "Chapter 2: The Basics", "Chapter 3: Advanced Concepts"]"""

    chapter_analyzer = BookProcessor(
        chapter_system_prompt, chapter_prompt, base_url=base_url, chunk_size=chunk_size
    )
    return chapter_analyzer.process_first_chunk(file_name)


def analyze_genre(
    file_name: str, base_url: str = "http://localhost:17173", chunk_size: int = 150000
) -> str:
    genre_system_prompt = """You are an expert in literary analysis and book classification. Your task is to determine the genre of a book based on its opening chapters. Use the BISAC (Book Industry Standards and Communications) Subject Headings as a guide for classification. Focus on the main category, and if applicable, provide one subcategory. You will only output the genre, no other text."""

    genre_prompt = """Based on the following text, which represents the opening of a book, determine its genre according to the BISAC Subject Headings. Provide the main category and, if applicable, one subcategory:

{text}

Format your response as a Python string:
"Main Genre / Subcategory"
If there's no applicable subcategory, only include the main genre.

Ensure that there are spaces around the slash, for example:
"Computers / Programming Languages" instead of "Computers/Programming Languages"
Also, format the genre names with proper capitalization, not all uppercase.
Do not write any reasoning or commentary, just write out the genre.
"""

    genre_analyzer = BookProcessor(
        genre_system_prompt, genre_prompt, base_url=base_url, chunk_size=chunk_size
    )
    return genre_analyzer.process_first_chunk(file_name).strip('"')


def analyze_metadata(
    file_name: str, base_url: str = "http://localhost:17173", chunk_size: int = 150000
) -> list[str]:
    metadata_system_prompt = """You are an expert in extracting metadata from books. Your task is to identify the book's title, author's name, and publication year based on the opening content of the book."""

    metadata_prompt = """Based on the following text, which represents the opening of a book, extract the following metadata:
1. The book's title (formatted as a normal title, not all uppercase)
2. The author's name
3. The publication year

If you cannot find exact information for any of these fields, provide your best estimate or leave it as an empty python string "".

Format the book title as a normal title (e.g., "The Great Gatsby" instead of "THE GREAT GATSBY").
Make sure to have quotes around all strings, and only output the strings, no other text such as "Here is the metadata:" or commentary.

{text}

Format your response as a Python list of strings:
["Book Title", "Author Name", "Publication Year"]"""

    metadata_analyzer = BookProcessor(
        metadata_system_prompt,
        metadata_prompt,
        base_url=base_url,
        chunk_size=chunk_size,
    )
    metadata_analysis = metadata_analyzer.process_first_chunk(file_name)

    # Find the first '[' and the corresponding ']'
    start = metadata_analysis.find("[")
    end = metadata_analysis.find("]", start)

    if start != -1 and end != -1:
        # try:
        metadata_list = eval(metadata_analysis[start : end + 1])
        # except Exception as e:
        #   print(f"Error evaluating metadata: {e}")
        #    metadata_list = ["Unknown", "Unknown", "Unknown"]
    else:
        metadata_list = ["Unknown", "Unknown", "Unknown"]

    return metadata_list


def main():
    fname = "E:\\athol.epub.txt"

    small_chunk_size = 30000
    large_chunk_size = 50000

    # Example usage:
    # summary = create_summary(fname, chunk_size=large_chunk_size)
    # qa_pairs = create_qa_pairs(fname, chunk_size=small_chunk_size)
    # best_takeaways = create_best_takeaways(fname, chunk_size=large_chunk_size)
    # rag_qa_pairs = create_rag_qa_pairs(fname, chunk_size=small_chunk_size)
    # genre = analyze_genre(fname, chunk_size=large_chunk_size)
    # metadata = analyze_metadata(fname, chunk_size=large_chunk_size)
    # shortened_version = create_shortened_version(fname, chunk_size=large_chunk_size)
    # chapters = analyze_chapters(fname, chunk_size=large_chunk_size)

    # Print or process the results as needed
    # print(summary)
    # print(qa_pairs)
    # print(best_takeaways)
    # print(rag_qa_pairs)
    # print(genre)
    # print(metadata)
    # print(shortened_version)
    # print(chapters)


if __name__ == "__main__":
    main()
