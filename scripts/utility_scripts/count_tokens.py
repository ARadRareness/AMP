from transformers import (
    AutoTokenizer,
    LlamaTokenizerFast,
    GemmaTokenizerFast,
    Qwen2TokenizerFast,
)

tokenizer_qwen = Qwen2TokenizerFast.from_pretrained("Qwen/Qwen-tokenizer")
tokenizer_llama = LlamaTokenizerFast.from_pretrained(
    "hf-internal-testing/llama-tokenizer"
)
tokenizer_llama3 = AutoTokenizer.from_pretrained("Xenova/llama-3-tokenizer")
tokenizer_gemma = GemmaTokenizerFast.from_pretrained("Xenova/gemma-tokenizer")

print(tokenizer_qwen.encode("Hello, world!"))
print(tokenizer_llama.encode("Hello, world!"))
print(tokenizer_llama3.encode("Hello, world!"))
print(tokenizer_gemma.encode("Hello, world!"))
