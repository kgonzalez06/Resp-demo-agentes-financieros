# utils/ofertador_utils.py
# Utilidades para el agente ofertador de créditos

import math
from datetime import datetime

def construir_input_ofertador(contexto_analisis, tipo_producto="credito_empresarial", monto_solicitado=None):
    """
    Construye el input para el agente ofertador basado en el análisis crediticio completado
    
    Args:
        contexto_analisis (dict): Contexto con análisis financiero, scoring y buró completados
        tipo_producto (str): Tipo de producto crediticio solicitado  
        monto_solicitado (int): Monto específico solicitado por el cliente
    
    Returns:
        str: Input formateado para el agente ofertador
    """
    
    # Normalizar tipo de producto
    tipo_producto = normalizar_tipo_producto(tipo_producto)
    
    # Extraer información del análisis
    score_final = contexto_analisis.get("score", 0)
    score_interno = contexto_analisis.get("score_interno", score_final)
    score_buro = contexto_analisis.get("score_buro")
    decision = contexto_analisis.get("decision", "pending")
    
    # Información del cliente
    nombre_empresa = contexto_analisis.get("nombre_empresa", "tu empresa")
    es_cliente_existente = contexto_analisis.get("es_cliente_existente", False)
    sector = contexto_analisis.get("sector", "general")
    
    # Calcular oferta base
    try:
        oferta_calculada = calcular_oferta_crediticia(
            score_final, 
            decision, 
            tipo_producto, 
            monto_solicitado,
            es_cliente_existente,
            sector
        )
    except Exception as e:
        print(f"[ERROR] Error calculando oferta: {e}")
        # Oferta de fallback
        oferta_calculada = {
            "monto_aprobado": 500000000,  # $500M default
            "plazo_maximo_meses": 48,
            "spread_porcentaje": 6.0,
            "tasa_ea_porcentaje": 14.5,
            "cuota_mensual": 15000000,
            "garantias_requeridas": "Pagaré + Aval",
            "dias_desembolso": 5,
            "dtf_referencia": 8.5,
            "beneficios_aplicables": ["Seguro de vida incluido"]
        }
    
    input_text = f"""
GENERAR OFERTA CREDITICIA PERSONALIZADA

INFORMACIÓN DEL ANÁLISIS COMPLETADO:
- Empresa: {nombre_empresa}
- Score final: {score_final}/1000
- Score interno: {score_interno}/1000
- Score buró: {score_buro if score_buro else "No disponible"}
- Decisión crediticia: {decision}
- Cliente existente: {"Sí" if es_cliente_existente else "No"}
- Sector: {sector}

PRODUCTO SOLICITADO:
- Tipo: {tipo_producto.replace("_", " ").title()}
- Monto solicitado: {f"${monto_solicitado:,} COP" if monto_solicitado else "Por determinar"}

PARÁMETROS DE LA OFERTA CALCULADA:
{formatear_parametros_oferta(oferta_calculada)}

BENEFICIOS ESPECÍFICOS DEL CLIENTE:
{obtener_beneficios_cliente(contexto_analisis)}

CONTEXTO CONVERSACIONAL COMPLETO:
{formatear_contexto_para_oferta(contexto_analisis)}

INSTRUCCIONES:
Con base en este análisis crediticio completado y PRE-APROBADO, genera una oferta crediticia específica y atractiva.

1. Presenta la tabla de oferta con los parámetros calculados
2. Personaliza según el perfil del cliente (existente, sector, score)
3. Menciona beneficios específicos que aplican
4. Haz referencia al análisis completado para generar confianza
5. INCLUYE la pregunta de continuidad (SÍ/NO)
6. Mantén tono profesional pero entusiasta

La oferta debe reflejar que ya se completó todo el análisis crediticio y la decisión es favorable.
"""
    
    return input_text

def normalizar_tipo_producto(tipo_producto):
    """
    Normaliza los nombres de tipos de producto para consistencia
    """
    if not tipo_producto:
        return "credito_empresarial"
    
    tipo_normalizado = str(tipo_producto).lower().strip()
    
    # Remover acentos y caracteres especiales
    import re
    tipo_normalizado = re.sub(r'[áéíóú]', lambda m: {'á':'a', 'é':'e', 'í':'i', 'ó':'o', 'ú':'u'}[m.group()], tipo_normalizado)
    tipo_normalizado = re.sub(r'[^a-z0-9_]', '_', tipo_normalizado)
    
    # Mapear variaciones a nombres estándar
    mapeo_productos = {
        "credito_empresarial": "credito_empresarial",
        "empresarial": "credito_empresarial", 
        "comercial": "credito_empresarial",
        "linea_credito_rotativa": "linea_credito_rotativa",
        "linea_rotativa": "linea_credito_rotativa",
        "rotativo": "linea_credito_rotativa",
        "hipotecario_comercial": "hipotecario_comercial",
        "hipotecario": "hipotecario_comercial",
        "factoring": "factoring"
    }
    
    return mapeo_productos.get(tipo_normalizado, "credito_empresarial")

def calcular_oferta_crediticia(score, decision, tipo_producto, monto_solicitado=None, es_cliente_existente=False, sector="general"):
    """
    Calcula los parámetros específicos de la oferta crediticia
    """
    
    # Determinar spread base según score
    spread_base = calcular_spread_por_score(score)
    
    # Ajustar spread por cliente existente
    if es_cliente_existente:
        spread_base -= 0.5  # Descuento por cliente existente
    
    # Ajustar por sector
    ajuste_sectorial = obtener_ajuste_sectorial(sector)
    spread_final = spread_base + ajuste_sectorial
    
    # Calcular monto máximo aprobado
    monto_maximo = calcular_monto_maximo_por_score(score, tipo_producto)
    
    # Determinar monto de la oferta
    if monto_solicitado:
    # SIEMPRE usar lo que pidió el cliente (hasta el máximo permitido)
        monto_oferta = min(monto_solicitado, monto_maximo)
    else:
        # Solo si no especificó monto, usar máximo
        monto_oferta = monto_maximo
    
    # Determinar plazo máximo
    plazo_maximo = calcular_plazo_maximo(score, tipo_producto, sector)
    
    # Calcular tasa efectiva anual
    dtf_actual = 8.5  # DTF de referencia
    tasa_ea = dtf_actual + spread_final
    
    # Calcular cuota mensual (sistema francés)
    cuota_mensual = calcular_cuota_francesa(monto_oferta, tasa_ea, plazo_maximo)
    
    # Determinar garantías requeridas
    garantias = determinar_garantias_requeridas(score, monto_oferta)
    
    # Calcular días de desembolso
    dias_desembolso = calcular_tiempo_desembolso(score, es_cliente_existente)
    
    return {
        "monto_aprobado": int(monto_oferta),
        "plazo_maximo_meses": int(plazo_maximo),
        "spread_porcentaje": round(spread_final, 2),
        "tasa_ea_porcentaje": round(tasa_ea, 2),
        "cuota_mensual": int(cuota_mensual),
        "garantias_requeridas": garantias,
        "dias_desembolso": int(dias_desembolso),
        "dtf_referencia": dtf_actual,
        "beneficios_aplicables": calcular_beneficios_aplicables(score, es_cliente_existente, monto_oferta)
    }

def calcular_spread_por_score(score):
    """Calcula el spread sobre DTF según el score crediticio"""
    if score >= 750:
        return 4.5  # DTF + 4.5% (clientes preferenciales)
    elif score >= 650:
        return 6.0  # DTF + 6.0% (clientes establecidos)
    elif score >= 550:  
        return 7.5  # DTF + 7.5% (clientes nuevos)
    elif score >= 400:
        return 9.0  # DTF + 9.0% (clientes emergentes)
    else:
        return 12.0  # DTF + 12.0% (alto riesgo)

def obtener_ajuste_sectorial(sector):
    """Ajustes de tasa por sector económico"""
    ajustes_sectoriales = {
        "construccion": -0.3,      # Sector estable con garantías inmobiliarias
        "agricultura": 0.5,        # Mayor riesgo estacional
        "manufactura": 0.0,        # Neutral
        "comercio": 0.2,          # Riesgo medio
        "servicios": 0.1,         # Riesgo bajo-medio
        "tecnologia": 0.3,        # Sector emergente, mayor riesgo
        "transporte": 0.4,        # Riesgo operacional alto
        "salud": -0.2             # Sector estable
    }
    return ajustes_sectoriales.get(sector, 0.0)

def calcular_monto_maximo_por_score(score, tipo_producto, monto_scoring=None):
    """
    Calcula el monto máximo REALISTA según score y tipo de producto
    VERSIÓN MEJORADA - Usa información del scoring si está disponible
    """
    
    # Si el scoring ya calculó un monto, usarlo como referencia principal
    if monto_scoring and monto_scoring > 0:
        print(f"[LOG] Usando monto del scoring: ${monto_scoring:,}")
        return int(monto_scoring)
    
    # Montos base REALISTAS por score (no más fantasías de $5 billones)
    if score >= 750:
        monto_base = 3000000000  # $3,000M máximo para excelentes
    elif score >= 650:
        monto_base = 1500000000  # $1,500M para buenos
    elif score >= 550:
        monto_base = 800000000   # $800M para aceptables
    elif score >= 400:
        monto_base = 400000000   # $400M para emergentes
    else:
        monto_base = 200000000   # $200M mínimo
    
    # Ajustar por tipo de producto de forma realista
    multiplicadores = {
        "credito_empresarial": 1.0,
        "linea_credito_rotativa": 0.6,  # Menor monto por ser rotativo
        "hipotecario_comercial": 1.5,   # Mayor por garantía real (no 2.0)
        "factoring": 0.4                # Menor por ser corto plazo
    }
    
    multiplicador = multiplicadores.get(tipo_producto, 1.0)
    monto_final = int(monto_base * multiplicador)
    
    print(f"[LOG] Monto calculado - Score: {score}, Base: ${monto_base:,}, Tipo: {tipo_producto}, Final: ${monto_final:,}")
    return monto_final

def calcular_plazo_maximo(score, tipo_producto, sector):
    """Calcula el plazo máximo según score, producto y sector"""
    
    # Plazos base por producto
    plazos_base = {
        "credito_empresarial": 60,      # 5 años
        "linea_credito_rotativa": 12,   # 1 año (renovable)
        "hipotecario_comercial": 180,   # 15 años  
        "factoring": 6                  # 6 meses
    }
    
    plazo_base = plazos_base.get(tipo_producto, 60)
    
    # Ajustar por score (mejor score = mayor plazo)
    if score >= 750:
        factor_score = 1.0
    elif score >= 650:
        factor_score = 0.9
    elif score >= 550:
        factor_score = 0.8
    else:
        factor_score = 0.7
    
    # Ajustar por sector
    if sector == "agricultura":
        factor_sector = 1.2  # Plazos más largos por estacionalidad
    elif sector == "construccion":  
        factor_sector = 1.1  # Proyectos de largo plazo
    else:
        factor_sector = 1.0
    
    return min(plazo_base * factor_score * factor_sector, plazos_base[tipo_producto])

def calcular_cuota_francesa(monto, tasa_ea, plazo_meses):
    """Calcula la cuota mensual usando sistema francés (cuota fija)"""
    if plazo_meses <= 0 or tasa_ea <= 0:
        return monto / max(plazo_meses, 1)
    
    # Convertir tasa efectiva anual a mensual
    tasa_mensual = (1 + tasa_ea/100)**(1/12) - 1
    
    if tasa_mensual == 0:
        return monto / plazo_meses
    
    # Fórmula sistema francés
    cuota = monto * (tasa_mensual * (1 + tasa_mensual)**plazo_meses) / ((1 + tasa_mensual)**plazo_meses - 1)
    
    return cuota

def determinar_garantias_requeridas(score, monto):
    """Determina las garantías requeridas según score y monto"""
    
    if score >= 750 and monto <= 1000000000:  # $1.000M
        return "Pagaré"
    elif score >= 650:
        return "Pagaré + Aval"  
    elif score >= 550:
        return "Pagaré + Aval + Garantía personal"
    elif monto >= 500000000:  # Montos altos requieren garantía real
        return "Pagaré + Aval + Garantía real (hipoteca/prenda)"
    else:
        return "Pagaré + Aval + Garantía personal"

def calcular_tiempo_desembolso(score, es_cliente_existente):
    """Calcula tiempo de desembolso según perfil"""
    
    dias_base = 7  # 7 días hábiles base
    
    if score >= 750:
        dias_base -= 3  # 4 días para clientes preferenciales
    elif score >= 650:
        dias_base -= 2  # 5 días para clientes establecidos
    
    if es_cliente_existente:
        dias_base -= 1  # Un día menos para clientes existentes
    
    return max(dias_base, 2)  # Mínimo 2 días hábiles

def calcular_beneficios_aplicables(score, es_cliente_existente, monto):
    """Calcula beneficios específicos aplicables"""
    
    beneficios = []
    
    # Por score
    if score >= 750:
        beneficios.append("Tasa preferencial cliente premium")
        beneficios.append("Proceso expedito (3-4 días)")
        beneficios.append("Sin comisión de estudio")
    elif score >= 650:
        beneficios.append("Tasa preferencial cliente establecido")
        beneficios.append("Comisión de estudio con descuento 50%")
    
    # Por ser cliente existente
    if es_cliente_existente:
        beneficios.append("Descuento débito automático (-0.5%)")
        beneficios.append("Seguros preferenciales")
        beneficios.append("Proceso simplificado")
    
    # Por monto
    if monto >= 1000000000:  # $1.000M o más
        beneficios.append("Descuento por monto significativo (-0.3%)")
        beneficios.append("Asesor dedicado")
    
    # Beneficios generales
    beneficios.append("Seguro de vida incluido")
    beneficios.append("Posibilidad de prepagos sin penalidad")
    
    return beneficios

def formatear_parametros_oferta(oferta):
    """Formatea los parámetros de la oferta para el input del agente"""
    
    return f"""
- Monto máximo aprobado: ${oferta['monto_aprobado']:,} COP
- Plazo máximo: {oferta['plazo_maximo_meses']} meses ({oferta['plazo_maximo_meses']//12} años)
- Spread sobre DTF: {oferta['spread_porcentaje']}%
- Tasa efectiva anual: {oferta['tasa_ea_porcentaje']}% E.A.
- Cuota mensual estimada: ${oferta['cuota_mensual']:,} COP
- Garantías requeridas: {oferta['garantias_requeridas']}
- Tiempo de desembolso: {oferta['dias_desembolso']} días hábiles
- DTF de referencia: {oferta['dtf_referencia']}% E.A.
"""

def obtener_beneficios_cliente(contexto):
    """Obtiene beneficios específicos del cliente basados en su perfil"""
    
    beneficios = []
    
    if contexto.get("es_cliente_existente"):
        tiempo_relacion = contexto.get("tiempo_relacion_anos", 0)
        if tiempo_relacion >= 5:
            beneficios.append("Cliente premium con más de 5 años de relación")
        elif tiempo_relacion >= 2:
            beneficios.append("Cliente establecido con relación sólida")
        
        beneficios.append("Acceso a tasas preferenciales por ser cliente existente")
        beneficios.append("Proceso simplificado y ágil")
    
    score = contexto.get("score", 0)
    if score >= 750:
        beneficios.append("Perfil crediticio excelente - mejores condiciones disponibles")
    elif score >= 650:
        beneficios.append("Buen perfil crediticio - condiciones favorables")
    
    clasificacion_riesgo = contexto.get("clasificacion_riesgo", "")
    if clasificacion_riesgo in ["A1", "A2"]:
        beneficios.append("Clasificación de riesgo óptima")
    
    return beneficios

def formatear_contexto_para_oferta(contexto):
    """Formatea el contexto completo para la oferta"""
    
    contexto_texto = f"""
- Empresa: {contexto.get('nombre_empresa', 'No especificada')}
- Sector: {contexto.get('sector', 'General')}
- Cliente existente: {'Sí' if contexto.get('es_cliente_existente') else 'No'}
- Análisis completado: {'Sí' if contexto.get('analysis_completed') else 'No'}
- Etapa: {contexto.get('stage', 'inicial')}
"""
    
    if contexto.get('financial_ratios'):
        contexto_texto += "- Análisis financiero: Completado\n"
    
    if contexto.get('scoring_details'):
        contexto_texto += "- Scoring interno: Completado\n"
    
    if contexto.get('buro_details'):
        contexto_texto += "- Análisis de buró: Completado\n"
    
    return contexto_texto

def procesar_respuesta_continuidad(respuesta_usuario):
    """
    Procesa la respuesta del usuario sobre continuar con la oferta
    """
    respuesta_normalizada = respuesta_usuario.lower().strip()
    
    # Palabras que indican SÍ
    palabras_si = ["sí", "si", "yes", "dale", "perfecto", "excelente", "continuo", "continuar", 
                   "acepto", "de acuerdo", "okay", "ok", "bueno", "claro", "afirmativo"]
    
    # Palabras que indican NO
    palabras_no = ["no", "not", "nope", "negativo", "paso", "ahora no", "después", 
                   "lo pensaré", "más tarde", "rechazar", "declino"]
    
    # Detectar respuesta afirmativa
    if any(palabra in respuesta_normalizada for palabra in palabras_si):
        return {
            "decision": "SI",
            "tipo_respuesta": "afirmativa",
            "siguiente_accion": "contacto_asesor"
        }
    
    # Detectar respuesta negativa
    elif any(palabra in respuesta_normalizada for palabra in palabras_no):
        return {
            "decision": "NO", 
            "tipo_respuesta": "negativa",
            "siguiente_accion": "despedida_cordial"
        }
    
    # Respuesta ambigua
    else:
        return {
            "decision": "UNCLEAR",
            "tipo_respuesta": "ambigua", 
            "siguiente_accion": "clarificar_intencion"
        }

def generar_mensaje_confirmacion_si():
    """Genera mensaje de confirmación cuando el cliente dice SÍ"""
    return """
¡Excelente decisión! 🎉

Tu solicitud de crédito está oficialmente en proceso. Estos son los próximos pasos:

📞 **Contacto del Asesor**: Un asesor comercial especializado te contactará en las próximas 24 horas
📋 **Documentación Final**: Te ayudará con cualquier documento adicional que pueda necesitarse  
⚡ **Proceso Ágil**: Como ya completaste la pre-aprobación, el proceso será muy rápido
💰 **Desembolso**: Una vez formalizada la documentación, el desembolso se realizará según los tiempos ofrecidos

**Importante**: Mantén esta oferta a la mano cuando te contacte el asesor. También puedes llamarnos si tienes alguna pregunta urgente.

¡Muchas gracias por confiar en nosotros para el crecimiento de tu empresa! 🏦✨
"""

def generar_mensaje_despedida_no():
    """Genera mensaje de despedida cordial cuando el cliente dice NO"""
    return """
¡Perfecto, entiendo completamente! 😊

Quiero que sepas que:

⏰ **Esta oferta estará disponible por 30 días** por si cambias de opinión
📞 **Puedes contactarnos cuando quieras** para reactivar tu solicitud
🔄 **Sin compromiso**: No hay ninguna obligación de tu parte

Valoramos mucho que hayas considerado nuestros servicios para el crecimiento de tu empresa. Estaremos aquí cuando nos necesites.

Si en el futuro tienes otros requerimientos financieros, ¡no dudes en consultarnos!

¡Que tengas un excelente día! 🌟
"""