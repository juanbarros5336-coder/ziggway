
import sys
import os
import pandas as pd

# Add the current directory to path so we can import pipeline
sys.path.append(os.getcwd())

from pipeline.ai_enricher import ReviewAnalyzer

def run_tests():
    analyzer = ReviewAnalyzer()
    print(f"Analyzer Mode (Mock?): {analyzer.mock_mode}")

    test_cases = [
        # 1. Adversative (The "But" Rule)
        {"text": "A entrega foi rápida, mas o produto é péssimo.", "score": 1, "desc": "Adversative w/ Low Score"},
        {"text": "Demorou um pouco, mas valeu a pena pela qualidade.", "score": 5, "desc": "Adversative w/ High Score"},

        # 2. Frustration Modality
        {"text": "Era para ser um presente de aniversário.", "score": 1, "desc": "Frustration (Excectation)"},
        {"text": "Fiquei esperando e nada.", "score": 1, "desc": "Frustration (Waiting)"},

        # 3. Urgency Triggers
        {"text": "Meu pedido está atrasado há 10 dias!", "score": 1, "desc": "Urgency (Delay)"},
        {"text": "Estou muito triste com essa compra.", "score": 2, "desc": "Urgency (Emotional - Sad)"},
        {"text": "Produto chegou quebrado.", "score": 1, "desc": "Urgency (Broken)"},

        # 4. Neutral Traps (Score Dictatorship)
        {"text": "O produto é ok.", "score": 1, "desc": "Neutral Text / Low Score (Should be Negative)"},
        {"text": "Normal.", "score": 5, "desc": "Neutral Text / High Score (Should be Positive)"},

        # 5. Positive Override
        {"text": "Parabéns, excelente atendimento.", "score": 5, "desc": "Positive Keywords"},
        
        # 6. Negation Complex
        {"text": "Não tenho do que reclamar.", "score": 5, "desc": "Complex Negation (Positive)"},
        {"text": "Não recomendo a ninguém.", "score": 1, "desc": "Complex Negation (Negative)"}
    ]

    print("\n--- RUNNING AI ACCURACY VERIFICATION ---\n")
    
    for case in test_cases:
        print(f"Testing: [{case['desc']}]")
        print(f"Input: '{case['text']}' | Score: {case['score']}")
        
        # Run analysis
        result = analyzer.analyze_review(case['text'], score=case['score'])
        
        # Print Result
        print(f"Output: Sentiment={result.get('sentiment')} | Urgency={result.get('urgency')} | Category={result.get('category')}")
        print(f"Action: {result.get('suggested_action')}")
        if "reasoning" in result:
             print(f"Reasoning: {result.get('reasoning')}")
        print("-" * 50)

if __name__ == "__main__":
    run_tests()
