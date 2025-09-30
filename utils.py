import json

def clean_markdown(text: str) -> str:
    """
    Limpia texto de markdown y bloques de código
    """
    if not text:
        return ""
    
    t = text.strip()
    if t.startswith("```json"):
        t = t.replace("```json", "").replace("```", "").strip()
    elif t.startswith("```"):
        t = t.replace("```", "").strip()
    return t

def parse_json(text: str, fallback=None):
    """
    Parsea JSON de forma segura con fallback
    """
    try:
        cleaned_text = clean_markdown(text)
        if not cleaned_text:
            return fallback
        return json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Text was: {text[:200]}...")
        return fallback
    except Exception as e:
        print(f"Unexpected error in parse_json: {e}")
        return fallback

def extract_score_from_scoring(scoring_result):
    """
    Extrae el score del resultado del agente scoring
    """
    if not scoring_result:
        return 0
    
    # Intentar diferentes formas de obtener el score
    if isinstance(scoring_result, dict):
        return scoring_result.get("score", 0)
    elif isinstance(scoring_result, str):
        try:
            parsed = json.loads(scoring_result)
            return parsed.get("score", 0)
        except:
            return 0
    
    return 0

def extract_decision_from_scoring(scoring_result):
    """
    Extrae la decisión del resultado del agente scoring
    """
    if not scoring_result:
        return "pending"
    
    if isinstance(scoring_result, dict):
        decision = scoring_result.get("decision", "pending")
    elif isinstance(scoring_result, str):
        try:
            parsed = json.loads(scoring_result)
            decision = parsed.get("decision", "pending")
        except:
            decision = "pending"
    else:
        decision = "pending"
    
    return str(decision)