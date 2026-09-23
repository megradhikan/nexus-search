import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eval.harness import load_judgments_from_file, load_judgments_from_feedback, run_eval


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--feedback", action="store_true", help="Use feedback table instead of file")
    args = parser.parse_args()

    if args.feedback:
        judgments = load_judgments_from_feedback()
    else:
        path = os.path.join(os.path.dirname(__file__), "synthetic_queries.json")
        judgments = {k: v for k, v in load_judgments_from_file(path).items() if not k.startswith("_")}

    results = run_eval(judgments)

    print("┌──────────────┬───────────┬────────────┐")
    print("│ Retriever    │ MRR       │ NDCG@5     │")
    print("├──────────────┼───────────┼────────────┤")
    for name, label in [("hybrid", "Hybrid (RRF)"), ("bm25_only", "BM25 only"), ("dense_only", "Dense only")]:
        r = results[name]
        print(f"│ {label:<12} │ {r['mrr']:.3f}     │ {r['ndcg_at_5']:.3f}      │")
    print("└──────────────┴───────────┴────────────┘")


if __name__ == "__main__":
    main()
