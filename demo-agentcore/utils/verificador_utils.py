# utils/verificador_utils.py
# Utilidades para el agente verificador

import sys
import os

# Importar desde la estructura de paquetes
try:
    # Intento 1: Importación relativa desde el paquete
    from ..data.clientes_bd import consultar_cliente
except ImportError:
    try:
        # Intento 2: Importación absoluta
        from data.clientes_bd import consultar_cliente
    except ImportError:
        # Intento 3: Agregar ruta manualmente
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from data.clientes_bd import consultar_cliente

def construir_input_verificador(nit, contexto_conversacion=None):
    """
    Construye el input para el agente verificador consultando la base de datos
    VERSIÓN CORREGIDA - Incluye información extraída del mensaje
    """
    
    # Consultar base de datos de clientes
    datos_cliente = consultar_cliente(nit)
    
    if datos_cliente.get("es_cliente", False):
        # CLIENTE EXISTENTE
        input_text = construir_input_cliente_existente(datos_cliente, nit, contexto_conversacion)
    else:
        # CLIENTE NUEVO
        input_text = construir_input_cliente_nuevo(datos_cliente, nit, contexto_conversacion)
    
    return input_text


def construir_input_cliente_existente(datos_cliente, nit, contexto_conversacion):
    """
    Construye input para cliente existente - VERSIÓN CORREGIDA
    """
    
    # Calcular años de relación
    tiempo_relacion = datos_cliente.get("tiempo_relacion_anos", 0)
    
    # Formatear productos actuales
    productos = datos_cliente.get("productos_actuales", [])
    productos_texto = ", ".join(productos) if productos else "Productos básicos"
    
    # Formatear beneficios disponibles
    beneficios = datos_cliente.get("beneficios_disponibles", [])
    beneficios_texto = "\n- " + "\n- ".join(beneficios) if beneficios else "Beneficios estándar"
    
    # Información del gestor
    gestor = datos_cliente.get("gestor_asignado", "Ejecutivo asignado")
    telefono_gestor = datos_cliente.get("telefono_gestor", "")
    
    # TRADUCIR PERFIL TÉCNICO A LENGUAJE AMIGABLE
    score_interno = datos_cliente.get("score_interno_historico", 0)
    clasificacion_riesgo = datos_cliente.get("clasificacion_riesgo", "")
    perfil_amigable = traducir_perfil_tecnico(score_interno, clasificacion_riesgo)
    
    # *** NUEVA SECCIÓN: INFORMACIÓN DEL CRÉDITO SOLICITADO ***
    info_credito_section = ""
    if contexto_conversacion:
        tipo_credito = contexto_conversacion.get('tipo_credito')
        monto_solicitado = contexto_conversacion.get('monto_solicitado') 
        proposito = contexto_conversacion.get('proposito')
        
        if tipo_credito or monto_solicitado:
            info_credito_section = f"""
INFORMACIÓN DEL CRÉDITO YA SOLICITADO (NO PREGUNTAR DE NUEVO):
- Tipo solicitado: {tipo_credito or 'No especificado'}
- Monto solicitado: ${monto_solicitado:,} COP ({contexto_conversacion.get('monto_formato', 'N/A')}) si monto_solicitado else 'No especificado'
- Propósito: {proposito or 'No especificado'}

INSTRUCCIÓN CRÍTICA: El cliente YA proporcionó esta información. NO preguntes el tipo ni el monto.
RESPONDE: "Perfecto Carlos, necesitas un {tipo_credito} por ${monto_solicitado//1000000 if monto_solicitado else 'X'}M para {proposito}. Para evaluar necesito estados financieros 2024."
"""
    
    input_text = f"""
VERIFICACIÓN DE CLIENTE - RESULTADO: CLIENTE EXISTENTE ✅

DATOS DEL CLIENTE:
- Empresa: {datos_cliente.get("nombre", "Empresa")}
- NIT consultado: {nit}
- Cliente desde: {datos_cliente.get("fecha_vinculacion", "No disponible")} ({tiempo_relacion} años)
- Sector: {datos_cliente.get("sector", "No especificado").title()}
- Ciudad: {datos_cliente.get("ciudad", "No especificada")}

PERFIL COMERCIAL:
- Descripción del perfil: {perfil_amigable}
- Relación comercial: {datos_cliente.get("relacion_comercial", "No evaluada")}

PRODUCTOS ACTUALES:
{productos_texto}

BENEFICIOS DISPONIBLES PARA ESTE CLIENTE:
{beneficios_texto}

GESTOR ASIGNADO:
- {gestor}
- Teléfono: {telefono_gestor}

{info_credito_section}

CONTEXTO CONVERSACIONAL PREVIO:
{formatear_contexto_conversacion(contexto_conversacion)}

INSTRUCCIONES IMPORTANTES:
- NO menciones scores numéricos ({score_interno}) ni códigos técnicos ({clasificacion_riesgo})
- USA el perfil amigable: "{perfil_amigable}"
- Este cliente tiene {tiempo_relacion} años de relación
- SI YA TIENES información del crédito arriba, úsala directamente y pide documentos
- SI NO tienes información completa del crédito, pregunta conversacionalmente
- Salúdalo reconociendo su historia y menciona productos actuales
"""
    
    return input_text

def traducir_perfil_tecnico(score_interno, clasificacion_riesgo):
    """
    Traduce términos técnicos a lenguaje amigable para el cliente
    """
    if score_interno >= 750 or clasificacion_riesgo in ["A1", "A2"]:
        return "cliente preferencial con excelente historial comercial"
    elif score_interno >= 650 or clasificacion_riesgo in ["B1", "B+"]:
        return "cliente establecido con buen comportamiento comercial"
    elif score_interno >= 600 or clasificacion_riesgo in ["B2", "BBB+"]:
        return "cliente con relación comercial sólida"
    elif score_interno >= 500 or clasificacion_riesgo in ["BBB", "C1"]:
        return "cliente en desarrollo con potencial de crecimiento"
    elif score_interno >= 400 or clasificacion_riesgo in ["C2", "BB"]:
        return "cliente que requiere evaluación personalizada"
    else:
        return "cliente que requiere análisis detallado"

def construir_input_cliente_nuevo(datos_cliente, nit, contexto_conversacion):
    """
    Construye input para cliente nuevo o no encontrado
    """
    
    motivo = datos_cliente.get("motivo", "NIT no encontrado")
    sector_identificado = datos_cliente.get("sector_identificado", "")
    ciudad_identificada = datos_cliente.get("ciudad_identificada", "")
    
    input_text = f"""
VERIFICACIÓN DE CLIENTE - RESULTADO: CLIENTE NUEVO 🆕

DATOS DE LA CONSULTA:
- NIT consultado: {nit}
- Resultado: {datos_cliente.get("nombre", "Empresa no identificada")}
- Motivo: {motivo}

INFORMACIÓN IDENTIFICADA:
- Sector estimado: {sector_identificado.title() if sector_identificado else "Por determinar"}
- Ciudad estimada: {ciudad_identificada if ciudad_identificada else "Por determinar"}

OBSERVACIONES:
{datos_cliente.get("observaciones", "Empresa nueva en nuestra base de datos")}

CONTEXTO CONVERSACIONAL PREVIO:
{formatear_contexto_conversacion(contexto_conversacion)}

INSTRUCCIONES:
Esta empresa NO es cliente actual de nuestra entidad. Dale una bienvenida cálida, explícale que como empresa nueva evaluaremos su solicitud con nuestros productos diseñados para todo tipo de empresas. Tranquilízala mencionando que tenemos soluciones para empresas en todas las etapas de desarrollo. Guía el siguiente paso indicando que necesitaremos documentos financieros para la evaluación.

PRODUCTOS DISPONIBLES PARA EMPRESAS NUEVAS:
- Crédito Empresarial: $50M-$5.000M, DTF+4.5% a DTF+8%, hasta 5 años
- Hipotecario Comercial: hasta 70% valor inmueble, hasta 15 años  
- Línea de Crédito Rotativa: disponibilidad inmediata
- Factoring: conversión inmediata de cuentas por cobrar

Pregunta conversacionalmente qué tipo de financiamiento necesita.
"""
    
    return input_text

def formatear_contexto_conversacion(contexto):
    """
    Formatea el contexto conversacional para el agente
    """
    if not contexto:
        return "Primera interacción del cliente"
    
    contexto_texto = "Información previa de la conversación:\n"
    
    if contexto.get("company_name"):
        contexto_texto += f"- Empresa mencionada: {contexto['company_name']}\n"
    
    if contexto.get("sector"):
        contexto_texto += f"- Sector indicado: {contexto['sector']}\n"
    
    if contexto.get("stage"):
        contexto_texto += f"- Etapa conversacional: {contexto['stage']}\n"
    
    if contexto.get("analysis_completed"):
        contexto_texto += f"- Análisis completado: {'Sí' if contexto['analysis_completed'] else 'No'}\n"
        
        if contexto.get("decision"):
            contexto_texto += f"- Decisión previa: {contexto['decision']}\n"
            
        if contexto.get("score"):
            contexto_texto += f"- Score obtenido: {contexto['score']}/1000\n"
    
    return contexto_texto

def formatear_monto(monto):
    """
    Formatea montos grandes en formato colombiano (millones/billones)
    """
    if monto == 0:
        return "$0"
    elif monto >= 1000000000:  # Mil millones o más
        billones = monto / 1000000000
        return f"${billones:,.1f} mil millones"
    elif monto >= 1000000:  # Millones
        millones = monto / 1000000
        return f"${millones:,.0f} millones"
    else:
        return f"${monto:,.0f}"

def extraer_nit_de_mensaje(mensaje):
    """
    Extrae el NIT del mensaje del usuario usando expresiones regulares
    """
    import re
    
    # Patrones comunes para NITs en Colombia
    patrones_nit = [
        r'\b(\d{9}-\d)\b',  # Formato: 123456789-0
        r'\b(\d{9})\b',     # Solo números: 123456789
        r'\b(\d{3}\.?\d{3}\.?\d{3}-\d)\b',  # Con puntos: 123.456.789-0
    ]
    
    for patron in patrones_nit:
        match = re.search(patron, mensaje)
        if match:
            nit_encontrado = match.group(1)
            # Limpiar y formatear
            nit_limpio = nit_encontrado.replace(".", "").replace(" ", "")
            return nit_limpio
    
    return None

def validar_formato_nit(nit):
    """
    Valida que el NIT tenga formato colombiano válido
    """
    import re
    
    if not nit:
        return False, "NIT vacío"
    
    # Limpiar NIT
    nit_limpio = str(nit).replace("-", "").replace(".", "").replace(" ", "")
    
    # Verificar longitud (8-10 dígitos)
    if len(nit_limpio) < 8 or len(nit_limpio) > 10:
        return False, "NIT debe tener entre 8 y 10 dígitos"
    
    # Verificar que solo contenga números
    if not nit_limpio.isdigit():
        return False, "NIT debe contener solo números"
    
    return True, "NIT válido"

def procesar_respuesta_verificador(respuesta_agente, nit):
    """
    Procesa la respuesta del agente verificador y extrae información estructurada
    """
    
    # Consultar datos originales para metadata
    datos_cliente = consultar_cliente(nit)
    
    return {
        "mensaje_conversacional": respuesta_agente,
        "es_cliente_existente": datos_cliente.get("es_cliente", False),
        "nombre_empresa": datos_cliente.get("nombre", "Empresa no identificada"),
        "nit_consultado": nit,
        "score_interno": datos_cliente.get("score_interno_historico", 0) if datos_cliente.get("es_cliente") else None,
        "clasificacion_riesgo": datos_cliente.get("clasificacion_riesgo", "") if datos_cliente.get("es_cliente") else "Nuevo",
        "beneficios_disponibles": datos_cliente.get("beneficios_disponibles", []) if datos_cliente.get("es_cliente") else [],
        "siguiente_paso": "verificacion_completada"
    }
    
def extraer_info_credito_del_mensaje(mensaje):
    """
    Extrae información completa usando comprensión de lenguaje natural de Claude
    VERSIÓN MEJORADA - Sin regex, con comprensión contextual
    """
    import re
    
    info = {}
    mensaje_lower = mensaje.lower()
    
    print(f"[LOG] Analizando mensaje para extracción: {mensaje[:100]}...")
    
    # EXTRAER TIPO DE CRÉDITO usando comprensión natural
    tipos_credito = {
        # Más específico a menos específico
        "capital de trabajo": "crédito empresarial",
        "crédito de capital de trabajo": "crédito empresarial", 
        "crédito empresarial": "crédito empresarial",
        "crédito comercial": "crédito empresarial",
        "credito empresarial": "crédito empresarial",
        "credito comercial": "crédito empresarial",
        "empresarial": "crédito empresarial",
        "comercial": "crédito empresarial",
        "expansión": "crédito empresarial",
        "expansion": "crédito empresarial",
        "crecimiento": "crédito empresarial",
        "inversión": "crédito empresarial",
        "inversion": "crédito empresarial",
        "financiamiento": "crédito empresarial",
        
        # Línea rotativa
        "línea de crédito": "línea rotativa",
        "linea de credito": "línea rotativa", 
        "línea rotativa": "línea rotativa",
        "linea rotativa": "línea rotativa",
        "rotativo": "línea rotativa",
        "rotativa": "línea rotativa",
        
        # Hipotecario
        "hipotecario": "hipotecario comercial",
        "hipoteca": "hipotecario comercial",
        "inmueble": "hipotecario comercial",
        "propiedad": "hipotecario comercial",
        
        # Factoring
        "factoring": "factoring",
        "cartera": "factoring",
        "cuentas por cobrar": "factoring"
    }
    
    for palabra_clave, tipo_estandar in tipos_credito.items():
        if palabra_clave in mensaje_lower:
            info["tipo_credito"] = tipo_estandar
            info["tipo_original"] = palabra_clave
            print(f"[LOG] Tipo detectado: {palabra_clave} -> {tipo_estandar}")
            break
    
    # EXTRAER MONTO usando comprensión natural mejorada
    # Patrones más inteligentes y flexibles
    patrones_monto = [
        # Números con palabras explícitas
        r'(\d{1,4})\s*mil\s*millones?',  # 5 mil millones
        r'(\d{1,3}(?:[.,]\d{3})*)\s*millones?',  # 500 millones, 1.000 millones
        r'\$\s*(\d{1,3}(?:[.,]\d{3})*)\s*millones?',  # $500 millones
        
        # Formato con M
        r'\$?\s*(\d{1,4})\s*[Mm](?:[Mm])?',  # 500M, $300MM
        
        # Números grandes sin millones explícito
        r'\$\s*(\d{3,}(?:[.,]\d{3})*)',  # $500,000,000
        
        # Casos especiales en texto
        r'quinientos?\s*millones?',  # quinientos millones -> 500
        r'mil\s*millones?',  # mil millones -> 1000 (cuando no hay número antes)
    ]
    
    for i, patron in enumerate(patrones_monto):
        match = re.search(patron, mensaje, re.IGNORECASE)
        if match:
            if patron == r'quinientos?\s*millones?':
                numero = 500
            elif patron == r'mil\s*millones?':
                numero = 1000
            else:
                numero_str = match.group(1).replace('.', '').replace(',', '')
                try:
                    numero = int(numero_str)
                except ValueError:
                    continue
            
            # Calcular monto final
            if 'mil millones' in match.group(0).lower():
                monto_final = numero * 1000000000
                formato = f"${numero} mil millones"
            elif 'millones' in match.group(0).lower() or 'M' in match.group(0):
                monto_final = numero * 1000000  
                formato = f"${numero}M"
            elif numero >= 100000000:  # Si es un número grande sin palabra
                monto_final = numero
                formato = f"${numero//1000000}M"
            else:
                monto_final = numero * 1000000
                formato = f"${numero}M"
            
            # Validar rango razonable
            if monto_final < 1000000:  # Menos de 1M
                print(f"[WARNING] Monto muy pequeño: ${monto_final:,}")
                continue
            elif monto_final > 50000000000:  # Más de 50 mil millones
                print(f"[WARNING] Monto muy grande: ${monto_final:,}")
                monto_final = 5000000000  # Limitar a 5 mil millones
                formato = "$5,000M"
            
            info["monto_solicitado"] = monto_final
            info["monto_formato"] = formato
            
            print(f"[LOG] Monto detectado (patrón {i+1}): {match.group(0)} -> ${monto_final:,}")
            break
    
    # EXTRAER PROPÓSITO usando comprensión natural
    propositos = {
        "capital de trabajo": "capital de trabajo",
        "flujo de caja": "capital de trabajo", 
        "inventario": "capital de trabajo",
        "operativo": "capital de trabajo",
        "operación": "capital de trabajo",
        "expansión": "expansión",
        "expansion": "expansión", 
        "crecimiento": "expansión",
        "ampliación": "expansión",
        "inversión": "inversión",
        "inversion": "inversión",
        "equipos": "compra de equipos",
        "maquinaria": "compra de equipos",
        "tecnología": "compra de equipos",
        "inmueble": "compra de inmueble",
        "local": "compra de inmueble",
        "oficina": "compra de inmueble"
    }
    
    for palabra_clave, proposito_estandar in propositos.items():
        if palabra_clave in mensaje_lower:
            info["proposito"] = proposito_estandar
            print(f"[LOG] Propósito detectado: {proposito_estandar}")
            break
    
    print(f"[LOG] Información extraída: {info}")
    return info


def build_conversational_input(message, context, history):
    """
    Construye input para el agente conversacional incluyendo información del crédito
    VERSIÓN MEJORADA que incluye info del crédito en el contexto
    """
    context_section = ""
    if context:
        context_section = f"""
CONTEXTO DE LA CONVERSACIÓN:
- Empresa: {context.get('company_name') or context.get('nombre_empresa', 'No especificada')}
- Sector: {context.get('sector', 'No especificado')}
- Etapa actual: {context.get('stage', 'inicial')}
- Análisis completado: {'Sí' if context.get('analysis_completed') else 'No'}
"""
        
        # INFORMACIÓN DEL CRÉDITO SOLICITADO (NUEVO)
        if context.get('tipo_credito') or context.get('monto_solicitado'):
            context_section += "\nINFORMACIÓN DEL CRÉDITO SOLICITADO:\n"
            if context.get('tipo_credito'):
                context_section += f"- Tipo: {context['tipo_credito']}\n"
            if context.get('monto_solicitado'):
                context_section += f"- Monto: ${context['monto_solicitado']:,} ({context.get('monto_formato', 'N/A')})\n"
            if context.get('proposito'):
                context_section += f"- Propósito: {context['proposito']}\n"
            if context.get('solicitud_completa'):
                context_section += "- Solicitud: COMPLETA (no preguntar tipo ni monto de nuevo)\n"
        
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

INSTRUCCIÓN CRÍTICA: Si ya tienes información del crédito en el contexto (tipo, monto), NO vuelvas a preguntarla. Úsala directamente.

Responde de forma natural y conversacional como un asesor crediticio experto.
"""