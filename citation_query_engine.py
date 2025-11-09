"""
Run a RAG query with inline numeric citations over local PDF files.

Usage:
  python citation-query-engine.py \
    --pdf /path/to/a.pdf /path/to/b.pdf \
    --query "Summarize the key findings with citations." \
    --top-k 4 \
    --citation-chunk-size 80 \
    --citation-chunk-overlap 10 \
    --model gpt-5-nano

Prereqs (install into your venv):
  pip install -U "llama-index>=0.13" llama-index-llms-openai \
                 llama-index-embeddings-openai llama-index-readers-file \
                 pypdf tiktoken

Environment:
  export OPENAI_API_KEY="sk-..."
"""

import argparse
import os
import sys
from typing import List

# Core LlamaIndex pieces
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.query_engine import CitationQueryEngine

# OpenAI LLM + Embeddings wrappers
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding


def load_pdfs(file_paths: List[str]):
    """Load PDFs as LlamaIndex Documents."""
    # SimpleDirectoryReader supports input_files to load specific files
    # (and attaches metadata like file_name, page_label for PDFs).
    reader = SimpleDirectoryReader(
        input_files=file_paths,
        required_exts=[".pdf"],   # ignore any non-PDFs accidentally passed
    )
    return reader.load_data()


def build_index(documents, embed_model_name: str = "text-embedding-3-small"):
    """Create a VectorStoreIndex with the given embedding model."""
    embed_model = OpenAIEmbedding(model=embed_model_name)
    index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)
    return index


def make_citation_engine(
    index: VectorStoreIndex,
    model_name: str = "gpt-5-nano",
    top_k: int = 4,
    citation_chunk_size: int = 80,
    citation_chunk_overlap: int = 10,
):
    """
    Build a CitationQueryEngine from an index.

    Notes:
      - similarity_top_k controls how many nodes are retrieved.
      - citation_chunk_size/overlap control re-chunking granularity for numbered sources.
    """
    llm = OpenAI(model=model_name)
    engine = CitationQueryEngine.from_args(
        index,
        llm=llm,
        similarity_top_k=top_k,
        citation_chunk_size=citation_chunk_size,
        citation_chunk_overlap=citation_chunk_overlap,
        # You can also override the default citation QA/refine templates here if needed.
    )
    return engine


def print_source_map(response):
    """
    Print a compact source map so the [N] in the answer can be verified.
    For PDFs, metadata typically includes 'file_name' and 'page_label'.
    """
    print("\n=== SOURCE MAP ===")
    if not getattr(response, "source_nodes", None):
        print("(no source nodes returned)")
        return

    for i, sn in enumerate(response.source_nodes, start=1):
        meta = getattr(sn.node, "metadata", {}) or {}
        file_name = meta.get("file_name") or meta.get("file_path") or "unknown_file"
        page = meta.get("page_label") or meta.get("page") or meta.get("page_number")
        score = getattr(sn, "score", None)
        head = f"[{i}] file={file_name}"
        if page is not None:
            head += f" page={page}"
        if score is not None:
            head += f" score={score:.3f}"
        print(head)
        # Optional: show a short snippet (trim newlines)
        try:
            text = sn.node.get_content().strip().replace("\n", " ")
            if len(text) > 220:
                text = text[:220] + " ..."
            print("  └─", text)
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(
        description="Query local PDFs with LlamaIndex CitationQueryEngine (inline numeric citations)."
    )
    parser.add_argument(
        "--pdf",
        nargs="+",
        required=True,
        help="Path(s) to one or more PDF files.",
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Your natural-language question.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=4,
        help="Retriever depth (similarity_top_k). Default: 4",
    )
    parser.add_argument(
        "--citation-chunk-size",
        type=int,
        default=80,
        help="Size for citation source chunks. Default: 80",
    )
    parser.add_argument(
        "--citation-chunk-overlap",
        type=int,
        default=10,
        help="Overlap for citation source chunks. Default: 10",
    )
    parser.add_argument(
        "--model",
        default="gpt-5-nano",
        help="OpenAI chat model for synthesis. Default: gpt-5-nano",
    )
    parser.add_argument(
        "--embed-model",
        default="text-embedding-3-small",
        help="OpenAI embedding model. Default: text-embedding-3-small",
    )

    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY is not set in the environment.", file=sys.stderr)
        sys.exit(2)

    # Validate files early
    pdfs = []
    for p in args.pdf:
        if not os.path.exists(p):
            print(f"ERROR: File not found: {p}", file=sys.stderr)
            sys.exit(2)
        pdfs.append(os.path.abspath(p))

    print("Loading PDFs...")
    documents = load_pdfs(pdfs)
    if not documents:
        print("No documents loaded from the provided PDFs.", file=sys.stderr)
        sys.exit(1)

    print("Building index...")
    index = build_index(documents, embed_model_name=args.embed_model)

    print("Creating citation query engine...")
    engine = make_citation_engine(
        index=index,
        model_name=args.model,
        top_k=args.top_k,
        citation_chunk_size=args.citation_chunk_size,
        citation_chunk_overlap=args.citation_chunk_overlap,
    )

    print("\n=== QUERY ===")
    print(args.query)

    response = engine.query(args.query)

    print("\n=== ANSWER (with inline citations) ===")
    # Printing the response object renders the text with inline [N] citations.
    print(str(response).strip())

    print_source_map(response)


if __name__ == "__main__":
    main()