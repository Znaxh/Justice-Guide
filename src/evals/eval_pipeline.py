"""
Ragas evaluation over a small IPC test set (<= MAX_EVAL_ROWS for 8GB RAM).
Run: python -m src.evals.eval_pipeline
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import structlog
from datasets import Dataset
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from src import config
from src.pipeline import run_rag_sync
from src import prompts

logger = structlog.get_logger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent
_p_eval = Path(config.EVAL_DATASET_PATH)
DATA_PATH = _p_eval if _p_eval.is_absolute() else ROOT / _p_eval
OUT_DIR = ROOT / "data" / "eval_results"


def _load_rows() -> list[dict]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing {DATA_PATH}")
    with open(DATA_PATH, encoding="utf-8") as f:
        rows = json.load(f)
    if len(rows) > config.MAX_EVAL_ROWS:
        rows = rows[: config.MAX_EVAL_ROWS]
    return rows


def run_evals() -> str:
    """Load dataset, run pipeline, score with Ragas, write JSON."""
    try:
        from ragas import evaluate
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from ragas.llms import LangchainLLMWrapper
        from ragas.metrics import answer_relevancy, context_precision, faithfulness
    except ImportError as exc:
        raise RuntimeError("ragas is required for evaluations") from exc

    if not config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is required for Ragas judge (Gemini)")

    lc_chat = ChatGoogleGenerativeAI(
        model=config.GEMINI_MODEL,
        google_api_key=config.GEMINI_API_KEY,
        temperature=0,
    )
    judge_llm = LangchainLLMWrapper(lc_chat)
    judge_embeddings = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)
    )

    try:
        lc_chat.invoke([HumanMessage(content="ping")])
        logger.info("eval_llm_reachable", model=config.GEMINI_MODEL)
    except Exception as e:
        logger.error("eval_llm_unreachable", error=str(e), model=config.GEMINI_MODEL)
        raise RuntimeError(
            f"Cannot reach judge LLM ({config.GEMINI_MODEL}). "
            "Check GEMINI_API_KEY and model name in config."
        ) from e

    eval_rows = _load_rows()
    questions: list[str] = []
    answers: list[str] = []
    contexts: list[list[str]] = []
    ground_truths: list[str] = []

    for row in eval_rows:
        questions.append(row["question"])
        ground_truths.append(row["ground_truth"])
        r = run_rag_sync(row["question"])
        answers.append(r.get("answer") or "")
        texts = [c.get("text", "") for c in (r.get("citations") or []) if c.get("text")]
        if not texts:
            texts = list(row.get("contexts") or [])
        contexts.append(texts)

    ds = Dataset.from_dict(
        {
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths,
            "reference": ground_truths,
        }
    )

    faithfulness.llm = judge_llm
    answer_relevancy.llm = judge_llm
    answer_relevancy.embeddings = judge_embeddings
    context_precision.llm = judge_llm

    result = evaluate(
        ds,
        metrics=[faithfulness, answer_relevancy, context_precision],
        llm=judge_llm,
        embeddings=judge_embeddings,
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    eval_ts_iso = datetime.now(timezone.utc).isoformat()
    out_path = OUT_DIR / f"eval_{ts}.json"

    summary_records: list = []
    means: dict = {}
    try:
        if hasattr(result, "to_pandas"):
            summary_df = result.to_pandas()
            summary_records = summary_df.to_dict(orient="records")
            means = summary_df.mean(numeric_only=True).to_dict()
        elif hasattr(result, "scores"):
            means = dict(result.scores)
        else:
            means = {k: float(v) for k, v in dict(result).items() if isinstance(v, (int, float))}
    except Exception:
        means = {"error": "could_not_summarize"}

    results_payload = {
        "eval_timestamp": eval_ts_iso,
        "prompt_version": prompts.VERSION,
        "gemini_model": config.GEMINI_MODEL,
        "num_questions": len(eval_rows),
        "metrics": means,
        "mean_scores": means,
        "rows": summary_records,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2, default=str)

    logger.info("eval.completed", path=str(out_path), mean_scores=means)
    for k, v in sorted(means.items()):
        try:
            fv = round(float(v), 4)
        except (TypeError, ValueError):
            fv = None
        logger.info("eval.metric_mean", metric=k, value=fv)
    logger.info("eval.wrote_results", path=str(out_path))
    return str(out_path)


def run_evals_job() -> str:
    """Background-thread entry used by the admin API."""
    return run_evals()


def main() -> None:
    run_evals()


if __name__ == "__main__":
    main()
