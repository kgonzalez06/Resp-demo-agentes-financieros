# utils/buro_utils.py
# Utilidades para el agente de buró de crédito

import json
from datetime import datetime

# Importar desde la estructura de paquetes
try:
    from ..data.buro_simulado import consultar_buro, interpretar_score_buro, obtener_resumen_buro
except ImportError:
    try:
        from data.buro_simulado import consultar_buro, interpretar_score_buro, obtener_resumen_buro
    except ImportError:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from data.buro_simulado import consultar_buro, interpretar_score_buro, obtener_resumen_buro

def construir_input_buro(nit, contexto_conversacion=None):
    """
    Construye el input para el agente de buró consultando las centrales de riesgo
    
    Args:
        nit (str): NIT de la empresa a consultar
        contexto_conversacion (dict): Contexto previo de la conversación
    
    Returns:
        str: Input formateado para el agente de buró
    """
    
    # Consultar buró de crédito
    reporte_buro = consultar_buro(nit)
    
    if not reporte_buro:
        return construir_input_sin_historial(nit, contexto_conversacion)
    
    # Construir input detallado con el reporte
    input_text = f"""
CONSULTA A CENTRALES DE RIESGO COLOMBIANAS

INFORMACIÓN BÁSICA:
- NIT consultado: {nit}
- Entidad consultora: {reporte_buro.get('entidad_consultora', 'DataCrédito Experian')}
- Fecha consulta: {reporte_buro.get('fecha_consulta', datetime.now().strftime('%Y-%m-%d'))}
- Última actualización: {reporte_buro.get('ultima_actualizacion', 'N/A')}

SCORE DE BURÓ:
- Score externo: {reporte_buro.get('score_externo', 'Sin información')}
- Categoría de riesgo: {reporte_buro.get('categoria_riesgo', 'Sin clasificar')}
- Calificación: {reporte_buro.get('calificacion', 'NR')}

COMPORTAMIENTO CREDITICIO:
- Comportamiento últimos 12 meses: {reporte_buro.get('comportamiento_12m', 'Sin información')}
- Comportamiento últimos 24 meses: {reporte_buro.get('comportamiento_24m', 'Sin información')}
- Historial de pagos: {reporte_buro.get('historial_pagos', 'Sin información')}
- Experiencia crediticia: {reporte_buro.get('experiencia_crediticia', 'Sin información')}

ENDEUDAMIENTO SISTEMA FINANCIERO:
{formatear_deudas_sistema(reporte_buro.get('deudas_sistema_financiero', {}))}

REPORTES NEGATIVOS:
{formatear_reportes_negativos(reporte_buro.get('reportes_negativos', []))}

PROCESOS LEGALES:
{formatear_procesos_legales(reporte_buro)}

INFORMACIÓN SECTORIAL:
- Score industria: {reporte_buro.get('score_industria', 'Sin referencia')}

OBSERVACIONES DEL BURÓ:
{reporte_buro.get('observaciones_buro', 'Sin observaciones')}

RECOMENDACIÓN INICIAL DEL BURÓ:
{reporte_buro.get('recomendacion_buro', 'Sin recomendación')}

ALERTAS IDENTIFICADAS:
{formatear_alertas(reporte_buro.get('alertas', []))}

CONTEXTO CONVERSACIONAL:
{formatear_contexto_buro(contexto_conversacion)}

INSTRUCCIONES:
Analiza completamente este reporte de buró de crédito y genera tu evaluación en formato JSON.
Considera todos los factores: score, comportamiento, deudas, reportes negativos, procesos legales.
Sé riguroso pero justo en tu recomendación.
"""
    
    return input_text

def construir_input_sin_historial(nit, contexto_conversacion):
    """
    Construye input para empresas sin historial en centrales de riesgo
    """
    input_text = f"""
CONSULTA A CENTRALES DE RIESGO COLOMBIANAS

INFORMACIÓN BÁSICA:
- NIT consultado: {nit}
- Resultado: Sin información en centrales de riesgo
- Entidad consultora: DataCrédito Experian
- Fecha consulta: {datetime.now().strftime('%Y-%m-%d')}

HALLAZGOS:
- Score externo: Sin información
- Experiencia crediticia: Sin historial reportado
- Deudas sistema financiero: Sin registros
- Reportes negativos: Ninguno
- Procesos legales: Ninguno

CONTEXTO CONVERSACIONAL:
{formatear_contexto_buro(contexto_conversacion)}

SITUACIÓN:
Esta empresa no tiene historial crediticio en las centrales de riesgo colombianas.
Esto puede indicar:
1. Empresa nueva sin experiencia crediticia
2. Empresa que maneja solo productos básicos (cuentas corrientes, ahorros)
3. Financiamiento exclusivamente con capital propio

INSTRUCCIONES:
Genera una evaluación para una empresa SIN historial crediticio.
La ausencia de información no es negativa, pero limita la evaluación.
Recomienda análisis basado en estados financieros y garantías.
"""
    
    return input_text

def formatear_deudas_sistema(deudas_info):
    """
    Formatea la información de deudas en el sistema financiero
    """
    if not deudas_info or deudas_info.get('total_deudas', 0) == 0:
        return "- Sin deudas reportadas en sistema financiero"
    
    total_deudas = deudas_info.get('total_deudas', 0)
    num_entidades = deudas_info.get('numero_entidades', 0)
    detalle = deudas_info.get('detalle_por_entidad', [])
    
    texto = f"- Total deudas sistema: ${total_deudas:,}\n"
    texto += f"- Número de entidades: {num_entidades}\n"
    
    if detalle:
        texto += "- Detalle por entidad:\n"
        for deuda in detalle:
            banco = deuda.get('banco', 'Entidad no identificada')
            monto = deuda.get('monto', 0)
            tipo = deuda.get('tipo', 'No especificado')
            comportamiento = deuda.get('comportamiento', 'Sin información')
            texto += f"  • {banco}: ${monto:,} ({tipo}) - {comportamiento}\n"
    
    return texto

def formatear_reportes_negativos(reportes):
    """
    Formatea los reportes negativos
    """
    if not reportes:
        return "- Sin reportes negativos"
    
    texto = f"- Total reportes negativos: {len(reportes)}\n"
    for reporte in reportes:
        fecha = reporte.get('fecha', 'Sin fecha')
        entidad = reporte.get('entidad', 'Sin entidad')
        tipo = reporte.get('tipo', 'Sin tipo')
        monto = reporte.get('monto', 0)
        estado = reporte.get('estado', 'Sin estado')
        observacion = reporte.get('observacion', '')
        
        texto += f"  • {fecha} - {entidad}: {tipo} por ${monto:,}\n"
        texto += f"    Estado: {estado}\n"
        if observacion:
            texto += f"    Observación: {observacion}\n"
    
    return texto

def formatear_procesos_legales(reporte_buro):
    """
    Formatea información de procesos legales
    """
    demandas = reporte_buro.get('demandas_ejecutivas', [])
    embargos = reporte_buro.get('embargos_vigentes', [])
    concordatos = reporte_buro.get('concordatos', [])
    
    if not demandas and not embargos and not concordatos:
        return "- Sin procesos legales vigentes"
    
    texto = ""
    
    if demandas:
        texto += f"- Demandas ejecutivas: {len(demandas)}\n"
        for demanda in demandas:
            fecha = demanda.get('fecha', 'Sin fecha')
            entidad = demanda.get('entidad', 'Sin entidad')
            monto = demanda.get('monto', 0)
            estado = demanda.get('estado', 'Sin estado')
            juzgado = demanda.get('juzgado', 'Sin juzgado')
            texto += f"  • {fecha} - {entidad}: ${monto:,} ({estado}) - {juzgado}\n"
    
    if embargos:
        texto += f"- Embargos vigentes: {len(embargos)}\n"
        for embargo in embargos:
            fecha = embargo.get('fecha', 'Sin fecha')
            tipo = embargo.get('tipo', 'Sin tipo')
            monto = embargo.get('monto', 0)
            bien = embargo.get('bien', 'Sin especificar')
            texto += f"  • {fecha}: {tipo} por ${monto:,} sobre {bien}\n"
    
    if concordatos:
        texto += f"- Concordatos: {len(concordatos)}\n"
        for concordato in concordatos:
            texto += f"  • {concordato}\n"
    
    return texto

def formatear_alertas(alertas):
    """
    Formatea las alertas identificadas
    """
    if not alertas:
        return "- Sin alertas identificadas"
    
    texto = f"- Total alertas: {len(alertas)}\n"
    for i, alerta in enumerate(alertas, 1):
        texto += f"  {i}. {alerta}\n"
    
    return texto

def formatear_contexto_buro(contexto):
    """
    Formatea el contexto conversacional para el análisis de buró
    """
    if not contexto:
        return "- Primera consulta de la empresa"
    
    texto = "Información contextual:\n"
    
    if contexto.get('nombre_empresa'):
        texto += f"- Empresa: {contexto['nombre_empresa']}\n"
    
    if contexto.get('sector'):
        texto += f"- Sector: {contexto['sector']}\n"
    
    if contexto.get('es_cliente_existente'):
        texto += f"- Cliente interno: {'Sí' if contexto['es_cliente_existente'] else 'No'}\n"
        
        if contexto.get('score_interno'):
            texto += f"- Score interno: {contexto['score_interno']}/1000\n"
    
    if contexto.get('monto_solicitado'):
        texto += f"- Monto solicitado: ${contexto['monto_solicitado']:,}\n"
    
    return texto

def procesar_respuesta_buro(respuesta_agente, nit):
    """
    Procesa la respuesta del agente de buró y extrae información estructurada
    """
    try:
        # Limpiar la respuesta de markdown si existe
        respuesta_limpia = respuesta_agente.replace('```json', '').replace('```', '').strip()
        
        # Parsear JSON
        resultado_buro = json.loads(respuesta_limpia)
        
        # Validar campos requeridos
        campos_requeridos = [
            'score_buro', 'interpretacion_score', 'comportamiento_general',
            'recomendacion_buro', 'impacto_decision'
        ]
        
        for campo in campos_requeridos:
            if campo not in resultado_buro:
                resultado_buro[campo] = f"No disponible - {campo}"
        
        # Agregar metadata
        resultado_buro['nit_consultado'] = nit
        resultado_buro['fecha_analisis'] = datetime.now().isoformat()
        resultado_buro['fuente_analisis'] = "Agente Buró CreditBot AI"
        
        return resultado_buro
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] Error parseando JSON del agente buró: {e}")
        print(f"[ERROR] Respuesta recibida: {respuesta_agente[:200]}...")
        
        # Respuesta de fallback
        return {
            "score_buro": None,
            "interpretacion_score": "Error en análisis de buró",
            "comportamiento_general": "No se pudo analizar",
            "deudas_sistema": {
                "total_deudas": 0,
                "numero_entidades": 0,
                "nivel_endeudamiento": "desconocido"
            },
            "alertas_identificadas": ["Error en procesamiento"],
            "fortalezas": [],
            "recomendacion_buro": "OBSERVAR",
            "justificacion": "Error en análisis, requiere revisión manual",
            "impacto_decision": {
                "peso_positivo": 0,
                "peso_negativo": 50,
                "factor_determinante": "Error en análisis de buró"
            },
            "observaciones": f"Error procesando respuesta del agente: {str(e)}",
            "nit_consultado": nit,
            "fecha_analisis": datetime.now().isoformat(),
            "fuente_analisis": "Error - CreditBot AI"
        }
    
    except Exception as e:
        print(f"[ERROR] Error inesperado procesando buró: {e}")
        return procesar_respuesta_buro("Error general", nit)
    
def generar_contexto_decision(score_interno, score_buro, recomendacion_buro, decision_final):
    """
    Genera contexto explicativo de por qué se tomó la decisión
    """
    if decision_final == "APROBADO":
        return f"Perfiles excelentes: interno {score_interno}, buró {score_buro}"
    elif decision_final == "CONDICIONAL":
        if score_buro and score_buro < 650:
            return f"Score interno sólido ({score_interno}) compensa score buró ({score_buro}). Recomendación buró: {recomendacion_buro}"
        else:
            return f"Perfiles buenos que ameritan aprobación con condiciones"
    else:
        return f"Perfiles por debajo de umbrales mínimos o alertas críticas"

def combinar_analisis_interno_buro(score_interno, datos_buro, clasificacion_interna=None):
    """
    Combina el análisis interno con el de buró para una evaluación integral
    VERSIÓN MEJORADA con lógica más equilibrada
    """
    
    # Pesos para la decisión final (ajustados)
    peso_interno = 65  # 65% score interno (más peso al análisis financiero)
    peso_buro = 35     # 35% score de buró
    
    score_buro = datos_buro.get('score_buro')
    recomendacion_buro = datos_buro.get('recomendacion_buro', 'OBSERVAR')
    
    # Calcular score combinado
    if score_interno and score_buro:
        score_combinado = (score_interno * peso_interno + score_buro * peso_buro) / 100
    else:
        score_combinado = score_interno if score_interno else score_buro
    
    # Determinar decisión combinada con nueva lógica
    decision_final = determinar_decision_combinada(
        score_interno, score_buro, recomendacion_buro, clasificacion_interna
    )
    
    # Agregar contexto de la decisión
    contexto_decision = generar_contexto_decision(
        score_interno, score_buro, recomendacion_buro, decision_final
    )
    
    return {
        "score_combinado": round(score_combinado) if score_combinado else None,
        "score_interno": score_interno,
        "score_buro": score_buro,
        "peso_interno": peso_interno,
        "peso_buro": peso_buro,
        "decision_final": decision_final,
        "recomendacion_buro": recomendacion_buro,
        "contexto_decision": contexto_decision,
        "factores_determinantes": extraer_factores_determinantes(datos_buro),
        "alertas_criticas": datos_buro.get('alertas_identificadas', []),
        "fortalezas_identificadas": datos_buro.get('fortalezas', [])
    }

def determinar_decision_combinada(score_interno, score_buro, recomendacion_buro, clasificacion_interna):
    """
    Política crediticia balanceada: considera tanto scores como recomendaciones
    """
    
    # CONTROL 1: Rechazos automáticos por clasificación interna crítica
    if clasificacion_interna and "RECHAZADO" in str(clasificacion_interna).upper():
        return "RECHAZADO"
    
    # CONTROL 2: Rechazos automáticos por buró crítico
    if recomendacion_buro in ["RECHAZAR", "DESFAVORABLE"]:
        return "RECHAZADO"
    
    # CONTROL 3: Si falta score interno, rechazar (crítico para análisis)
    if not score_interno:
        return "RECHAZADO"  
    
    # CONTROL 4: Sin score de buró pero recomendación favorable = usar solo interno
    if not score_buro:
        if score_interno >= 700:
            return "CONDICIONAL"  # Sin historial = condicional, no aprobado
        elif score_interno >= 550:
            return "CONDICIONAL" 
        else:
            return "RECHAZADO"
    
    # LÓGICA PRINCIPAL: Combinación equilibrada
    
    # APROBADOS: Perfiles excelentes
    if score_interno >= 700 and score_buro >= 700:
        return "APROBADO"
    
    # CONDICIONALES: Buenos perfiles (rango más amplio)
    elif score_interno >= 700 and score_buro >= 600:  # Interno excelente + buró aceptable
        return "CONDICIONAL"
    elif score_interno >= 650 and score_buro >= 650:  # Ambos buenos
        return "CONDICIONAL"
    elif score_interno >= 600 and score_buro >= 600:  # Ambos aceptables
        # Verificar si hay recomendación favorable a pesar del score
        if recomendacion_buro in ["FAVORABLE", "FAVORABLE CON OBSERVACIONES", "OBSERVAR"]:
            return "CONDICIONAL"
        else:
            return "RECHAZADO"
    
    # CASOS ESPECIALES: Considerar recomendación de buró
    elif score_interno >= 550:  # Score interno mínimo aceptable
        # Si buró recomienda favorable a pesar de score bajo = considerar contexto
        if recomendacion_buro in ["FAVORABLE", "FAVORABLE CON OBSERVACIONES"]:
            return "CONDICIONAL"  # Dar oportunidad con condiciones
        else:
            return "RECHAZADO"
    
    # TODO LO DEMÁS: RECHAZADO
    else:
        return "RECHAZADO"

def extraer_factores_determinantes(datos_buro):
    """
    Extrae los factores más relevantes del análisis de buró
    """
    factores = []
    
    impacto = datos_buro.get('impacto_decision', {})
    factor_determinante = impacto.get('factor_determinante', '')
    if factor_determinante:
        factores.append(factor_determinante)
    
    alertas = datos_buro.get('alertas_identificadas', [])
    if alertas:
        factores.extend(alertas[:2])  # Máximo 2 alertas principales
    
    return factores[:3]  # Máximo 3 factores