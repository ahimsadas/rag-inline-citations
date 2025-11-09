# Run PDF Citations

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![OpenAI API](https://img.shields.io/badge/OpenAI-API-412991)](https://platform.openai.com/)

This README describes how to set up and run a single Python script (`run_pdf_citations.py`) that answers questions over one or more local PDF files and returns a concise answer with inline citations like "[Source N]". It also prints a "SOURCE MAP" that shows which file/page each [Source N] came from.

## Prerequisites

- Python 3.12 or 3.13 (also works on 3.10–3.11)
- An OpenAI API key available in your environment as `OPENAI_API_KEY`
- The script file saved as: `run_pdf_citations.py` (place it in any directory you prefer)

## Installation (one-time)

1. Create and activate a virtual environment:

   ```bash
   # macOS / Linux (bash/zsh)
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   ```powershell
   # Windows (PowerShell)
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Upgrade pip and install required packages:

   ```bash
   # All platforms (inside the venv)
   pip install -U pip
   pip install "llama-index>=0.13" llama-index-llms-openai llama-index-embeddings-openai llama-index-readers-file pypdf tiktoken
   ```

3. Set your OpenAI API key:

   ```bash
   # macOS / Linux
   export OPENAI_API_KEY="sk-..."
   ```

   ```powershell
   # Windows (PowerShell)
   setx OPENAI_API_KEY "sk-..."
   # Open a new terminal, then reactivate your venv
   ```


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

### Basic Usage (Single PDF)
```bash
python run_pdf_citations.py --pdf /path/to/YourFile.pdf --query "Give me a 5-line summary with inline citations."
```

### Multiple PDFs
```bash
python run_pdf_citations.py --pdf /path/a.pdf /path/b.pdf --query "What are the main conclusions across these documents?"
```

### Optional Flags
| Flag | Description | Default |
|------|-------------|---------|
| `--top-k <int>` | Retrieval depth | 4 |
| `--chunk-size <int>` | Chunk size used when splitting | 512 |
| `--chunk-overlap <int>` | Overlap between chunks | 20 |
| `--model <str>` | OpenAI chat model name | gpt-5-nano |

### Examples
```bash
# Summarize key findings
python run_pdf_citations.py --pdf notes.pdf --query "Summarize key findings with citations."

# Analyze multiple documents
python run_pdf_citations.py --pdf a.pdf b.pdf --query "Key regulatory requirements?" --top-k 6

# Custom chunk settings
python run_pdf_citations.py --pdf report.pdf --query "List assumptions and their implications." --chunk-size 400 --chunk-overlap 40

# Specify model
python run_pdf_citations.py --pdf doc.pdf --query "Provide a concise abstract." --model gpt-5-nano
```


## Expected Output

### FINAL ANSWER Section
A compact answer where claims are supported by inline citations like `[Source 3]`, `[Source 7]`.

### SOURCE MAP Section
One line per numbered source chunk, for example:
```
[Source 3] file=/absolute/or/relative/path/to/doc.pdf page=5 score=0.82
  └─ Short snippet of the chunk...
```

The source map helps you verify that every `[Source N]` in the answer corresponds to a real file/page location.

### No Results Case
If no relevant text is found, you may see:
```
No results retrieved. Try increasing --top-k or check your PDFs.
```


## Troubleshooting

### Common Issues

#### "Error: OPENAI_API_KEY is not set"
Set the key as shown in the installation section, open a new terminal, reactivate the venv, and retry.

#### "No results retrieved"
- Increase retrieval depth (e.g., `--top-k 6` or `--top-k 8`)
- Ensure your PDFs contain relevant text (not just images)
- For scanned PDFs, consider OCRing them first

#### Import errors related to readers
Ensure you installed both `llama-index-readers-file` and `pypdf` in the same venv.

#### Still stuck?
Check your environment setup:
```bash
# Verify Python version
python -V

# Check package versions
pip show llama-index
pip freeze | grep llama-index
```
If issues persist, try reinstalling in a fresh venv.


## Additional Notes

### Default Behavior
The script keeps output concise by default. You can adjust the following parameters to influence retrieval breadth and citation granularity:
- `--top-k` for number of chunks to retrieve
- `--chunk-size` for text segment size
- `--chunk-overlap` for context preservation

### Model Selection
The default model is `gpt-5-nano`. You can switch to another OpenAI chat model available in your account using the `--model` parameter.