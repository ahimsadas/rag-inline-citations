# Run PDF Citations README

This README describes how to set up and run a single Python script (`run_pdf_citations.py`) that answers questions over one or more local PDF files and returns a concise answer with inline citations like "[Source N]". It also prints a "SOURCE MAP" that shows which file/page each [Source N] came from.

## Prerequisites
- Python 3.12 or 3.13 (also works on 3.10–3.11)
- An OpenAI API key available in your environment as OPENAI_API_KEY
- The script file saved as: run_pdf_citations.py (place it in any directory you prefer)


## Installation (one-time)
1) Create and activate a virtual environment.

   macOS / Linux (bash/zsh):
       python3 -m venv .venv
       source .venv/bin/activate

   Windows (PowerShell):
       py -m venv .venv
       .\.venv\Scripts\Activate.ps1

2) Upgrade pip and install required packages.

   All platforms (inside the venv):
       pip install -U pip
       pip install "llama-index>=0.13" llama-index-llms-openai llama-index-embeddings-openai llama-index-readers-file pypdf tiktoken

3) Set your OpenAI API key.

   macOS / Linux:
       export OPENAI_API_KEY="sk-..."

   Windows (PowerShell):
       setx OPENAI_API_KEY "sk-..."
       (Open a new terminal, then reactivate your venv.)


## What the Script Does
Given your PDFs and a question:
1) Loads the PDFs using LlamaIndex’s file reader.
2) Builds a vector index using the OpenAI embedding model `text-embedding-3-small`.
3) Retrieves the top-K relevant chunks for your query.
4) Splits retrieved text into smaller pieces and numbers them as:
   “Source 1: ...”, “Source 2: ...”, etc.
5) Uses an OpenAI chat model (default: `gpt-5-nano`) to synthesize a concise answer that cites sources inline as “[Source N]”.
6) Prints the final answer, followed by a “SOURCE MAP” that maps each [Source N] to its file path and page, along with a short snippet.


## How to Run
Basic usage (single PDF):
    python run_pdf_citations.py --pdf /path/to/YourFile.pdf --query "Give me a 5-line summary with inline citations."

Multiple PDFs:
    python run_pdf_citations.py --pdf /path/a.pdf /path/b.pdf --query "What are the main conclusions across these documents?"

Optional flags:
    --top-k <int>          Retrieval depth (default: 4)
    --chunk-size <int>     Chunk size used when splitting (default: 512)
    --chunk-overlap <int>  Overlap between chunks (default: 20)
    --model <str>          OpenAI chat model name (default: gpt-5-nano)

Examples:
    python run_pdf_citations.py --pdf notes.pdf --query "Summarize key findings with citations."
    python run_pdf_citations.py --pdf a.pdf b.pdf --query "Key regulatory requirements?" --top-k 6
    python run_pdf_citations.py --pdf report.pdf --query "List assumptions and their implications." --chunk-size 400 --chunk-overlap 40
    python run_pdf_citations.py --pdf doc.pdf --query "Provide a concise abstract." --model gpt-5-nano


## Expected Output
- A “FINAL ANSWER” section: a compact answer where claims are supported by inline citations like [Source 3], [Source 7].
- A “SOURCE MAP” section:
  - One line per numbered source chunk, e.g.:
        [Source 3] file=/absolute/or/relative/path/to/doc.pdf page=5 score=0.82
          └─ Short snippet of the chunk...
  - The source map helps you verify that every “[Source N]” in the answer corresponds to a real file/page location.
- If no relevant text is found, you may see:
        No results retrieved. Try increasing --top-k or check your PDFs.


## Troubleshooting
- “Error: OPENAI_API_KEY is not set”:
  Set the key as shown above (export/setx), open a new terminal, reactivate the venv, and retry.

- “No results retrieved”:
  Increase retrieval depth (e.g., --top-k 6 or 8) or ensure your PDFs contain relevant text (not just images). If your PDFs are scans, consider OCRing them first.

- Import errors related to readers:
  Ensure you installed both `llama-index-readers-file` and `pypdf` in the same venv.

- Still stuck?
  Confirm Python and package versions:
      python -V
      pip show llama-index
      pip freeze | grep llama-index
  Reinstall inside a fresh venv if needed.


## Notes
- The script keeps output concise by default. You can adjust `--top-k`, `--chunk-size`, and `--chunk-overlap` to influence retrieval breadth and citation granularity.
- The default model is `gpt-5-nano`. You can switch to another OpenAI chat model available in your account via `--model`.