#!/usr/bin/env python3

from src.data_retrieval import get_excerpt
from src.generate_answers import generate_answer

def test_retrieval():
    print("Testing document retrieval system...")

    # Test query about murder
    query = "What constitutes murder under Indian law?"
    print(f"Query: {query}")

    try:
        results = get_excerpt(query)
        print(f"Retrieved {len(results)} results:")

        for i, result in enumerate(results):
            print(f"\n{i+1}. {result[:300]}...")

    except Exception as e:
        print(f"Error during retrieval: {e}")
        import traceback
        traceback.print_exc()

def test_full_answer():
    print("\n" + "="*50)
    print("Testing complete answer generation...")

    query = "What constitutes murder under Indian law?"
    print(f"Query: {query}")

    try:
        answer = generate_answer(query)
        print(f"\nGenerated Answer:\n{answer}")

    except Exception as e:
        print(f"Error during answer generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_retrieval()
    test_full_answer()
