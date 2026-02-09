import os
import json
import time
from groq import Groq
from dotenv import load_dotenv
import re
import concurrent.futures

# Load environment variables
try:
    load_dotenv(encoding="utf-8")
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")

class ReviewAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.mock_mode = False
        self.client = None
        
        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                print(f"Error configuring Groq: {e}")
                self.mock_mode = True
        else:
            print("WARNING: GROQ_API_KEY not found. Running in MOCK mode.")
            self.mock_mode = True

    def analyze_review(self, text, score=None):
        """
        Analyzes a single review text using Groq (LLaMA 3.3).
        Returns a dict with sentiment, category, urgency, and suggested_action.
        """
        if not text or len(str(text)) < 2:
             return {
                "sentiment": "Neutral",
                "category": "Unknown",
                "urgency": "Baixa",
                "suggested_action": "None"
            }

        result = None

        # --- AI ARCHITECTURE ---
        if not self.mock_mode:
            try: # Outer try for safety
                # Contexto da Nota (Ground Truth)
                score_context = f"NOTA DADA: {score}/5" if score else "NOTA: Não informada"
                
                # Prompt Engineering
                prompt = f"""
                ANALISE O TEXTO ABAIXO (PT-BR) E RETORNE UM JSON.
                
                TEXTO: "{text}"
                {score_context}
                
                REGRAS:
                1. "Mas"/"Porém" inverte o sentimento (ex: "Bom, mas atrasou" = NEGATIVO).
                2. "Não entregou"/"Extraviado" = URGÊNCIA ALTA.
                3. "Não recomendo" = NEGATIVO.
                4. Elogios ("Ótimo", "Amei") = POSITIVO.

                AÇÕES SUGERIDAS:
                - Logística -> "Verificar Rastreio"
                - Produto -> "Autorizar Troca"
                - Elogio -> "Fidelizar"

                SAÍDA JSON OBRIGATÓRIA:
                {{
                    "sentiment": "Positivo" | "Negativo" | "Neutro",
                    "category": "Logística" | "Qualidade" | "Atendimento" | "Preço" | "Outro",
                    "urgency": "Alta" | "Média" | "Baixa",
                    "suggested_action": "Ação Curta (Max 3 palavras)"
                }}
                """

                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system", 
                            "content": prompt
                        },
                        # --- FEW-SHOT EXAMPLES ---
                        {
                            "role": "user",
                            "content": 'TEXTO: "Gostei, mas veio quebrado." NOTA: 1/5'
                        },
                        {
                            "role": "assistant",
                            "content": '{"sentiment": "Negativo", "category": "Logística", "urgency": "Alta", "suggested_action": "Troca Correta Imediata"}'
                        },
                        {
                            "role": "user",
                            "content": 'TEXTO: "Não tenho o que reclamar, tudo nos conformes." NOTA: 5/5'
                        },
                        {
                            "role": "assistant",
                            "content": '{"sentiment": "Positivo", "category": "Outro", "urgency": "Baixa", "suggested_action": "Agradecer Confiança"}'
                        },
                        # --- REAL INPUT ---
                        {
                            "role": "user",
                            "content": f'TEXTO: "{text}"'
                        }
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.1,
                    max_completion_tokens=512
                )

                response_content = chat_completion.choices[0].message.content
                
                # Cleanup common AI artifacts
                clean_text = response_content.strip().replace('```json', '').replace('```', '')
                
                # Extract JSON if there's text surrounding it
                json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
                if json_match:
                    clean_text = json_match.group(0)
                    
                result = json.loads(clean_text)

            except Exception as e:
                # print(f"Error analyzing review with Groq: {e}")
                pass

        # --- FALLBACK / SAFETY NET ---
        if not result:
            result = self._rule_based_analysis(text)

        # --- SANITY CHECK LAYER (Applied to BOTH AI and Rule-Based) ---
        return self._apply_sanity_checks(result, score, text)

    def _apply_sanity_checks(self, result, score, text_raw):
        """
        Enforces business rules and 'Ground Truth' logic using the Score.
        This fixes AI hallucinations AND limitations of regex.
        """
        if not score:
            return result
            
        try:
            score_int = int(float(score))
            
            # Initialize reasoning if not present
            if "reasoning" not in result:
                result["reasoning"] = ""

            # 1. Neutral Sentiment Logic
            if result.get("sentiment") == "Neutro":
                if score_int <= 3:
                     result["sentiment"] = "Negativo"
                     result["category"] = "Qualidade"
                     result["reasoning"] += " [AUTO-CORRECT: Integrated Score Adjustment]"
                elif score_int >= 4:
                     result["sentiment"] = "Positivo"
                     result["reasoning"] += " [AUTO-CORRECT: Integrated Score Adjustment]"

            # 2. Score Polarity Enforcement
            if score_int <= 2 and result.get("sentiment") != "Negativo":
                result["sentiment"] = "Negativo"
                result["reasoning"] += " [FORCE: Critical Score]"
            elif score_int == 5 and result.get("sentiment") != "Positivo":
                result["sentiment"] = "Positivo"
                result["reasoning"] += " [FORCE: Max Score]"

            # 3. Urgency Matrix Logic
            if result.get("sentiment") == "Negativo":
                if result.get("urgency") == "Baixa":
                    result["urgency"] = "Média" # Upgrade automático
                
                # Upgrade para Alta se houver palavras-gatilho
                triggers_alta = [
                    "atraso", "não recebi", "extraviado", "quebrado", "defeito", "procon", "justiça",
                    "triste", "decepcionado", "chateado", "nunca mais", "indignado", "vergonha", "absurdo", "lixo"
                ]
                if any(t in text_raw.lower() for t in triggers_alta):
                    result["urgency"] = "Alta"
                    if "triste" in text_raw.lower() or "decepcionado" in text_raw.lower():
                        result["suggested_action"] = "Acolhimento + Solução"
                    else:
                        result["suggested_action"] = "Resolução Imediata / Estorno"

            # 4. Positive Lexicon Override
            triggers_positive = ["parabéns", "excelente", "perfeito", "amei", "recomendo", "ótimo", "maravilhoso"]
            if any(t in text_raw.lower() for t in triggers_positive):
                    if score_int >= 4: 
                        result["sentiment"] = "Positivo"
                        result["category"] = "Outro" if result.get("category") == "Unknown" else result.get("category")
                        result["suggested_action"] = "Agradecer e Fidelizar"

        except Exception as e:
            pass
            
        return result

    def _rule_based_analysis(self, text):
        """High-precision regex logic for fallback or offline mode."""
        text_lower = text.lower()
        import unicodedata
        normalized = "".join(c for c in unicodedata.normalize("NFKD", text_lower) if not unicodedata.combining(c))
        
        # Dicionário de Crimes (Negativos)
        neg_triggers = {
            "urgency_high": ["processo", "procon", "justiça", "advogado", "nunca mais", "lixo", "golpe", "roubo"],
            "logistics": ["atraso", "demorou", "nao chegou", "extraviado", "sumiu", "correios", "entrega"],
            "quality": ["quebrado", "defeito", "falha", "estragado", "pior", "horrivel", "falsificado"],
            "support": ["grosso", "mal educado", "ignora", "descaso", "atendimento", "sac"]
        }
        
        # FIX: Check for "não recomendo" explicitly
        if "nao recomendo" in normalized or "nao indico" in normalized:
             return {"sentiment": "Negativo", "category": "Qualidade", "urgency": "Média", "suggested_action": "Monitorar"}

        # 1. Check Critical Urgency
        if any(w in normalized for w in neg_triggers["urgency_high"]):
            return {"sentiment": "Negativo", "category": "Outro", "urgency": "Alta", "suggested_action": "Reter Cliente Imediatamente"}
            
        # 2. Check Logistics
        if any(w in normalized for w in neg_triggers["logistics"]):
             return {"sentiment": "Negativo", "category": "Logística", "urgency": "Alta", "suggested_action": "Verificar Rastreio"}
             
        # 3. Check General Negative
        general_bad = ["ruim", "pessimo", "terrivel", "odiei", "triste", "insatisfeito"]
        if any(w in normalized for w in general_bad):
             return {"sentiment": "Negativo", "category": "Qualidade", "urgency": "Média", "suggested_action": "Oferecer Cupom/Troca"}
             
        # 4. Positives
        positives = ["bom", "otimo", "excelente", "amei", "gostei", "recomendo", "top", "show", "perfeito"]
        if any(w in normalized for w in positives):
             return {"sentiment": "Positivo", "category": "Qualidade", "urgency": "Baixa", "suggested_action": "Agradecer Review"}

        return {"sentiment": "Neutro", "category": "Outro", "urgency": "Baixa", "suggested_action": "Monitorar"}

    def batch_analyze(self, texts):
        results = []
        for text in texts:
            results.append(self.analyze_review(text))
            if not self.mock_mode:
                time.sleep(0.5) 
        return results

    analyze_batch_concurrent = None # Deprecated/Replaced in usage but kept signature if needed
    
    def analyze_batch_with_progress(self, reviews_data, max_workers=5):
        """
        Generator that yields results as they complete for real-time progress bars.
        """
        # We need to map future back to index to maintain order? 
        # Actually for progress bar we just need "a result happened".
        # But we need final results essentially ordered or at least mapped.
        
        # To keep it simple and safe: We yield (index, result) so caller can reconstruct if needed,
        # OR caller just appends. Since we are enriching a slice, order matters if we just append?
        # Concurrent futures doesn't guarantee order. 
        # Let's yield just the result, but wait... if we just append to list in main loop, 
        # we might lose alignment with the original dataframe rows if we aren't careful.
        
        # FIX: We will return results OUT OF ORDER primarily, but we need to reorder them?
        # Or we act simpler: We are processing a list. 
        # The main.py code just appends to `enrichment_data`.
        # If `as_completed` yields out of order, the `enrichment_data` will be shuffled 
        # relative to `demo_subset`. THIS IS A BUG Risk.
        
        # Safe Strategy:
        # We handle the futures. We yield "Progress" but we collect Results internally? 
        # No, that blocks.
        
        # Better Strategy:
        # Helper returns yield.
        # But we must yield (index, result). Main.py should handle reassembly or we handle it here
        # and just yield "tick".
        
        # Let's stick to the current main.py implementation which expects `result`
        # BUT we must ensure main.py handles the order? 
        # main.py does: `results.append(result)`. This WILL be out of order if we use as_completed.
        # This breaks row alignment.
        
        # CRITICAL FIX: we must ensure results are ordered or return (index, result).
        # I will return (index, result) and update main.py to handle it?
        # OR I make this generator yield strictly in order?
        # If I yield in order, I block on earlier items.
        
        # compromise: Use as_completed to drive progress, but store results in a dict/list 
        # and re-sort at the end or yield (index, result).
        # I cannot change main.py indiscriminately.
        # Let's look at main.py again. It does `enrichment_data = results`. 
        # And assumes `enriched_subset` (which is `demo_subset`) matches row-by-row.
        # So `results` MUST be in order.
        
        # Solution:
        # We cannot use `as_completed` for yielding results individually IF we want order,
        # UNLESS we yield (i, res) and main.py puts it in `results[i]`.
        
        # Let's fix loop in main.py? I already wrote main.py to append.
        # So I will change this function to yield (index, result) tuple? No, existing code expects `r['sentiment']`.
        
        # WAIT. If I use `executor.map`, it preserves order! 
        # But `map` blocks until results are ready? No, `map` returns an iterator that yields results in order
        # as they become available? NO, it yields in order, so if item 0 is slow, it blocks item 1.
        # BUT it allows progress to update as long as items 0,1,2... complete.
        # This is acceptable for a progress bar (it might stutter but it works).
        
        # Let's use `executor.map` wrapper logic?
        # Actually, `as_completed` is better for "liveness".
        # I will change the main.py logic to handle reordering? 
        # Too many changes.
        
        # Simplest Fix for User's "Buggy Bar":
        # Just use `map`. It preserves order. It might stall if #1 is slow, but usually API calls are similar text -> similar time.
        # It's better than `as_completed` breaking the data alignment.
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Prepare args
            futures = [
                executor.submit(self.analyze_review, item['text'], score=item.get('score')) 
                for item in reviews_data
            ]
            
            # We want to yield results IN ORDER to preserve dataframe alignment
            # This means the progress bar will move as the "slowest previous task" completes.
            for future in futures:
                yield future.result()

if __name__ == "__main__":
    analyzer = ReviewAnalyzer()
    print(analyzer.analyze_review("O produto atrasou e é péssimo", score=1))
