"""Versioned prompt templates for Justice-Guide RAG."""

from langchain_core.prompts import ChatPromptTemplate

VERSION = "v1.0"

QUERY_ENHANCEMENT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You rewrite user queries for legal document retrieval in the Indian context (IPC, CrPC, "
            "constitutional references, and common Hindi/English legal phrasing). "
            "Keep the user's intent; add IPC-related keywords where helpful; do not invent facts.",
        ),
        (
            "human",
            "Original query:\n{query}\n\nOutput a single enhanced search query on one line, "
            "optimised for retrieving Indian Penal Code and related statutory text.",
        ),
    ]
)

ANSWER_SYSTEM = (
    "You are a research assistant for Indian criminal law materials. "
    "You are not a lawyer. Use only the numbered context excerpts [1], [2], … below. "
    "When you use information from a chunk, cite it inline using the same numbers, e.g. [1] or [2]. "
    "If the excerpts do not contain enough information to answer, respond exactly with: "
    "I cannot find this in the provided legal text. "
    "Do not rely on outside knowledge beyond what is in the excerpts.\n\n"
    "Disclaimer: This is not legal advice. Consult a qualified lawyer for your situation."
)

ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", ANSWER_SYSTEM),
        (
            "human",
            "Context (each block is labelled with a citation number):\n{context}\n\n"
            "Original question: {question}\n"
            "Retrieval-enhanced query: {enhanced_query}\n\n"
            "Answer with inline citations like [1] where appropriate.",
        ),
    ]
)

PROMPT_REGISTRY = {
    "query_enhancement": QUERY_ENHANCEMENT_PROMPT,
    "answer_generation": ANSWER_PROMPT,
}
