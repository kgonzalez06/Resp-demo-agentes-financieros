# entrypoint.py - VERSIÓN FINAL COMPLETA CON TODOS LOS AGENTES
import json
from datetime import datetime
from bedrock_agentcore import BedrockAgentCoreApp
from agents.orquestador import orquestador
from agents.financiero import financiero
from agents.scoring import scoring
from agents.conversacional import conversacional
from agents.verificador import verificador
from agents.buro import buro
from agents.ofertador import ofertador
from utils.main_utils import clean_markdown, parse_json, validar_coherencia_solicitud
from utils.verificador_utils import (
    construir_input_verificador, 
    extraer_nit_de_mensaje, 
    validar_formato_nit,
    procesar_respuesta_verificador,
    extraer_info_credito_del_mensaje
)
from utils.buro_utils import (
    construir_input_buro,
    procesar_respuesta_buro,
    combinar_analisis_interno_buro
)
from utils.ofertador_utils import (
    construir_input_ofertador,
    procesar_respuesta_continuidad,
    generar_mensaje_confirmacion_si,
    generar_mensaje_despedida_no
)

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload):
    """
    Entrypoint que SIEMPRE pasa por el orquestador primero
    """
    try:
        interaction_type = payload.get("type", "message")
        user_id = payload.get("user_id", f"user_{hash(str(payload)) % 10000}")
        
        print(f"[LOG] Iniciando procesamiento - Tipo: {interaction_type}, Usuario: {user_id}")
        
        # PASO 1: SIEMPRE llamar al orquestador primero
        orchestrator_input = build_orchestrator_input(payload)
        
        print(f"[LOG] Llamando a orquestador...")
        orq_result = orquestador(orchestrator_input)
        orq_output = orq_result.message['content'][0]['text']
        
        print(f"[LOG] Orquestador respondió: {orq_output[:100]}...")
        
        # Detectar si es decisión de routing o resumen final
        if is_routing_decision(orq_output):
            # Es una decisión de routing
            orq_decision = parse_json(clean_markdown(orq_output), {"next_agent": "end"})
            next_agent = orq_decision.get("next_agent", "end")
            
            print(f"[LOG] Decisión de routing: {next_agent}")
            
            return execute_agent_flow(payload, next_agent, user_id)
        else:
            # Es un resumen final, devolverlo directamente
            return {
                "success": True,
                "message": clean_markdown(orq_output),
                "conversation_mode": "dynamic",
                "user_id": user_id
            }
            
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return {"success": False, "error": str(e)}


def build_orchestrator_input(payload):
    """
    Construye input para el orquestador según el tipo de solicitud
    """
    interaction_type = payload.get("type", "message")
    
    if interaction_type == "message":
        # CONVERSACIÓN
        message = payload.get("message", "")
        context = payload.get("conversation_context", {})
        
        # Detectar si hay un NIT en el mensaje
        nit_detectado = extraer_nit_de_mensaje(message)
        nit_valido = False
        if nit_detectado:
            nit_valido, _ = validar_formato_nit(nit_detectado)
        
        # Detectar si es cliente pre-aprobado que necesita oferta
        analysis_completed = context.get("analysis_completed", False)
        decision = context.get("decision", "")
        stage = context.get("stage", "")
        
        es_pre_aprobado = (analysis_completed and 
                          decision in ["approved", "APROBADO"] and 
                          stage not in ["esperando_respuesta_oferta", "oferta_generada"])
        
        # Detectar respuestas a ofertas previas
        esperando_respuesta = (stage == "esperando_respuesta_oferta")
        
        input_text = f"""
TIPO: CONVERSACIÓN
MENSAJE DEL USUARIO: {message}
CONTEXTO PREVIO: {json.dumps(context, indent=2)}

DETECCIONES:
- NIT encontrado en mensaje: {nit_detectado if nit_detectado else "No detectado"}
- NIT válido: {"Sí" if nit_valido else "No"}
- Cliente pre-aprobado para oferta: {"Sí" if es_pre_aprobado else "No"}
- Esperando respuesta a oferta: {"Sí" if esperando_respuesta else "No"}
- Etapa actual: {stage}
- Decisión crediticia: {decision}
- Análisis completado: {"Sí" if analysis_completed else "No"}

AGENTES DISPONIBLES:
- conversacional: Para chat general, información de productos, respuestas SÍ/NO
- verificador: Cuando hay un NIT válido para verificar cliente
- ofertador: Para clientes pre-aprobados que necesitan oferta crediticia
- financiero: Para análisis de estados financieros (solo con documentos)
- scoring: Para evaluación crediticia (solo con ratios)
- buro: Para consulta centrales de riesgo
- end: Cuando no se requiere procesamiento

PRIORIDADES DE DECISIÓN:
1. Si esperando respuesta a oferta → "conversacional" (manejar SÍ/NO)
2. Si pre-aprobado sin oferta → "ofertador" (generar oferta)
3. Si hay NIT válido → "verificador" (verificar cliente)
4. Si información general → "conversacional"
5. Si documento financiero → "financiero"

Decide qué agente debe manejar esta conversación.
"""
    
    elif interaction_type == "document":
        # DOCUMENTO
        financial_data = payload.get("financial_data", {})
        extracted_text = payload.get("extracted_text", "")
        tables = payload.get("tables", [])
        prompt = payload.get("prompt", "")
        
        company_name = financial_data.get("company_info", {}).get("name", "Empresa no identificada")
        tables_count = len(tables)
        
        input_text = f"""
TIPO: ANÁLISIS DE DOCUMENTO
SOLICITUD DEL USUARIO: {prompt}

DATOS EXTRAÍDOS DEL DOCUMENTO:
- Empresa: {company_name}
- Tablas encontradas: {tables_count}
- Texto extraído: {len(extracted_text)} caracteres

RESUMEN DE EXTRACCIÓN:
{json.dumps(financial_data.get('extraction_summary', {}), indent=2)}

TEXTO PRINCIPAL (primeros 1000 caracteres):
{extracted_text[:1000]}

TABLAS IDENTIFICADAS:
{json.dumps(tables[:3], indent=2) if tables else "No se encontraron tablas"}

Decide qué agente debe procesar este documento.
"""
    
    else:
        input_text = f"TIPO: DESCONOCIDO - {interaction_type}\nDatos: {json.dumps(payload, indent=2)}"
    
    return input_text


def extract_routing_decision(output):
    """
    Extrae la decisión de routing del output del orquestador, manejando respuestas mixtas
    """
    try:
        # Primero intentar con parse_json mejorado
        decision = parse_json(output, None)
        if decision and "next_agent" in decision:
            return decision
        
        # Si eso falla, buscar manualmente el JSON en el texto
        cleaned = clean_markdown(output)
        
        # Buscar patrón {"next_agent": "xxx"}
        import re
        pattern = r'\{\s*"next_agent"\s*:\s*"([^"]+)"[^}]*\}'
        match = re.search(pattern, cleaned)
        
        if match:
            return {
                "next_agent": match.group(1),
                "info": "extraído de respuesta mixta"
            }
        
        # Como último recurso, buscar next_agent en texto plano
        pattern2 = r'"next_agent"\s*:\s*"([^"]+)"'
        match2 = re.search(pattern2, cleaned)
        
        if match2:
            return {
                "next_agent": match2.group(1),
                "info": "extraído de texto plano"
            }
        
        print(f"[WARNING] No se pudo extraer decisión de routing de: {output[:200]}...")
        return {"next_agent": "end", "info": "fallback por error de parsing"}
        
    except Exception as e:
        print(f"[ERROR] Error extrayendo decisión de routing: {e}")
        return {"next_agent": "end", "info": "fallback por excepción"}


def is_routing_decision(output):
    """
    Detecta si el output del orquestador es una decisión de routing (JSON) o un resumen final (texto)
    """
    try:
        cleaned = clean_markdown(output)
        parsed = json.loads(cleaned)
        return "next_agent" in parsed
    except:
        return False


def execute_agent_flow(payload, next_agent, user_id):
    """
    Ejecuta el flujo según la decisión del orquestador
    """
    if next_agent == "conversacional":
        return handle_conversational_agent(payload, user_id)
    
    elif next_agent == "verificador":
        return handle_verification_flow(payload, user_id)
    
    elif next_agent == "ofertador":
        return handle_ofertador_flow(payload, user_id)
    
    elif next_agent == "financiero":
        return handle_financial_flow(payload, user_id)
    
    elif next_agent == "scoring":
        return handle_direct_scoring(payload, user_id)
    
    elif next_agent == "end":
        return handle_insufficient_data(payload, user_id)
    
    else:
        print(f"[WARNING] Agente desconocido: {next_agent}")
        return handle_conversational_agent(payload, user_id)


def handle_verification_flow(payload, user_id):
    """
    Maneja el flujo de verificación de clientes existentes
    VERSIÓN COMPLETA CORREGIDA - Con validación de coherencia
    """
    print(f"[LOG] Ejecutando agente verificador...")
    
    message = payload.get("message", "")
    conversation_context = payload.get("conversation_context", {})
    conversation_history = payload.get("conversation_history", [])
    
    # Extraer NIT del mensaje
    nit_detectado = extraer_nit_de_mensaje(message)
    
    if not nit_detectado:
        print(f"[WARNING] No se pudo extraer NIT del mensaje, redirigiendo a conversacional")
        return handle_conversational_agent(payload, user_id)
    
    # Validar formato del NIT
    nit_valido, mensaje_validacion = validar_formato_nit(nit_detectado)
    
    if not nit_valido:
        # NIT inválido, responder con ayuda
        respuesta_error = f"""
Lo siento, el NIT que proporcionaste no tiene un formato válido. {mensaje_validacion}

Por favor, proporciona el NIT en uno de estos formatos:
- 900123456-7 (con guión)
- 900123456 (solo números)
- 900.123.456-7 (con puntos y guión)

¿Podrías indicarme nuevamente el NIT de tu empresa?
"""
        return {
            "success": True,
            "message": respuesta_error,
            "conversation_context": conversation_context,
            "conversation_history": conversation_history,
            "conversation_mode": "dynamic",
            "user_id": user_id
        }
    
    # *** EXTRAER INFORMACIÓN DEL CRÉDITO ANTES DE LLAMAR AL VERIFICADOR ***
    info_credito = extraer_info_credito_del_mensaje(message)
    
    # *** ACTUALIZAR CONTEXTO CON INFORMACIÓN EXTRAÍDA ***
    contexto_con_info_credito = {
        **conversation_context,
        **info_credito  # Agregar tipo_credito, monto_solicitado, proposito
    }
    
    # Construir input para el verificador CON la información del crédito
    verificador_input = construir_input_verificador(nit_detectado, contexto_con_info_credito)
    
    print(f"[LOG] Consultando cliente con NIT: {nit_detectado}")
    print(f"[LOG] Info crédito extraída: {info_credito}")
    
    # Llamar al agente verificador
    verificador_result = verificador(verificador_input)
    respuesta_verificador = verificador_result.message['content'][0]['text']
    
    # Procesar la respuesta del verificador
    info_procesada = procesar_respuesta_verificador(respuesta_verificador, nit_detectado)
    
    # *** VALIDACIÓN DE COHERENCIA PARA CLIENTES EXISTENTES ***
    validacion_coherencia = None
    if info_procesada["es_cliente_existente"] and info_credito.get("monto_solicitado") and info_procesada.get("score_interno"):
        # Importar la función de validación
        from utils.main_utils import validar_coherencia_solicitud
        
        # Obtener el sector del contexto o inferirlo
        sector = contexto_con_info_credito.get("sector", "general")
        
        validacion_coherencia = validar_coherencia_solicitud(
            info_credito["monto_solicitado"],
            info_procesada["score_interno"], 
            sector,
            True  # es_cliente_existente
        )
        
        # Log para debugging
        print(f"[LOG] Validación coherencia: {validacion_coherencia}")
        
        # Si la solicitud es muy incoherente, agregar advertencia al contexto
        if not validacion_coherencia["es_coherente"]:
            print(f"[WARNING] Solicitud incoherente - Solicitado: ${info_credito['monto_solicitado']:,}, Sugerido: ${validacion_coherencia['monto_sugerido']:,}")
    
    # Actualizar contexto conversacional con TODA la información
    updated_context = {
        **conversation_context,
        "nit_empresa": nit_detectado,
        "empresa_verificada": True,
        "es_cliente_existente": info_procesada["es_cliente_existente"],
        "nombre_empresa": info_procesada["nombre_empresa"],
        "stage": "post_verification",
        "score_interno": info_procesada["score_interno"],
        "clasificacion_riesgo": info_procesada["clasificacion_riesgo"],
        "beneficios_disponibles": info_procesada["beneficios_disponibles"],
        # *** AGREGAR INFORMACIÓN DEL CRÉDITO ***
        **info_credito
    }
    
    # Agregar validación de coherencia al contexto si existe
    if validacion_coherencia:
        updated_context["validacion_coherencia"] = validacion_coherencia
    
    # Si es cliente existente, agregar información adicional
    if info_procesada["es_cliente_existente"]:
        updated_context["cliente_premium"] = info_procesada["score_interno"] and info_procesada["score_interno"] >= 750
        updated_context["tiene_beneficios"] = len(info_procesada["beneficios_disponibles"]) > 0
        
        # Agregar información sectorial si está disponible
        # Buscar en la base de datos del cliente para obtener el sector
        from data.clientes_bd import consultar_cliente
        datos_cliente = consultar_cliente(nit_detectado)
        if datos_cliente.get("sector"):
            updated_context["sector"] = datos_cliente["sector"]
    
    # Actualizar historial
    updated_history = update_conversation_history(
        conversation_history, message, respuesta_verificador
    )
    
    print(f"[LOG] Verificación completada - Cliente: {info_procesada['es_cliente_existente']}")
    print(f"[LOG] Contexto actualizado con: {info_credito}")
    
    return {
        "success": True,
        "message": clean_markdown(respuesta_verificador),
        "verification_info": {
            "nit": nit_detectado,
            "es_cliente": info_procesada["es_cliente_existente"],
            "nombre_empresa": info_procesada["nombre_empresa"],
            "score_interno": info_procesada["score_interno"],
            "clasificacion_riesgo": info_procesada["clasificacion_riesgo"],
            "beneficios_count": len(info_procesada["beneficios_disponibles"])
        },
        "conversation_context": updated_context,
        "conversation_history": updated_history,
        "conversation_mode": "dynamic",
        "user_id": user_id,
        # *** AGREGAR INFO EXTRAÍDA PARA DEBUG ***
        "extracted_info": info_credito,
        "coherence_validation": validacion_coherencia
    }


def handle_ofertador_flow(payload, user_id):
    """
    Maneja el flujo del ofertador - genera ofertas para clientes pre-aprobados
    """
    print(f"[LOG] Ejecutando agente ofertador...")
    
    message = payload.get("message", "")
    conversation_context = payload.get("conversation_context", {})
    conversation_history = payload.get("conversation_history", [])
    
    # Verificar si el cliente está pre-aprobado
    decision = conversation_context.get("decision", "")
    analysis_completed = conversation_context.get("analysis_completed", False)
    
    if not analysis_completed or decision not in ["approved", "APROBADO"]:
        print(f"[WARNING] Cliente no pre-aprobado, redirigiendo a conversacional")
        return handle_conversational_agent(payload, user_id)
    
    # Detectar si es respuesta a oferta previa (SÍ/NO)
    if conversation_context.get("stage") == "esperando_respuesta_oferta":
        return handle_respuesta_oferta(message, conversation_context, conversation_history, user_id)
    
    # Generar nueva oferta
    tipo_producto = extraer_tipo_producto(message, conversation_context)
    monto_solicitado = extraer_monto_solicitado(message)
    
    # Construir input para ofertador
    ofertador_input = construir_input_ofertador(
        conversation_context, 
        tipo_producto, 
        monto_solicitado
    )
    
    print(f"[LOG] Generando oferta para {tipo_producto}...")
    
    # Llamar al agente ofertador
    ofertador_result = ofertador(ofertador_input)
    oferta_response = ofertador_result.message['content'][0]['text']
    
    # Actualizar contexto - ahora esperamos respuesta del cliente
    updated_context = {
        **conversation_context,
        "stage": "esperando_respuesta_oferta",
        "oferta_generada": True,
        "tipo_producto_ofertado": tipo_producto,
        "monto_ofertado": monto_solicitado,
        "fecha_oferta": datetime.now().isoformat()
    }
    
    # Actualizar historial
    updated_history = update_conversation_history(
        conversation_history, message, oferta_response
    )
    
    print(f"[LOG] Oferta generada exitosamente")
    
    return {
        "success": True,
        "message": clean_markdown(oferta_response),
        "offer_generated": True,
        "awaiting_response": True,  # Indica que esperamos respuesta SÍ/NO
        "conversation_context": updated_context,
        "conversation_history": updated_history,
        "conversation_mode": "dynamic",
        "user_id": user_id
    }


def handle_respuesta_oferta(respuesta_usuario, conversation_context, conversation_history, user_id):
    """
    Maneja la respuesta del usuario a una oferta (SÍ/NO)
    Mantiene estado completo sin resetear
    """
    print(f"[LOG] Procesando respuesta a oferta: {respuesta_usuario[:50]}...")
    
    # Procesar respuesta usando la utilidad existente
    respuesta_procesada = procesar_respuesta_continuidad(respuesta_usuario)
    decision_usuario = respuesta_procesada["decision"]
    
    print(f"[LOG] Decisión del usuario: {decision_usuario}")
    
    # Generar mensaje según la decisión
    if decision_usuario == "SI":
        mensaje_respuesta = generar_mensaje_confirmacion_si()
        stage_final = "proceso_formalizado"
        proceso_iniciado = True
        
    elif decision_usuario == "NO":
        mensaje_respuesta = generar_mensaje_despedida_no()
        stage_final = "oferta_declinada"
        proceso_iniciado = False
        
    else:  # UNCLEAR
        mensaje_respuesta = """
Me gustaría asegurarme de entender tu respuesta sobre la oferta que te presenté.

¿Te interesa **continuar con la oferta** y que un asesor te contacte para formalizar el crédito?

Por favor responde claramente **SÍ** o **NO**. ¿Cuál es tu decisión?
"""
        stage_final = "esperando_respuesta_oferta"  # Sigue esperando
        proceso_iniciado = False
    
    # CRÍTICO: Mantener TODO el contexto existente sin resetear
    updated_context = {
        **conversation_context,  # PRESERVAR TODO EL ESTADO ACTUAL
        "stage": stage_final,
        "respuesta_cliente": decision_usuario,
        "proceso_crediticio_iniciado": proceso_iniciado,
        "fecha_respuesta": datetime.now().isoformat()
    }
    
    # ASEGURAR que estos campos críticos NO se pierdan
    if conversation_context.get("analysis_completed"):
        updated_context["analysis_completed"] = True
        
    if conversation_context.get("decision"):
        updated_context["decision"] = conversation_context["decision"]
        
    if conversation_context.get("score"):
        updated_context["score"] = conversation_context["score"]
        
    if conversation_context.get("score_interno"):
        updated_context["score_interno"] = conversation_context["score_interno"]
        
    if conversation_context.get("score_buro"):
        updated_context["score_buro"] = conversation_context["score_buro"]
        
    # Mantener detalles técnicos si existen
    for key in ["financial_ratios", "scoring_details", "buro_details", "analisis_combinado"]:
        if conversation_context.get(key):
            updated_context[key] = conversation_context[key]
    
    # Mantener información de empresa y oferta
    for key in ["nit_empresa", "nombre_empresa", "es_cliente_existente", 
                "tipo_credito", "monto_solicitado", "oferta_generada"]:
        if conversation_context.get(key):
            updated_context[key] = conversation_context[key]
    
    # Actualizar historial conservando todo el contexto previo
    updated_history = update_conversation_history(
        conversation_history, respuesta_usuario, mensaje_respuesta
    )
    
    print(f"[LOG] Respuesta procesada - Decisión: {decision_usuario}, Proceso iniciado: {proceso_iniciado}")
    
    return {
        "success": True,
        "message": mensaje_respuesta,
        "client_decision": decision_usuario,
        "process_initiated": proceso_iniciado,
        "conversation_context": updated_context,
        "conversation_history": updated_history,
        "conversation_mode": "dynamic",
        "user_id": user_id,
        # MANTENER campos importantes en la respuesta
        "decision": conversation_context.get("decision", "pending"),
        "score": conversation_context.get("score", 0),
        "analysis_completed": conversation_context.get("analysis_completed", False)
    }


def handle_conversational_agent(payload, user_id):
    """
    Maneja solicitudes que van al agente conversacional
    VERSIÓN CORREGIDA - Extrae y guarda información del crédito
    """
    print(f"[LOG] Ejecutando agente conversacional...")
    
    message = payload.get("message", "")
    conversation_context = payload.get("conversation_context", {})
    conversation_history = payload.get("conversation_history", [])
    
    # CRÍTICO: Extraer información del crédito ANTES de llamar al agente
    info_credito = extraer_info_credito_del_mensaje(message)
    
    # ACTUALIZAR contexto con información extraída del mensaje actual
    updated_context = {**conversation_context}
    
    if info_credito.get("tipo_credito"):
        updated_context["tipo_credito"] = info_credito["tipo_credito"]
        updated_context["tipo_credito_original"] = info_credito.get("tipo_original", info_credito["tipo_credito"])
        print(f"[LOG] Tipo de crédito detectado: {info_credito['tipo_credito']}")
    
    if info_credito.get("monto_solicitado"):
        updated_context["monto_solicitado"] = info_credito["monto_solicitado"]
        updated_context["monto_formato"] = f"${info_credito['monto_solicitado']//1000000}M"
        print(f"[LOG] Monto detectado: ${info_credito['monto_solicitado']:,}")
    
    if info_credito.get("proposito"):
        updated_context["proposito"] = info_credito["proposito"]
        print(f"[LOG] Propósito detectado: {info_credito['proposito']}")
    
    # Marcar si la solicitud está completa
    if info_credito.get("tipo_credito") and info_credito.get("monto_solicitado"):
        updated_context["solicitud_completa"] = True
        print(f"[LOG] Solicitud completa detectada: {info_credito['tipo_credito']} por ${info_credito['monto_solicitado']:,}")
    
    # Construir input para el agente conversacional con contexto actualizado
    conv_input = build_conversational_input(message, updated_context, conversation_history)
    
    print(f"[LOG] Contexto enviado al agente: tipo={updated_context.get('tipo_credito')}, monto={updated_context.get('monto_solicitado')}")
    
    # Llamar al agente conversacional
    conv_result = conversacional(conv_input)
    bot_response = conv_result.message['content'][0]['text']
    
    # Actualizar contexto y historial conservando toda la información
    final_context, updated_history = update_conversation_data(
        updated_context, conversation_history, message, bot_response
    )
    
    print(f"[LOG] Agente conversacional completado")
    
    return {
        "success": True,
        "message": clean_markdown(bot_response),
        "conversation_context": final_context,
        "conversation_history": updated_history,
        "conversation_mode": "dynamic",
        "user_id": user_id,
        # AGREGAR información extraída para debugging
        "extracted_info": {
            "tipo_credito": info_credito.get("tipo_credito"),
            "monto_solicitado": info_credito.get("monto_solicitado"),
            "proposito": info_credito.get("proposito"),
            "solicitud_completa": updated_context.get("solicitud_completa", False)
        }
    }


def handle_financial_flow(payload, user_id):
    """
    Maneja el flujo financiero completo (financiero → scoring → buró → resumen/oferta)
    VERSIÓN COMPLETA MEJORADA - Con validación de coherencia y montos realistas
    """
    print(f"[LOG] Ejecutando flujo financiero completo...")
    
    financial_data = payload.get("financial_data", {})
    extracted_text = payload.get("extracted_text", "")
    tables = payload.get("tables", [])
    conversation_context = payload.get("conversation_context", {})
    
    # PASO 1: Agente financiero
    print(f"[LOG] Paso 1: Análisis financiero...")
    fin_input = build_financial_input(financial_data, extracted_text, tables)
    fin_result = financiero(fin_input)
    fin_output = fin_result.message['content'][0]['text']
    financial_ratios = parse_json(fin_output)
    
    if not financial_ratios:
        return handle_insufficient_data(payload, user_id)
    
    print(f"[LOG] Ratios financieros calculados: {list(financial_ratios.keys()) if financial_ratios else 'Error'}")
    
    # PASO 2: Agente scoring interno
    print(f"[LOG] Paso 2: Scoring interno...")
    scr_input = build_scoring_input(financial_ratios, financial_data, conversation_context)
    scr_result = scoring(scr_input)
    scr_output = scr_result.message['content'][0]['text']
    scoring_details = parse_json(scr_output)
    
    score_interno = scoring_details.get("score", 0)
    monto_recomendado_scoring = scoring_details.get("monto_recomendado", 0)
    
    print(f"[LOG] Score interno calculado: {score_interno}")
    print(f"[LOG] Monto recomendado por scoring: ${monto_recomendado_scoring:,}" if monto_recomendado_scoring else "[LOG] No se calculó monto en scoring")
    
    # *** VALIDACIÓN DE COHERENCIA CON MONTO SOLICITADO ***
    monto_solicitado = conversation_context.get("monto_solicitado")
    validacion_coherencia = None
    
    if monto_solicitado and score_interno > 0:
        # Importar la función de validación
        from utils.main_utils import validar_coherencia_solicitud
        
        validacion_coherencia = validar_coherencia_solicitud(
            monto_solicitado,
            score_interno,
            conversation_context.get("sector", "general"),
            conversation_context.get("es_cliente_existente", False)
        )
        
        print(f"[LOG] Validación coherencia en flujo financiero: {validacion_coherencia}")
        
        # Si la solicitud es muy alta vs la recomendación del scoring
        if monto_recomendado_scoring > 0 and monto_solicitado > (monto_recomendado_scoring * 1.5):
            print(f"[WARNING] Monto solicitado (${monto_solicitado:,}) muy superior al recomendado por scoring (${monto_recomendado_scoring:,})")
    
    # PASO 3: Agente buró de crédito
    print(f"[LOG] Paso 3: Análisis de buró...")
    nit_empresa = conversation_context.get("nit_empresa")
    
    if nit_empresa:
        buro_input = construir_input_buro(nit_empresa, conversation_context)
        buro_result = buro(buro_input)
        buro_output = buro_result.message['content'][0]['text']
        buro_details = procesar_respuesta_buro(buro_output, nit_empresa)
        print(f"[LOG] Análisis de buró completado")
        
        # PASO 4: Combinar análisis interno + buró
        print(f"[LOG] Paso 4: Combinando análisis...")
        analisis_combinado = combinar_analisis_interno_buro(
            score_interno, 
            buro_details, 
            scoring_details.get("decision", "pending")
        )
        
        decision_final = analisis_combinado["decision_final"]
        score_combinado = analisis_combinado["score_combinado"]
        
    else:
        print(f"[LOG] Sin NIT disponible, solo análisis interno")
        buro_details = None
        decision_final = scoring_details.get("decision", "pending")
        score_combinado = score_interno
        analisis_combinado = None
    
    print(f"[LOG] Decisión final: {decision_final}, Score combinado: {score_combinado}")
    
    # PASO 5: Preparar contexto base para la respuesta
    company_name = conversation_context.get("nombre_empresa") or financial_data.get("company_info", {}).get("name", "tu empresa")
    
    contexto_base = {
        **conversation_context,
        "stage": "post_analysis",
        "decision": normalize_decision(decision_final),
        "score": int(score_combinado) if score_combinado else int(score_interno),
        "score_interno": int(score_interno),
        "score_buro": buro_details.get("score_buro") if buro_details else None,
        "financial_ratios": financial_ratios,
        "scoring_details": scoring_details,
        "buro_details": buro_details,
        "analisis_combinado": analisis_combinado,
        "analysis_completed": True,
        "company_name": company_name,
        "nombre_empresa": company_name,
        # Agregar monto recomendado del scoring para que lo use el ofertador
        "monto_recomendado_scoring": monto_recomendado_scoring
    }
    
    # Agregar validación de coherencia si existe
    if validacion_coherencia:
        contexto_base["validacion_coherencia"] = validacion_coherencia
    
    # PASO 6: Decidir si generar oferta o solo resumen
    if decision_final in ["APROBADO", "CONDICIONAL"]:
        print(f"[LOG] Cliente pre-aprobado, generando oferta...")
        
        # *** CONSTRUIR INPUT MEJORADO PARA OFERTADOR ***
        contexto_para_oferta = {
            **contexto_base,
            # Información específica para el ofertador
            "tipo_producto_solicitado": conversation_context.get("tipo_credito", "credito_empresarial"),
            "monto_cliente_solicito": monto_solicitado,
            "proposito": conversation_context.get("proposito", "capital de trabajo")
        }
        
        # Generar oferta automáticamente
        print(f"[LOG] Generando oferta con monto recomendado: ${monto_recomendado_scoring:,}" if monto_recomendado_scoring else "[LOG] Generando oferta sin monto específico del scoring")
        
        ofertador_input = construir_input_ofertador(
            contexto_para_oferta,
            conversation_context.get("tipo_credito", "credito_empresarial"),
            monto_solicitado
        )
        
        ofertador_result = ofertador(ofertador_input)
        oferta_response = ofertador_result.message['content'][0]['text']
        
        # Contexto final con oferta
        updated_context = {
            **contexto_para_oferta,
            "stage": "esperando_respuesta_oferta",
            "oferta_generada": True,
            "fecha_oferta": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "decision": normalize_decision(decision_final),
            "score": int(score_combinado) if score_combinado else int(score_interno),
            "message": clean_markdown(oferta_response),
            "offer_generated": True,
            "awaiting_response": True,
            "executive_summary": f"Análisis completado: {normalize_decision(decision_final)} con score {score_combinado or score_interno}. Monto máximo: ${monto_recomendado_scoring//1000000 if monto_recomendado_scoring else 'N/A'}M",
            "technical_details": {
                "monto_recomendado": monto_recomendado_scoring,
                "monto_solicitado": monto_solicitado,
                "coherence_validation": validacion_coherencia,
                "raw_flow": {
                    "financiero": financial_ratios,
                    "scoring": scoring_details,
                    "buro": buro_details,
                    "combinado": analisis_combinado
                }
            },
            "conversation_context": updated_context,
            "conversation_mode": "dynamic",
            "user_id": user_id
        }
    
    else:
        # RECHAZADO - Solo resumen sin oferta
        print(f"[LOG] Cliente rechazado, generando resumen...")
        
        # Resumen conversacional del orquestador para rechazos
        summary_input = build_financial_summary_input(
            financial_ratios, scoring_details, buro_details, analisis_combinado, 
            financial_data, contexto_base, company_name
        )
        
        summary_result = orquestador(summary_input)
        conversational_summary = clean_markdown(summary_result.message['content'][0]['text'])
        
        # Contexto final sin oferta
        updated_context = {
            **contexto_base
        }
        
        return {
            "success": True,
            "decision": normalize_decision(decision_final),
            "score": int(score_combinado) if score_combinado else int(score_interno),
            "message": conversational_summary,
            "executive_summary": conversational_summary,
            "technical_details": {
                "monto_recomendado": monto_recomendado_scoring,
                "monto_solicitado": monto_solicitado,
                "coherence_validation": validacion_coherencia,
                "raw_flow": {
                    "financiero": financial_ratios,
                    "scoring": scoring_details,
                    "buro": buro_details,
                    "combinado": analisis_combinado
                }
            },
            "conversation_context": updated_context,
            "conversation_mode": "dynamic",
            "user_id": user_id
        }


def handle_direct_scoring(payload, user_id):
    """
    Maneja scoring directo (sin análisis financiero previo) con buró
    """
    print(f"[LOG] Ejecutando scoring directo con buró...")
    
    financial_data = payload.get("financial_data", {})
    extracted_text = payload.get("extracted_text", "")
    tables = payload.get("tables", [])
    conversation_context = payload.get("conversation_context", {})
    
    # PASO 1: Scoring directo
    print(f"[LOG] Paso 1: Scoring directo...")
    scr_input = build_direct_scoring_input(financial_data, extracted_text, tables)
    scr_result = scoring(scr_input)
    scr_output = scr_result.message['content'][0]['text']
    scoring_details = parse_json(scr_output)
    
    score_interno = scoring_details.get("score", 0)
    print(f"[LOG] Score directo calculado: {score_interno}")
    
    # PASO 2: Agente buró de crédito
    print(f"[LOG] Paso 2: Análisis de buró...")
    nit_empresa = conversation_context.get("nit_empresa")
    
    if nit_empresa:
        buro_input = construir_input_buro(nit_empresa, conversation_context)
        buro_result = buro(buro_input)
        buro_output = buro_result.message['content'][0]['text']
        buro_details = procesar_respuesta_buro(buro_output, nit_empresa)
        
        # PASO 3: Combinar análisis
        analisis_combinado = combinar_analisis_interno_buro(
            score_interno, 
            buro_details,
            scoring_details.get("clasificacion_riesgo")
        )
        
        decision_final = analisis_combinado["decision_final"]
        score_combinado = analisis_combinado["score_combinado"]
    else:
        buro_details = None
        decision_final = scoring_details.get("decision", "pending")
        score_combinado = score_interno
        analisis_combinado = None
    
    print(f"[LOG] Decisión combinada: {decision_final}")
    
    # Resumen conversacional del orquestador
    company_name = conversation_context.get("nombre_empresa") or financial_data.get("company_info", {}).get("name", "tu empresa")
    
    summary_input = f"""
GENERAR RESUMEN CONVERSACIONAL FINAL:

Empresa evaluada: {company_name}
Resultado del scoring directo: {json.dumps(scoring_details, indent=2)}
Análisis de buró: {json.dumps(buro_details, indent=2) if buro_details else "No disponible"}
Análisis combinado: {json.dumps(analisis_combinado, indent=2) if analisis_combinado else "Solo análisis interno"}
Contexto conversacional: {json.dumps(conversation_context, indent=2)}

Presenta estos resultados de forma conversacional natural, como un asesor crediticio experto.
Incluye la decisión, factores clave, y próximos pasos recomendados.
Si hay información de buró, inclúyela de forma natural.
NO uses formato JSON, responde en texto natural.
"""
    
    summary_result = orquestador(summary_input)
    conversational_summary = clean_markdown(summary_result.message['content'][0]['text'])
    
    updated_context = {
        **conversation_context,
        "stage": "post_analysis",
        "decision": normalize_decision(decision_final),
        "score": int(score_combinado) if score_combinado else int(score_interno),
        "score_interno": int(score_interno),
        "score_buro": buro_details.get("score_buro") if buro_details else None,
        "scoring_details": scoring_details,
        "buro_details": buro_details,
        "analisis_combinado": analisis_combinado,
        "analysis_completed": True,
        "company_name": company_name
    }
    
    return {
        "success": True,
        "decision": normalize_decision(decision_final),
        "score": int(score_combinado) if score_combinado else int(score_interno),
        "message": conversational_summary,
        "executive_summary": conversational_summary,
        "technical_details": {
            "raw_flow": {
                "scoring": scoring_details,
                "buro": buro_details,
                "combinado": analisis_combinado
            }
        },
        "conversation_context": updated_context,
        "conversation_mode": "dynamic",
        "user_id": user_id
    }


def handle_insufficient_data(payload, user_id):
    """
    Maneja casos con datos insuficientes
    """
    print(f"[LOG] Datos insuficientes - usando orquestador para respuesta")
    
    financial_data = payload.get("financial_data", {})
    extracted_text = payload.get("extracted_text", "")
    conversation_context = payload.get("conversation_context", {})
    
    insufficient_input = f"""
GENERAR RESPUESTA PARA DATOS INSUFICIENTES:

Contexto: No se pudieron extraer datos financieros suficientes para evaluación
Datos disponibles: {json.dumps(financial_data.get('extraction_summary', {}), indent=2)}
Contexto conversacional: {json.dumps(conversation_context, indent=2)}

Explica de forma conversacional y empática que no hay suficientes datos, 
qué documentos se necesitan, y cómo proceder.
"""
    
    insufficient_result = orquestador(insufficient_input)
    response_message = clean_markdown(insufficient_result.message['content'][0]['text'])
    
    return {
        "success": True,
        "decision": "pending",
        "score": 0,
        "message": response_message,
        "conversation_context": conversation_context,
        "conversation_mode": "dynamic",
        "user_id": user_id
    }


def update_conversation_history(history, user_message, bot_response):
    """
    Actualiza solo el historial de conversación
    """
    updated_history = history.copy() if history else []
    
    # Agregar nuevos mensajes
    updated_history.extend([
        {
            "sender": "user",
            "message": user_message,
            "timestamp": "2024-01-01T00:00:00Z"
        },
        {
            "sender": "bot", 
            "message": bot_response,
            "timestamp": "2024-01-01T00:00:01Z"
        }
    ])
    
    # Mantener solo últimos 20 mensajes
    if len(updated_history) > 20:
        updated_history = updated_history[-20:]
    
    return updated_history


# FUNCIONES AUXILIARES

def build_conversational_input(message, context, history):
    """Construye input para el agente conversacional"""
    context_section = ""
    if context:
        context_section = f"""
CONTEXTO DE LA CONVERSACIÓN:
- Empresa: {context.get('company_name', 'No especificada')}
- Sector: {context.get('sector', 'No especificado')}
- Etapa actual: {context.get('stage', 'inicial')}
- Análisis completado: {'Sí' if context.get('analysis_completed') else 'No'}
"""
        
        if context.get('analysis_completed'):
            context_section += f"""
- Decisión crediticia: {context.get('decision', 'No disponible')}
- Score obtenido: {context.get('score', 'No disponible')}/1000
"""

        # Información de verificación de cliente
        if context.get('empresa_verificada'):
            context_section += f"""
- Cliente verificado: {'Sí' if context.get('es_cliente_existente') else 'No'}
- NIT: {context.get('nit_empresa', 'No disponible')}
"""
            if context.get('es_cliente_existente'):
                context_section += f"""
- Score interno: {context.get('score_interno', 'No disponible')}/1000
- Clasificación: {context.get('clasificacion_riesgo', 'No disponible')}
- Beneficios disponibles: {len(context.get('beneficios_disponibles', []))}
"""

        # Información de ofertas
        if context.get('stage') == 'esperando_respuesta_oferta':
            context_section += f"""
- Oferta generada: Sí
- Esperando respuesta del cliente (SÍ/NO)
"""

    history_section = ""
    if history and len(history) > 0:
        recent_messages = history[-6:]
        history_section = "\nHISTORIAL RECIENTE:\n"
        for msg in recent_messages:
            sender = "Usuario" if msg.get('sender') == 'user' else "CreditBot"
            message_text = msg.get('message', '')[:200]
            history_section += f"{sender}: {message_text}\n"

    return f"""{context_section}{history_section}
MENSAJE ACTUAL DEL USUARIO:
{message}

Responde de forma natural y conversacional como un asesor crediticio experto.
"""


def build_financial_summary_input(financial_ratios, scoring_details, buro_details, analisis_combinado, financial_data, conversation_context, company_name):
    """Construye input para resumen conversacional con análisis completo"""
    
    score_interno = scoring_details.get("score", 0) if scoring_details else 0
    score_buro = buro_details.get("score_buro") if buro_details else None
    decision_final = analisis_combinado.get("decision_final") if analisis_combinado else "pending"
    es_cliente_existente = conversation_context.get("es_cliente_existente", False)
    
    # Generar explicación en lenguaje natural usando la nueva función
    from utils.main_utils import formatear_explicacion_dual_analisis
    explicacion_dual = formatear_explicacion_dual_analisis(
        score_interno, score_buro, decision_final, es_cliente_existente
    )
    
    input_base = f"""
GENERAR RESPUESTA CONVERSACIONAL FINAL - IMPORTANTE: SIN SCORES TÉCNICOS

EMPRESA: {company_name}
EXPLICACIÓN DUAL YA FORMATEADA (usar tal como está):
{explicacion_dual}

CONTEXTO TÉCNICO PARA TU COMPRENSIÓN (NO mostrar al usuario):
- Score interno: {score_interno}
- Score buró: {score_buro}
- Decisión: {decision_final}

INSTRUCCIONES:
1. USA la explicación dual formateada EXACTAMENTE como está escrita
2. NUNCA menciones números de score (752/1000, etc.)
3. Continúa la conversación naturalmente después de la explicación
4. Si es aprobado, menciona que pueden proceder con la oferta
5. Si es rechazado, ofrece alternativas y próximos pasos constructivos
6. Mantén tono profesional pero cercano

La respuesta debe ser conversacional, transparente sobre el proceso dual, pero sin jerga técnica.
"""
    
    return input_base


def build_financial_input(financial_data, extracted_text, tables):
    """Construye input para el agente financiero"""
    fin_input = f"""
Analiza los siguientes datos financieros extraídos con Textract:

DATOS ESTRUCTURADOS:
{json.dumps(financial_data, indent=2)}

TEXTO EXTRAÍDO:
{extracted_text}

TABLAS FINANCIERAS:
{json.dumps(tables, indent=2)}

Calcula los ratios financieros según las instrucciones del sistema.
"""
    return fin_input


def build_scoring_input(financial_ratios, financial_data, conversation_context=None):
    """
    Construye input para el agente de scoring - VERSIÓN MEJORADA
    Incluye contexto del cliente para mejor análisis
    """
    company_name = financial_data.get("company_info", {}).get("name", "Empresa")
    
    # Información adicional del contexto
    contexto_adicional = ""
    if conversation_context:
        es_cliente = conversation_context.get("es_cliente_existente", False)
        score_interno_previo = conversation_context.get("score_interno", 0)
        sector = conversation_context.get("sector", "general")
        monto_solicitado = conversation_context.get("monto_solicitado", 0)
        
        contexto_adicional = f"""
CONTEXTO ADICIONAL DEL CLIENTE:
- Empresa: {company_name}
- Sector: {sector.title()}
- Cliente existente: {"Sí" if es_cliente else "No"}
- Score interno previo: {score_interno_previo}/1000 (si es cliente existente)
- Monto solicitado: ${monto_solicitado:,} COP
- Propósito: {conversation_context.get('proposito', 'No especificado')}

INSTRUCCIONES ESPECÍFICAS:
- Si es cliente existente con buen historial, considera esto como factor positivo
- El monto_recomendado debe ser realista para el sector {sector}
- Compara el monto solicitado con tu cálculo de capacidad de pago
"""
    
    scr_input = f"""
Evalúa crediticiamente a {company_name} con base en:

RATIOS FINANCIEROS CALCULADOS:
{json.dumps(financial_ratios, indent=2)}

INFORMACIÓN ADICIONAL DE LA EMPRESA:
{json.dumps(financial_data.get("company_info", {}), indent=2)}

{contexto_adicional}

Calcula el score, decisión y MONTO MÁXIMO REALISTA según tu metodología inteligente.
Recuerda: NO uses $5,000,000,000 - calcula montos reales basados en capacidad de pago.
"""
    return scr_input


def build_direct_scoring_input(financial_data, extracted_text, tables):
    """Construye input para scoring directo"""
    scr_input = f"""
Evalúa directamente los siguientes datos financieros:

DATOS EXTRAÍDOS:
{json.dumps(financial_data, indent=2)}

TEXTO DEL DOCUMENTO:
{extracted_text[:2000]}

TABLAS:
{json.dumps(tables[:5], indent=2)}

Calcula ratios y asigna puntaje crediticio.
"""
    return scr_input


def update_conversation_data(context, history, user_message, bot_response):
    """Actualiza contexto y historial después de cada intercambio"""
    # Actualizar historial
    updated_history = update_conversation_history(history, user_message, bot_response)
    
    # Actualizar contexto extrayendo información nueva
    updated_context = context.copy() if context else {}
    
    # Extraer información del mensaje del usuario
    extracted_info = extract_user_info(user_message)
    updated_context.update(extracted_info)
    
    return updated_context, updated_history


def extract_user_info(user_message):
    """Extrae información relevante del mensaje del usuario"""
    info = {}
    message_lower = user_message.lower()
    
    # Detectar nombre de empresa
    import re
    company_patterns = [
        r"empresa\s+([A-Za-z][A-Za-z\s&.,]+?)(?:\s|$|,)",
        r"compañía\s+([A-Za-z][A-Za-z\s&.,]+?)(?:\s|$|,)",
        r"([A-Za-z][A-Za-z\s&.,]*?)\s+(?:s\.a\.s\.|sas|ltda|s\.a\.|sa)(?:\s|$|,)"
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, user_message, re.IGNORECASE)
        if match:
            info["company_name"] = match.group(1).strip()
            break
    
    # Detectar sector empresarial
    sectors_map = {
        "construcción": ["construcción", "construc", "obra", "inmobiliaria", "constructor"],
        "comercio": ["comercio", "ventas", "retail", "tienda", "almacén"],
        "servicios": ["servicios", "consultoría", "asesoría", "consulting"],
        "manufactura": ["manufactura", "producción", "fábrica", "industrial", "manufactur"],
        "tecnología": ["tecnología", "software", "desarrollo", "IT", "tech"],
        "salud": ["salud", "médico", "clínica", "hospital", "farmac"],
        "transporte": ["transporte", "logística", "carga", "fletes"],
        "agricultura": ["agricultura", "agrícola", "campo", "agro", "cultivo"]
    }
    
    for sector, keywords in sectors_map.items():
        if any(keyword in message_lower for keyword in keywords):
            info["sector"] = sector
            break
    
    # Detectar años de operación
    years_match = re.search(r"(\d+)\s+años", message_lower)
    if years_match:
        info["years_operating"] = int(years_match.group(1))
    
    # Detectar etapa de conversación
    if any(word in message_lower for word in ["documentos", "subir", "pdf", "archivo"]):
        info["stage"] = "document_upload"
    elif any(word in message_lower for word in ["monto", "cuánto", "cantidad", "simulación"]):
        info["stage"] = "amount_inquiry"
    elif any(word in message_lower for word in ["siguiente", "pasos", "formalizar", "firmar"]):
        info["stage"] = "formalization"
    
    return info


def extraer_tipo_producto(mensaje, contexto):
    """
    Extrae el tipo de producto crediticio del mensaje o contexto
    """
    mensaje_lower = mensaje.lower()
    
    # Detectar tipos específicos en el mensaje
    if any(word in mensaje_lower for word in ["hipotecario", "hipoteca", "inmueble", "local", "oficina"]):
        return "hipotecario_comercial"
    elif any(word in mensaje_lower for word in ["rotativo", "rotativa", "línea", "linea", "flexible"]):
        return "linea_credito_rotativa"  
    elif any(word in mensaje_lower for word in ["factoring", "cartera", "cuentas por cobrar", "descuento"]):
        return "factoring"
    elif any(word in mensaje_lower for word in ["empresarial", "comercial", "capital", "expansion", "inversion"]):
        return "credito_empresarial"
    
    # Si no se detecta tipo específico, usar contexto
    sector = contexto.get("sector", "")
    if sector == "construccion":
        return "credito_empresarial"  # Créditos de construcción son empresariales
    elif sector == "comercio":
        return "linea_credito_rotativa"  # Comercio suele necesitar rotativo
    else:
        return "credito_empresarial"  # Default


def extraer_monto_solicitado(mensaje):
    """
    Extrae el monto solicitado del mensaje usando regex
    """
    import re
    
    # Patrones para detectar montos
    patrones_monto = [
        r'(\d{1,3}(?:\.\d{3})*(?:\.\d{3})*)\s*(?:millones?|mill?)',  # 500 millones
        r'\$\s*(\d{1,3}(?:\.\d{3})*(?:\.\d{3})*)\s*(?:millones?|mill?)',  # $500 millones
        r'(\d{1,3}(?:\,\d{3})*(?:\,\d{3})*)\s*(?:millones?|mill?)',  # 500,000 millones (formato US)
        r'\$\s*(\d{1,3}(?:\,\d{3})*(?:\,\d{3})*)\s*(?:COP|cop|pesos?)?',  # $500,000,000
        r'(\d{1,3}(?:\.\d{3})*)\s*(?:mil millones?)',  # 5 mil millones
    ]
    
    for patron in patrones_monto:
        match = re.search(patron, mensaje, re.IGNORECASE)
        if match:
            numero_str = match.group(1).replace('.', '').replace(',', '')
            try:
                numero = int(numero_str)
                
                # Ajustar según el patrón encontrado
                if 'millones' in match.group(0).lower():
                    if 'mil millones' in match.group(0).lower():
                        return numero * 1000000000  # mil millones
                    else:
                        return numero * 1000000  # millones normales
                else:
                    return numero  # Número directo en pesos
                    
            except ValueError:
                continue
    
    return None  # No se encontró monto específico


def normalize_decision(decision):
    """Normaliza la decisión para el frontend"""
    if not decision:
        return "pending"
    
    decision_upper = str(decision).upper()
    
    if "APROBADO" in decision_upper or "APPROVED" in decision_upper:
        return "approved"
    elif "RECHAZADO" in decision_upper or "REJECTED" in decision_upper:
        return "rejected"
    else:
        return "pending"


if __name__ == "__main__":
    app.run()