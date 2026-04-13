"""
LlamaIndex + FAISS retrieval with on-disk persistence (no pickle).
Loads the embedding model and index only on first use.
"""

from __future__ import annotations

import re
import shutil
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import faiss
import structlog
from llama_index.core import (
    Document,
    QueryBundle,
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.query_engine import CitationQueryEngine
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.faiss import FaissVectorStore

from src import config

logger = structlog.get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_ROOT / "dataset"
LEGACY_CHUNK_DIR = DATASET_DIR / "Indian Penal Code Book (2)_chunks"
INDEX_DIR = PROJECT_ROOT / "data" / "index"

EMBED_DIM = 384

_lock = threading.Lock()
_state: "_IndexState | None" = None

STRUCTURE_KEYWORDS = (
    "different sections",
    "sections in ipc",
    "structure of ipc",
    "chapters in ipc",
    "different chapters",
    "overview of ipc",
    "how many sections",
    "how many chapters",
    "what are the chapters",
    "what are the sections",
    "list of chapters",
    "list of sections",
    "chapters within",
    "sections within",
    "organization of",
    "structure and organization",
    "categories of offenses",
    "different categories",
    "organized into",
    "divided into",
    "framework",
    "classification",
)

IPC_OVERVIEW_TEXT = (
    "The Indian Penal Code (IPC) contains 511 sections divided into 23 chapters covering substantive "
    "criminal law in India, including offences against the state, public tranquillity, the human body, "
    "property, and related topics. Individual sections define elements and punishments for specific offences."
)


def _ipc_section_from_path(path: str) -> str:
    base = Path(path).name
    m = re.search(r"(?:section|sec\.?)\s*(\d+)", base, re.I)
    if m:
        return m.group(1)
    m2 = re.search(r"\b(\d{3})\b", base)
    if m2:
        return m2.group(1)
    return "unknown"


def _file_metadata(path: str) -> dict[str, Any]:
    return {
        "source_file": Path(path).name,
        "ipc_section": _ipc_section_from_path(path),
    }


def _sample_documents() -> list[Document]:
    texts = [
        "The Indian Penal Code (IPC) is the main criminal code of India covering substantive criminal law.",
        IPC_OVERVIEW_TEXT,
        "Section 300 of the Indian Penal Code defines murder when culpable homicide falls within its clauses.",
        "Section 302 of the Indian Penal Code prescribes punishment for murder: death or imprisonment for life, and fine.",
        "Section 299 defines culpable homicide; Section 300 narrows when it amounts to murder.",
        "Section 420 of the IPC deals with cheating and dishonestly inducing delivery of property.",
    ]
    docs: list[Document] = []
    for i, t in enumerate(texts):
        docs.append(
            Document(
                text=t,
                metadata={
                    "source_file": f"sample_{i}.txt",
                    "ipc_section": "sample",
                    "page_label": "1",
                },
            )
        )
    return docs


def _pick_input_dir() -> Path | None:
    if LEGACY_CHUNK_DIR.is_dir():
        return LEGACY_CHUNK_DIR
    if DATASET_DIR.is_dir() and any(DATASET_DIR.rglob("*.pdf")):
        return DATASET_DIR
    return None


def _build_documents() -> list[Document]:
    input_dir = _pick_input_dir()
    if input_dir is None:
        logger.info("retrieval.no_pdf_dataset", path=str(DATASET_DIR))
        return _sample_documents()

    reader = SimpleDirectoryReader(
        input_dir=str(input_dir),
        recursive=True,
        required_exts=[".pdf"],
        file_metadata=_file_metadata,
    )
    docs = reader.load_data()
    if not docs:
        logger.info("retrieval.empty_pdf_load", path=str(input_dir))
        return _sample_documents()
    return docs


def _make_embed_model() -> HuggingFaceEmbedding:
    return HuggingFaceEmbedding(model_name=config.EMBEDDING_MODEL)


def _nodes_from_documents(documents: list[Document]) -> list[Any]:
    splitter = SentenceSplitter(chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP)
    nodes = splitter.get_nodes_from_documents(documents)
    for i, node in enumerate(nodes):
        node.metadata.setdefault("chunk_index", i)
        node.metadata.setdefault("source_file", node.metadata.get("file_name", "unknown"))
        node.metadata.setdefault("ipc_section", _ipc_section_from_path(str(node.metadata.get("file_path", ""))))
        if "page_label" not in node.metadata and "page" in node.metadata:
            node.metadata["page_label"] = str(node.metadata["page"])
    return nodes


def _persist_index(nodes: list[Any], embed_model: HuggingFaceEmbedding) -> None:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss_index = faiss.IndexFlatIP(EMBED_DIM)
    vector_store = FaissVectorStore(faiss_index=faiss_index)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    VectorStoreIndex(
        nodes,
        storage_context=storage_context,
        embed_model=embed_model,
        show_progress=True,
    )
    storage_context.persist(persist_dir=str(INDEX_DIR))
    logger.info("retrieval.index_persisted", path=str(INDEX_DIR), num_nodes=len(nodes))


def _load_index(embed_model: HuggingFaceEmbedding) -> VectorStoreIndex:
    vector_store = FaissVectorStore.from_persist_dir(str(INDEX_DIR))
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store,
        persist_dir=str(INDEX_DIR),
    )
    return load_index_from_storage(storage_context, embed_model=embed_model)


@dataclass
class _IndexState:
    index: VectorStoreIndex
    embed_model: HuggingFaceEmbedding
    citation_engine: CitationQueryEngine


def _build_state_unlocked() -> _IndexState:
    embed_model = _make_embed_model()
    if not (INDEX_DIR / "docstore.json").exists():
        documents = _build_documents()
        nodes = _nodes_from_documents(documents)
        _persist_index(nodes, embed_model)
    index = _load_index(embed_model)
    from llama_index.core.llms.mock import MockLLM

    citation_engine = CitationQueryEngine.from_args(
        index,
        similarity_top_k=config.TOP_K,
        citation_chunk_size=config.CHUNK_SIZE,
        llm=MockLLM(max_tokens=16),
    )
    return _IndexState(index=index, embed_model=embed_model, citation_engine=citation_engine)


def ensure_index_loaded() -> _IndexState:
    """Lazy-load FAISS + LlamaIndex artefacts (first query pays the cost)."""
    global _state
    with _lock:
        if _state is None:
            logger.info("retrieval.lazy_load_start")
            _state = _build_state_unlocked()
            logger.info("retrieval.lazy_load_done")
        return _state


def rebuild_index() -> None:
    """Delete persisted index and rebuild from dataset/ on next load."""
    global _state
    with _lock:
        _state = None
        if INDEX_DIR.exists():
            shutil.rmtree(INDEX_DIR)
            logger.info("retrieval.index_deleted", path=str(INDEX_DIR))
        _state = _build_state_unlocked()
        logger.info("retrieval.index_rebuilt")


def _is_structure_query(query: str) -> bool:
    q = query.lower()
    return any(k in q for k in STRUCTURE_KEYWORDS)


def retrieve_cited_context(enhanced_query: str, top_k: int | None = None) -> tuple[str, list[dict[str, Any]], int]:
    """
    Retrieve chunks via CitationQueryEngine.retrieve so nodes carry citation-ready metadata.
    Returns (numbered_context, citations_metadata, num_chunks).
    """
    if top_k is None:
        top_k = config.TOP_K
    state = ensure_index_loaded()
    query_bundle = QueryBundle(query_str=enhanced_query)
    nodes = state.citation_engine.retrieve(query_bundle)

    if _is_structure_query(enhanced_query):
        prefix = (
            "[0] (source: ipc_overview, page: n/a)\n"
            f"{IPC_OVERVIEW_TEXT}\n\n"
        )
        extra_offset = 1
    else:
        prefix = ""
        extra_offset = 0

    lines: list[str] = []
    citations: list[dict[str, Any]] = []
    if prefix:
        lines.append(prefix.rstrip("\n"))
        citations.append(
            {
                "citation_id": 0,
                "source_file": "ipc_overview",
                "page": "n/a",
                "ipc_section": None,
                "chunk_index": None,
                "score": None,
                "text": IPC_OVERVIEW_TEXT,
            }
        )
    for i, nws in enumerate(nodes[:top_k], start=1):
        label = i - 1 + extra_offset
        meta = nws.node.metadata
        src = meta.get("source_file", "unknown")
        page = meta.get("page_label") or meta.get("page_number") or "n/a"
        body = nws.node.get_content().strip()
        lines.append(f"[{label}] (source: {src}, page: {page})\n{body}")
        citations.append(
            {
                "citation_id": label,
                "source_file": src,
                "page": page,
                "ipc_section": meta.get("ipc_section"),
                "chunk_index": meta.get("chunk_index"),
                "score": float(nws.score) if nws.score is not None else None,
                "text": body,
            }
        )

    context = "\n\n".join(lines)
    return context, citations, len(citations)
