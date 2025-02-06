from flask import jsonify, request
import hashlib

# Add cache dictionary at module level
text_cache = {}


def register_summarization_routes(app, amp_manager):
    @app.route("/summarize", methods=["POST"])
    def summarize():
        if request.is_json:
            data = request.get_json()
            text = data.get("text", "")
            url = data.get("url", "")

            if not text:
                return jsonify({"error": "No text provided for summarization"}), 400

            # Generate hash of the text
            text_hash = hashlib.md5(text.encode()).hexdigest()

            # Check if summary exists in cache
            if text_hash in text_cache:
                return jsonify({"summary": text_cache[text_hash]})

            print("Analyzing URL:", url)

            prompt = f"""Please provide a concise summary of the following text from a web page. The summary should:
1. Be around 3-5 sentences long
2. Capture the main topics or themes discussed
3. Highlight any key points or conclusions
4. Avoid unnecessary details or tangents
5. There might be weird numbers and artifacts from the html, ignore them
6. Use double newlines to separate paragraphs
7. Just present the summary, skip any introductions such as "Here is a summary of the text:"

URL: {url}
Text:
{text}

Summary:"""

            messages = [
                {
                    "role": "user",
                    "content": prompt,
                },
            ]

            success, response = amp_manager.chat_completions(
                {
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 500,
                    "model": "Llama-3.1-8B-Lexi-Uncensored_V2_Q8.gguf",
                    "stream": False,
                }
            )

            if not success:
                return jsonify({"error": "Failed to generate summary"}), 500

            summary = response["choices"][0]["message"]["content"]
            # Store in cache before returning
            text_cache[text_hash] = summary
            return jsonify({"summary": summary})

        return jsonify({"error": "Request must be JSON"}), 400
