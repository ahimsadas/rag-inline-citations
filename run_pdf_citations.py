#!/usr/bin/env python3
"""
Standalone runner: load local PDFs -> retrieve -> split & number sources -> synthesize
answer with inline [Source N] citations. Compatible with modern LlamaIndex.

Usage:
  python run_pdf_citations.py --pdf notes.pdf --query "Summarize with citations."
  python run_pdf_citations.py --pdf a.pdf b.pdf --query "Main findings?" --top-k 4
"""

import argparse
import asyncio
import os
import sys
from typing import List, Tuple

# --- LlamaIndex imports with compatibility fallbacks ---
from llama_index.core import VectorStoreIndex, PromptTemplate
try:
    # get_response_synthesizer lives here on modern versions
    from llama_index.core.response_synthesizers import get_response_synthesizer
    try:
        # Some versions still expose ResponseMode here
        from llama_index.core.response_synthesizers import ResponseMode  # type: ignore
    except Exception:
        ResponseMode = None  # we'll pass a string instead
except Exception:
    # Older fallback
    from llama_index.core import get_response_synthesizer  # type: ignore
    ResponseMode = None

# SimpleDirectoryReader can be re-exported from core or live in readers.file
try:
    from llama_index.core import SimpleDirectoryReader
except Exception:
    from llama_index.readers.file import SimpleDirectoryReader  # type: ignore

from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode, NodeWithScore
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

CITATION_CHUNK_SIZE = 512
CITATION_CHUNK_OVERLAP = 20

CITATION_QA_TEMPLATE = PromptTemplate(
    """You are a careful analyst. Use ONLY the numbered sources to answer.
Each time you use information, cite it inline as [Source N]. If multiple sources support a claim, include multiple citations.

Sources:
{context_str}

Question:
{query_str}

Rules:
- Never invent citations or source numbers that do not exist above.
- If the answer is not fully supported by the sources, say you don't know.
- Keep the answer concise but complete.

Answer with inline citations:"""
)

CITATION_REFINE_TEMPLATE = PromptTemplate(
    """We are refining an existing answer using NEW numbered sources.
Use the new sources to improve or correct the answer. Preserve correct parts.

Existing answer:
{existing_answer}

New sources:
{context_msg}

Rules:
- Cite using [Source N] from the new sources when you add or modify content.
- If the new sources are not helpful, return the original answer unchanged.

Refined answer with inline citations:"""
)

def _load_pdfs(pdf_paths: List[str]):
    reader = SimpleDirectoryReader(input_files=pdf_paths)
    return reader.load_data()

def _split_and_number(nodes: List[NodeWithScore],
                      chunk_size: int,
                      chunk_overlap: int) -> Tuple[List[NodeWithScore], List[dict]]:
    """Split retrieved nodes into chunks, prefix each with 'Source N:', and track a printable map."""
    splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    numbered_nodes: List[NodeWithScore] = []
    source_map: List[dict] = []
    counter = 1

    for nws in nodes:
        base_node = getattr(nws, "node", nws)
        text = getattr(base_node, "get_content", None)
        text = text() if callable(text) else getattr(base_node, "text", "") or ""

        meta = getattr(base_node, "metadata", {}) or {}
        file_path = meta.get("file_path") or meta.get("filename") or meta.get("source") or "unknown"
        page = meta.get("page_label") or meta.get("page_number") or meta.get("page") or "?"

        for chunk in splitter.split_text(text):
            labeled_text = f"Source {counter}:\n{chunk}"
            new_node = TextNode(
                text=labeled_text,
                metadata={"source_index": counter, "file_path": file_path, "page": page},
            )
            score = getattr(nws, "score", None)
            numbered_nodes.append(NodeWithScore(node=new_node, score=score))
            source_map.append({
                "N": counter, "file_path": file_path, "page": page,
                "score": score, "snippet": chunk[:240].replace("\n", " "),
            })
            counter += 1

    return numbered_nodes, source_map

async def answer_with_citations(pdf_paths: List[str],
                                query: str,
                                top_k: int,
                                chunk_size: int,
                                chunk_overlap: int,
                                model: str) -> None:
    # 1) Load docs
    print(f"Loading {len(pdf_paths)} PDF file(s)...")
    documents = _load_pdfs(pdf_paths)

    # 2) Build index
    embed = OpenAIEmbedding(model="text-embedding-3-small")
    index = VectorStoreIndex.from_documents(documents, embed_model=embed)

    # 3) Retrieve
    retriever = index.as_retriever(similarity_top_k=top_k)
    retrieved = retriever.retrieve(query)
    if not retrieved:
        print("No results retrieved. Try increasing --top-k or check your PDFs.")
        return

    # 4) Split & number
    numbered_nodes, source_map = _split_and_number(retrieved, chunk_size, chunk_overlap)

    # 5) Synthesize with strict citation prompts
    llm = OpenAI(model=model)
    synth_kwargs = dict(
        llm=llm,
        text_qa_template=CITATION_QA_TEMPLATE,
        refine_template=CITATION_REFINE_TEMPLATE,
        use_async=True,
    )
    # Prefer enum if available; otherwise pass a string (works on modern versions)
    if ResponseMode is not None:
        synth_kwargs["response_mode"] = ResponseMode.COMPACT  # type: ignore
    else:
        synth_kwargs["response_mode"] = "compact"

    synthesizer = get_response_synthesizer(**synth_kwargs)
    print("Generating answer...")
    resp = await synthesizer.asynthesize(query, nodes=numbered_nodes)

    # 6) Print final answer
    print("\n" + "=" * 80)
    print("FINAL ANSWER")
    print("=" * 80)
    final_text = getattr(resp, "response", None) or getattr(resp, "text", None) or str(resp)
    print(final_text)

    # 7) Show mapping for [Source N] → file/page
    print("\n" + "-" * 80)
    print("SOURCE MAP (match these to the [Source N] citations in the answer)")
    print("-" * 80)
    for s in source_map[:50]:
        print(f"[Source {s['N']}] file={s['file_path']} page={s['page']} score={s['score']}")
        print(f"  └─ {s['snippet']}...")
    if len(source_map) > 50:
        print(f"...and {len(source_map) - 50} more chunks.")

def main():
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY is not set. Example:")
        print("  export OPENAI_API_KEY='sk-...'")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Answer questions over local PDF(s) with inline [Source N] citations.")
    parser.add_argument("--pdf", nargs="+", required=True, help="Path(s) to one or more PDF files.")
    parser.add_argument("--query", required=True, help="Your question.")
    parser.add_argument("--top-k", type=int, default=4, help="Retriever top_k (default: 4).")
    parser.add_argument("--chunk-size", type=int, default=CITATION_CHUNK_SIZE, help="Chunk size for citation nodes.")
    parser.add_argument("--chunk-overlap", type=int, default=CITATION_CHUNK_OVERLAP, help="Chunk overlap for citation nodes.")
    parser.add_argument("--model", default="gpt-5-nano", help="OpenAI chat model (default: gpt-5-nano).")
    args = parser.parse_args()

    try:
        asyncio.run(
            answer_with_citations(
                pdf_paths=args.pdf,
                query=args.query,
                top_k=args.top_k,
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap,
                model=args.model,
            )
        )
    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:
        print("\nFatal error:", repr(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
