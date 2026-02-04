
import sys
import os
import time

# Add root to path so we can import as if we are in the root
sys.path.append(os.getcwd())

from pipeline.ai_enricher import ReviewAnalyzer

def test_parallel():
    analyzer = ReviewAnalyzer()
    print(f"Analyzer Mode: {'Mock' if analyzer.mock_mode else 'Live AI'}")
    
    # Create dummy data
    texts = [
        {"text": "Produto muito bom, chegou rapido.", "score": 5},
        {"text": "Atrasou e veio quebrado.", "score": 1},
        {"text": "Nao gostei, atendimento ruim.", "score": 2},
        {"text": "Regular, podia ser melhor.", "score": 3},
        {"text": "Excelente qualidade!", "score": 5}
    ]
    
    # Duplicate to simulate load
    load = texts * 2 # 10 items
    
    print(f"Testing parallel processing with {len(load)} items...")
    start = time.time()
    results = analyzer.analyze_batch_concurrent(load, max_workers=5)
    end = time.time()
    
    print(f"Time taken: {end - start:.2f}s")
    print(f"Results count: {len(results)}")
    
    for i, res in enumerate(results[:3]):
        print(f"[{i}] {res.get('sentiment')} - {res.get('urgency')}")

if __name__ == "__main__":
    test_parallel()
