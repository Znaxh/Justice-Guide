from src.data_retrieval import get_excerpt
import pandas as pd
import torch
import gc

# Initialize the reranker model (optional)
try:
    from FlagEmbedding import FlagReranker
    reranker_model = FlagReranker('BAAI/bge-reranker-base', use_fp16=True) # use_fp16 speeds up computation with a slight performance degradation
    print("Reranker model loaded successfully")
except Exception as e:
    print(f"Warning: Could not load reranker model: {e}")
    reranker_model = None

# Re-rank Search Results using Re-ranker from BGE Reranker
# Pass all the results to a stronger model to give them the similarity ranking

def get_reranked_docs(query):
    try:
        old_docs = get_excerpt(query)
        df_old_docs = pd.DataFrame(old_docs, columns=["Excerpts"])

        if reranker_model:
            torch.cuda.empty_cache()
            gc.collect()
            df_old_docs["new_scores"] = reranker_model.compute_score([[query,chunk] for chunk in df_old_docs['Excerpts']]) # Re compute ranks
            df_old_docs = df_old_docs.sort_values(by = "new_scores", ascending = False).reset_index(drop = True)

        return df_old_docs['Excerpts'].tolist()
    except Exception as e:
        print(f"Error in reranking: {e}")
        # Fallback to simple retrieval without reranking
        return get_excerpt(query)

# print("get_reranked_docs: ", get_reranked_docs(query = "what is indian panel code?"))