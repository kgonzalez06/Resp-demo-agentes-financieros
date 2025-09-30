# data/clientes_bd.py
# Simulación de base de datos interna de la entidad financiera

CLIENTES_BD = {
    # CLIENTES EXISTENTES - PERFIL PREMIUM
    "900123456-7": {
        "nombre": "Constructora Los Andes S.A.S",
        "es_cliente": True,
        "fecha_vinculacion": "2019-03-15",
        "tiempo_relacion_anos": 5,
        "sector": "construccion",
        "ciudad": "Bogotá",
        "productos_actuales": ["Cuenta Corriente Empresarial", "CDT $200M", "Crédito Rotativo $300M"],
        "score_interno_historico": 780,
        "clasificacion_riesgo": "A1",
        "relacion_comercial": "Excelente",
        "ingresos_promedio_mensual": 2500000000,  # $2.500M mensuales
        "patrimonio_estimado": 8000000000,  # $8.000M
        "experiencia_crediticia": "5 créditos pagados sin novedad",
        "beneficios_disponibles": [
            "Tasa preferencial (-1.5%)",
            "Débito automático (-0.5% adicional)", 
            "Proceso expedito (48 horas)",
            "Sin comisión de estudio",
            "Seguro de vida gratis"
        ],
        "gestor_asignado": "María Fernández - Gerente Corporativo",
        "telefono_gestor": "601-234-5678",
        "observaciones": "Cliente premium con excelente comportamiento de pago. Relación comercial sólida."
    },

    "800987654-3": {
        "nombre": "Textiles del Valle Ltda",
        "es_cliente": True,
        "fecha_vinculacion": "2021-08-10",
        "tiempo_relacion_anos": 3,
        "sector": "manufactura",
        "ciudad": "Cali",
        "productos_actuales": ["Cuenta Corriente", "Factoring $150M", "Tarjeta Crédito Empresarial"],
        "score_interno_historico": 680,
        "clasificacion_riesgo": "B1",
        "relacion_comercial": "Buena",
        "ingresos_promedio_mensual": 800000000,  # $800M mensuales
        "patrimonio_estimado": 2500000000,  # $2.500M
        "experiencia_crediticia": "2 créditos activos, 1 mora leve hace 8 meses",
        "beneficios_disponibles": [
            "Débito automático (-0.5%)",
            "Proceso preferencial",
            "Descuento 25% comisión estudio"
        ],
        "gestor_asignado": "Carlos Ruiz - Ejecutivo PYME",
        "telefono_gestor": "602-345-6789",
        "observaciones": "Cliente con potencial de crecimiento. Sector textil estable en la región."
    },

    "700456789-1": {
        "nombre": "Distribuidora del Caribe S.A",
        "es_cliente": True,
        "fecha_vinculacion": "2022-11-20",
        "tiempo_relacion_anos": 2,
        "sector": "comercio",
        "ciudad": "Barranquilla", 
        "productos_actuales": ["Cuenta Corriente", "Datafonos"],
        "score_interno_historico": 620,
        "clasificacion_riesgo": "B2",
        "relacion_comercial": "Regular",
        "ingresos_promedio_mensual": 450000000,  # $450M mensuales
        "patrimonio_estimado": 900000000,  # $900M
        "experiencia_crediticia": "Cliente nuevo en productos crediticios",
        "beneficios_disponibles": [
            "Proceso preferencial",
            "Asesoría financiera gratuita"
        ],
        "gestor_asignado": "Ana Vargas - Ejecutiva Comercial",
        "telefono_gestor": "605-456-7890",
        "observaciones": "Cliente en construcción de relación comercial. Potencial para productos crediticios."
    },

    "600789123-4": {
        "nombre": "Agropecuaria El Dorado S.A.S",
        "es_cliente": True,
        "fecha_vinculacion": "2018-05-22",
        "tiempo_relacion_anos": 6,
        "sector": "agricultura",
        "ciudad": "Villavicencio",
        "productos_actuales": ["Cuenta Corriente", "CDT $100M", "Crédito Agrícola $400M"],
        "score_interno_historico": 720,
        "clasificacion_riesgo": "A2",
        "relacion_comercial": "Muy Buena",
        "ingresos_promedio_mensual": 600000000,  # $600M mensuales (estacional)
        "patrimonio_estimado": 5000000000,  # $5.000M (terrenos + ganado)
        "experiencia_crediticia": "Cliente tradicional del sector, pagos estacionales normales",
        "beneficios_disponibles": [
            "Tasa preferencial sector (-1%)",
            "Débito automático (-0.5%)",
            "Períodos de gracia estacionales",
            "Sin comisión estudio"
        ],
        "gestor_asignado": "Roberto Molina - Especialista Agro",
        "telefono_gestor": "608-567-8901",
        "observaciones": "Cliente sector agropecuario con comportamiento estacional predecible y responsable."
    },

    # EMPRESAS NO CLIENTES
    "500234567-8": {
        "nombre": "Innovaciones Tecnológicas SAS",
        "es_cliente": False,
        "motivo": "Empresa nueva en el mercado, constituida hace 8 meses",
        "sector_identificado": "tecnologia",
        "ciudad_identificada": "Medellín",
        "observaciones": "Startup en crecimiento, sin historial crediticio con la entidad"
    },

    "400345678-9": {
        "nombre": "Transporte y Logística Nacional Ltda", 
        "es_cliente": False,
        "motivo": "Empresa conocida del mercado pero sin productos con nuestra entidad",
        "sector_identificado": "transporte",
        "ciudad_identificada": "Bogotá",
        "observaciones": "Empresa establecida en el sector transporte, cliente potencial"
    },

    "300456789-0": {
        "nombre": "Servicios Integrales del Pacífico S.A",
        "es_cliente": False,
        "motivo": "NIT no encontrado en nuestras bases de datos",
        "observaciones": "Empresa nueva o con información incompleta"
    }
}

def consultar_cliente(nit):
    """
    Simula la consulta a la base de datos interna de la entidad financiera
    
    Args:
        nit (str): NIT de la empresa a consultar
        
    Returns:
        dict: Información del cliente o indicación de no encontrado
    """
    # Limpiar el NIT de espacios y caracteres especiales
    nit_limpio = nit.strip().replace("-", "").replace(".", "").replace(" ", "")
    
    # Agregar guión antes del último dígito si no lo tiene
    if len(nit_limpio) >= 9 and "-" not in nit:
        nit_formateado = f"{nit_limpio[:-1]}-{nit_limpio[-1]}"
    else:
        nit_formateado = nit
    
    # Buscar en la base de datos
    cliente = CLIENTES_BD.get(nit_formateado)
    
    if cliente:
        return cliente
    else:
        # Generar respuesta para NIT no encontrado
        return {
            "nombre": "Empresa no identificada",
            "es_cliente": False,
            "motivo": "NIT no encontrado en nuestra base de datos",
            "observaciones": "Empresa nueva o información por verificar"
        }

def obtener_estadisticas_bd():
    """
    Obtiene estadísticas generales de la base de datos para reporting
    """
    clientes_activos = sum(1 for c in CLIENTES_BD.values() if c.get("es_cliente", False))
    prospectos = sum(1 for c in CLIENTES_BD.values() if not c.get("es_cliente", False))
    
    sectores = {}
    for cliente in CLIENTES_BD.values():
        if cliente.get("es_cliente", False):
            sector = cliente.get("sector", "no_definido")
            sectores[sector] = sectores.get(sector, 0) + 1
    
    return {
        "total_registros": len(CLIENTES_BD),
        "clientes_activos": clientes_activos,
        "prospectos": prospectos,
        "sectores_activos": sectores
    }