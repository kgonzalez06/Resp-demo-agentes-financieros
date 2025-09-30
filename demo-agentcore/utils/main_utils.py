# utils/main_utils.py
# Funciones principales de utilidades (migradas del utils.py original)

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
    Parsea JSON de forma segura con fallback, incluyendo extracción de JSON de texto mixto
    """
    try:
        if not text:
            return fallback
            
        cleaned_text = clean_markdown(text)
        
        # Intentar parsear directamente
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            pass
        
        # Intentar extraer JSON del texto si está mezclado
        lines = cleaned_text.strip().split('\n')
        
        # Buscar líneas que parezcan JSON
        for line in lines:
            line = line.strip()
            if line.startswith('{') and line.endswith('}'):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
        
        # Buscar bloques JSON multilinea
        json_start = -1
        brace_count = 0
        
        for i, char in enumerate(cleaned_text):
            if char == '{':
                if json_start == -1:
                    json_start = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and json_start != -1:
                    json_candidate = cleaned_text[json_start:i+1]
                    try:
                        return json.loads(json_candidate)
                    except json.JSONDecodeError:
                        json_start = -1
                        continue
        
        print(f"[WARNING] No se pudo extraer JSON válido de: {text[:200]}...")
        return fallback
        
    except Exception as e:
        print(f"[ERROR] Error inesperado en parse_json: {e}")
        print(f"[ERROR] Texto era: {text[:200]}...")
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

def formatear_explicacion_dual_analisis(score_interno, score_buro, decision_final, es_cliente_existente=False):
    """
    Formatea explicación comprensible del análisis dual sin scores técnicos
    Para simulación - no menciona entidades reales específicas
    """
    
    # Traducir score interno a lenguaje natural
    if score_interno >= 750:
        desc_interno = "indicadores financieros excelentes con muy buena capacidad de pago"
    elif score_interno >= 650:
        desc_interno = "indicadores financieros sólidos y capacidad de pago adecuada"
    elif score_interno >= 550:
        desc_interno = "indicadores financieros aceptables"
    else:
        desc_interno = "indicadores financieros que requieren fortalecimiento"
    
    # Traducir score buró a lenguaje natural (SIN mencionar DataCrédito específicamente)
    if score_buro:
        if score_buro >= 700:
            desc_buro = "excelente comportamiento crediticio en el sistema financiero"
        elif score_buro >= 650:
            desc_buro = "buen historial crediticio sin mayores incidencias"
        elif score_buro >= 600:
            desc_buro = "comportamiento crediticio aceptable"
        else:
            desc_buro = "historial crediticio con algunas observaciones"
    else:
        desc_buro = "empresa nueva sin historial crediticio previo (no es negativo)"
    
    # Construir explicación
    explicacion = f"""📊 **Análisis Interno**: Basado en tus estados financieros, tu empresa presenta {desc_interno}.

🏦 **Consulta de Centrales de Riesgo**: Según tu historial en el sistema financiero colombiano, {desc_buro}."""
    
    if es_cliente_existente:
        explicacion += "\n\n⭐ **Ventaja Adicional**: Como cliente existente, tienes condiciones preferenciales."
    
    # Explicar decisión final
    if decision_final in ["APROBADO", "approved"]:
        explicacion += "\n\n✅ **Resultado Final**: ¡APROBADO! La combinación de ambos análisis respalda tu solicitud."
    elif decision_final == "CONDICIONAL":
        explicacion += "\n\n⚠️ **Resultado Final**: APROBADO con condiciones especiales para mitigar riesgos identificados."
    else:
        explicacion += "\n\n❌ **Resultado Final**: No aprobado en este momento. Te explicamos las razones y alternativas."
    
    return explicacion


def validar_coherencia_solicitud(monto_solicitado, score_interno, sector, es_cliente_existente=False):
    """
    Valida que la solicitud sea coherente con el perfil crediticio
    Usada en: handle_verification_flow y handle_financial_flow para alertas tempranas
    """
    
    if not monto_solicitado or not score_interno:
        return {"es_coherente": True, "observaciones": "Información insuficiente"}
    
    # Calcular monto máximo esperado según score
    if score_interno >= 750:
        monto_max_esperado = 2500000000  # $2,500M
    elif score_interno >= 650:
        monto_max_esperado = 1500000000  # $1,500M  
    elif score_interno >= 550:
        monto_max_esperado = 800000000   # $800M
    elif score_interno >= 400:
        monto_max_esperado = 400000000   # $400M
    else:
        monto_max_esperado = 200000000   # $200M
    
    # Ajustar por sector
    multiplicadores_sector = {
        "construccion": 1.3,    # Mayor por garantías inmobiliarias
        "manufactura": 1.0,     # Estándar
        "comercio": 0.8,        # Menor por mayor volatilidad  
        "servicios": 0.9,       # Menor respaldo tangible
        "tecnologia": 0.7,      # Mayor incertidumbre
        "agricultura": 1.1      # Activos tangibles pero estacional
    }
    
    multiplicador = multiplicadores_sector.get(sector.lower(), 1.0)
    monto_max_ajustado = int(monto_max_esperado * multiplicador)
    
    # Beneficio por cliente existente
    if es_cliente_existente:
        monto_max_ajustado = int(monto_max_ajustado * 1.2)  # 20% más
    
    # Validar coherencia
    ratio_solicitud = monto_solicitado / monto_max_ajustado
    
    if ratio_solicitud <= 1.0:
        return {
            "es_coherente": True,
            "ratio": ratio_solicitud,
            "observaciones": "Solicitud dentro del rango esperado"
        }
    elif ratio_solicitud <= 1.5:
        return {
            "es_coherente": True,
            "ratio": ratio_solicitud,
            "observaciones": f"Solicitud alta pero posible. Revisar capacidad de pago detalladamente.",
            "monto_sugerido": monto_max_ajustado,
            "diferencia": monto_solicitado - monto_max_ajustado
        }
    else:
        return {
            "es_coherente": False,
            "ratio": ratio_solicitud, 
            "razon": f"Monto solicitado (${monto_solicitado//1000000}M) muy alto para el perfil crediticio",
            "monto_sugerido": monto_max_ajustado,
            "diferencia": monto_solicitado - monto_max_ajustado,
            "recomendacion": "Considerar solicitud por etapas o mejora previa del perfil crediticio"
        }