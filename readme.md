# RAG PDF with Inline Citations

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![OpenAI API](https://img.shields.io/badge/OpenAI-API-412991)](https://platform.openai.com/)

This document describes two alternative scripts that answer questions over one or more local PDF files and return a concise response with inline citations, plus a source listing for verification.

Option A: inline_citation_generator.py
- A standalone pipeline that retrieves relevant chunks, splits and numbers them as “Source N: …”, and synthesizes an answer that cites as “[N]”.
- Offers granular control (retrieval depth, chunking, prompts, model).

Option B: citation_query_engine.py
- Uses LlamaIndex’s built-in CitationQueryEngine for a higher-level, batteries-included API.
- Produces inline numeric citations like “[1]”, “[2]” and exposes source nodes.


Prerequisites (Both Options)
----------------------------
- Python 3.12 or 3.13 (also works on 3.10–3.11)
- An OpenAI API key in your environment as OPENAI_API_KEY
- Virtual environment recommended

Shared one-time install:
  macOS / Linux (bash/zsh)
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -U pip
    pip install "llama-index>=0.13" \
                llama-index-llms-openai \
                llama-index-embeddings-openai \
                llama-index-readers-file \
                pypdf tiktoken
  
  Windows (PowerShell)
    py -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -U pip
    pip install "llama-index>=0.13" `
                llama-index-llms-openai `
                llama-index-embeddings-openai `
                llama-index-readers-file `
                pypdf tiktoken

Set your API key:
  macOS / Linux
    export OPENAI_API_KEY="sk-..."
  Windows (PowerShell)
    setx OPENAI_API_KEY "sk-..."
    (Open a new terminal, then reactivate your venv.)

### Option A: inline_citation_generator.py

#### What it does
1) Loads local PDF(s).
2) Builds a vector index using the OpenAI embedding model “text-embedding-3-small”.
3) Retrieves the top-K relevant chunks for your query.
4) Splits retrieved text and prefixes each chunk as “Source N: …”.
5) Uses an OpenAI chat model (default: gpt-5-nano) to synthesize a concise answer that cites inline as “[N]”.
6) Prints the final answer and then a “SOURCE MAP” listing each [N] with file path and page.

#### Basic usage (single PDF)

```bash
python inline_citation_generator.py \
  --pdf /path/to/YourFile.pdf \
  --query "Give me a 5-line summary with inline citations."
```

#### Multiple PDFs

```bash
python inline_citation_generator.py \
  --pdf /path/a.pdf /path/b.pdf \
  --query "What are the main conclusions across these documents?"
```

#### Optional flags

| Flag | Description | Default |
| --- | --- | --- |
| --top-k <int> | Retrieval depth | 5 |
| --chunk-size <int> | Chunk size for splitting | 80 |
| --chunk-overlap <int> | Overlap between chunks | 10 |
| --model <str> | OpenAI chat model | gpt-5-nano |

#### Examples

```bash
python inline_citation_generator.py --pdf notes.pdf --query "Summarize key findings with citations."
python inline_citation_generator.py --pdf a.pdf b.pdf --query "Key regulatory requirements?" --top-k 6
python inline_citation_generator.py --pdf report.pdf --query "List assumptions and implications." --chunk-size 400 --chunk-overlap 40
python inline_citation_generator.py --pdf doc.pdf --query "Provide a concise abstract." --model gpt-4o-mini
```

#### Expected output

- FINAL ANSWER with inline citations like “[3]”.
- SOURCE MAP lines like:
  [3] file=/path/to/doc.pdf page=5 score=0.82
  └─ Short snippet...
- If nothing relevant is retrieved:
  No results retrieved. Try increasing --top-k or check your PDFs.

### Option B: citation_query_engine.py

#### What it does

1) Loads local PDF(s).
2) Builds a vector index using “text-embedding-3-small”.
3) Wraps the index with LlamaIndex’s CitationQueryEngine to:
   - Re-chunk retrieved text for citation granularity.
   - Produce inline numeric citations like “[1]”, “[2]”.
4) Prints the final answer and a compact source map (from response.source_nodes).

#### Basic usage (single PDF)

```bash
python citation_query_engine.py \
  --pdf /path/to/YourFile.pdf \
  --query "Summarize the key findings with citations."
```

#### Multiple PDFs

```bash
python citation_query_engine.py \
  --pdf /path/a.pdf /path/b.pdf \
  --query "What are the main conclusions across these documents?"
```

#### Optional flags

| Flag | Description | Default |
| --- | --- | --- |
| --top-k <int> | Retrieval depth | 4 |
| --citation-chunk-size <int> | Citation chunk size | 80 |
| --citation-chunk-overlap <int> | Citation chunk overlap | 10 |
| --model <str> | OpenAI chat model | gpt-5-nano |
| --embed-model <str> | Embedding model | text-embedding-3-small |

#### Examples

```bash
python citation_query_engine.py --pdf notes.pdf --query "Summarize key findings with citations."
python citation_query_engine.py --pdf a.pdf b.pdf --query "Key regulatory requirements?" --top-k 6
python citation_query_engine.py --pdf report.pdf --query "Main assumptions?" --citation-chunk-size 400 --citation-chunk-overlap 40
python citation_query_engine.py --pdf doc.pdf --query "Concise abstract." --model gpt-4o-mini
```

#### Expected output

- FINAL ANSWER with inline numeric citations like “[1]”, “[2]”.
- SOURCE MAP listing each numbered source node’s file path and page.

### Key Differences (A vs B)

1) API style
   - A (inline_citation_generator.py): Explicit pipeline you control end-to-end (retrieve → split/number → synthesize). Uses LlamaIndex’s ResponseSynthesizer directly.
   - B (citation_query_engine.py): High-level engine that bundles retrieval, re-chunking for citations, and synthesis in one component.

2) Citation format
   - A: Cites as “[N]” because chunks are explicitly labeled “Source N: …” in the prompt context.
   - B: Cites as “[1]”, “[2]”, etc., following CitationQueryEngine’s built-in numbering.

3) Granularity and extensibility
   - A: More granular control over prompts and chunk labeling; easy to add custom rules/guardrails or extra pipeline steps (reranking, filters).
   - B: Faster to use, fewer moving parts; tune via engine kwargs (top-k, citation chunk size/overlap) but less explicit control per step.

4) Output ergonomics
   - A: Prints a “SOURCE MAP” aligned to “[N]”.
   - B: Prints a source map based on engine’s numbered source nodes (typically “[1]”, “[2]”, …).

5) Code footprint
   - A: Slightly more code; designed for customization.
   - B: Smaller surface area; designed for quick adoption.

### Troubleshooting (Both Options)

- “Error: OPENAI_API_KEY is not set”
  Export/set the key as shown above, open a new terminal, reactivate the venv, and retry.

- “No results retrieved”
  Increase --top-k (e.g., 6 or 8) or ensure your PDFs contain extractable text. For scanned PDFs, run OCR first.

- Reader/loader import issues
  Ensure both llama-index-readers-file and pypdf are installed in the same venv.

- Environment sanity checks
  ```bash
python -V
pip show llama-index
pip freeze | grep llama-index
```

If problems persist, try a fresh virtual environment and reinstall the dependencies listed above.

## License

MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.