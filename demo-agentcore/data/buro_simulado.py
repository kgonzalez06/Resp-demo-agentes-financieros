# data/buro_simulado.py
# Simulación de consultas a centrales de riesgo colombianas (DataCrédito, Experian)

import random
from datetime import datetime, timedelta

REPORTES_BURO = {
    # CLIENTES EXISTENTES DE NUESTRO BANCO
    "900123456-7": {  # Constructora Los Andes - Cliente premium
        "entidad_consultora": "DataCrédito Experian",
        "fecha_consulta": "2024-09-12",
        "score_externo": 745,
        "categoria_riesgo": "A1",  # A1=Excelente, A2=Muy Bueno, B1=Bueno, B2=Aceptable, C1=Regular, C2=Deficiente, D=Malo
        "calificacion": "AA",
        "comportamiento_12m": "Normal",
        "comportamiento_24m": "Normal", 
        "historial_pagos": "Cumplidor en todas las obligaciones últimos 24 meses",
        "deudas_sistema_financiero": {
            "total_deudas": 850000000,  # $850M
            "numero_entidades": 4,
            "detalle_por_entidad": [
                {"banco": "Banco de Bogotá", "monto": 400000000, "tipo": "Crédito Comercial", "comportamiento": "Normal"},
                {"banco": "Bancolombia", "monto": 250000000, "tipo": "Leasing", "comportamiento": "Normal"},
                {"banco": "Davivienda", "monto": 150000000, "tipo": "Tarjeta Crédito", "comportamiento": "Normal"},
                {"banco": "NUESTRA ENTIDAD", "monto": 50000000, "tipo": "Rotativo", "comportamiento": "Normal"}
            ]
        },
        "reportes_negativos": [],
        "demandas_ejecutivas": [],
        "embargos_vigentes": [],
        "concordatos": [],
        "experiencia_crediticia": "15 años en sistema financiero",
        "ultima_actualizacion": "2024-09-10",
        "observaciones_buro": "Empresa sólida con excelente comportamiento crediticio histórico",
        "recomendacion_buro": "FAVORABLE - Sin restricciones para otorgamiento de crédito",
        "alertas": [],
        "score_industria": "Por encima del promedio del sector construcción (720)"
    },

    "800987654-3": {  # Textiles del Valle - Cliente bueno con mora menor
        "entidad_consultora": "DataCrédito Experian", 
        "fecha_consulta": "2024-09-12",
        "score_externo": 625,
        "categoria_riesgo": "B1",
        "calificacion": "A-",
        "comportamiento_12m": "Normal con 1 incidencia menor",
        "comportamiento_24m": "Normal",
        "historial_pagos": "1 mora de 18 días en marzo 2024, resto normal",
        "deudas_sistema_financiero": {
            "total_deudas": 320000000,  # $320M
            "numero_entidades": 3,
            "detalle_por_entidad": [
                {"banco": "Bancolombia", "monto": 180000000, "tipo": "Crédito Comercial", "comportamiento": "Normal"},
                {"banco": "NUESTRA ENTIDAD", "monto": 100000000, "tipo": "Factoring", "comportamiento": "Normal"},
                {"banco": "Banco Popular", "monto": 40000000, "tipo": "Tarjeta Crédito", "comportamiento": "Mora reportada marzo 2024"}
            ]
        },
        "reportes_negativos": [
            {
                "fecha": "2024-03-15",
                "entidad": "Banco Popular",
                "monto": 40000000,
                "tipo": "Mora mayor a 15 días",
                "estado": "Normalizada",
                "observacion": "Mora de 18 días, normalizada el 2024-04-02"
            }
        ],
        "demandas_ejecutivas": [],
        "embargos_vigentes": [],
        "concordatos": [],
        "experiencia_crediticia": "8 años en sistema financiero",
        "ultima_actualizacion": "2024-09-08",
        "observaciones_buro": "Empresa con comportamiento general bueno, incidencia menor reciente ya normalizada",
        "recomendacion_buro": "FAVORABLE CON OBSERVACIONES - Considerar mora menor reciente",
        "alertas": ["Mora normalizada hace 5 meses"],
        "score_industria": "En promedio del sector textil (630)"
    },

    "700456789-1": {  # Distribuidora del Caribe - Cliente nuevo con poco historial
        "entidad_consultora": "DataCrédito Experian",
        "fecha_consulta": "2024-09-12", 
        "score_externo": 580,
        "categoria_riesgo": "B2",
        "calificacion": "BBB+",
        "comportamiento_12m": "Normal",
        "comportamiento_24m": "Información limitada",
        "historial_pagos": "Experiencia crediticia limitada, pagos normales en productos básicos",
        "deudas_sistema_financiero": {
            "total_deudas": 85000000,  # $85M
            "numero_entidades": 2,
            "detalle_por_entidad": [
                {"banco": "NUESTRA ENTIDAD", "monto": 50000000, "tipo": "Sobregiro", "comportamiento": "Normal"},
                {"banco": "Banco Agrario", "monto": 35000000, "tipo": "Microcrédito", "comportamiento": "Normal"}
            ]
        },
        "reportes_negativos": [],
        "demandas_ejecutivas": [],
        "embargos_vigentes": [],
        "concordatos": [],
        "experiencia_crediticia": "3 años en sistema financiero",
        "ultima_actualizacion": "2024-09-05",
        "observaciones_buro": "Empresa en construcción de historial crediticio, sin incidencias negativas",
        "recomendacion_buro": "FAVORABLE - Empresa emergente sin antecedentes negativos", 
        "alertas": ["Historial crediticio corto"],
        "score_industria": "Levemente bajo para sector comercio (600)"
    },

    "600789123-4": {  # Agropecuaria El Dorado - Cliente sector agro
        "entidad_consultora": "DataCrédito Experian",
        "fecha_consulta": "2024-09-12",
        "score_externo": 690,
        "categoria_riesgo": "A2",
        "calificacion": "A",
        "comportamiento_12m": "Normal",
        "comportamiento_24m": "Normal con estacionalidad",
        "historial_pagos": "Comportamiento estacional típico del sector, cumplidor en fechas acordadas",
        "deudas_sistema_financiero": {
            "total_deudas": 1200000000,  # $1.200M
            "numero_entidades": 3,
            "detalle_por_entidad": [
                {"banco": "Banco Agrario", "monto": 600000000, "tipo": "Crédito Agrícola", "comportamiento": "Normal"},
                {"banco": "NUESTRA ENTIDAD", "monto": 400000000, "tipo": "Crédito Comercial", "comportamiento": "Normal"},
                {"banco": "Finagro", "monto": 200000000, "tipo": "Redescuento", "comportamiento": "Normal"}
            ]
        },
        "reportes_negativos": [],
        "demandas_ejecutivas": [],
        "embargos_vigentes": [],
        "concordatos": [],
        "experiencia_crediticia": "12 años en sistema financiero",
        "ultima_actualizacion": "2024-09-07",
        "observaciones_buro": "Empresa del sector agropecuario con comportamiento responsable y predecible",
        "recomendacion_buro": "FAVORABLE - Empresa consolidada del sector agropecuario",
        "alertas": [],
        "score_industria": "Por encima del promedio del sector agropecuario (665)"
    },

    # EMPRESAS NO CLIENTES NUESTRAS
    "500234567-8": {  # Innovaciones Tecnológicas - Startup
        "entidad_consultora": "DataCrédito Experian",
        "fecha_consulta": "2024-09-12",
        "score_externo": 520,
        "categoria_riesgo": "C1",
        "calificacion": "BBB",
        "comportamiento_12m": "Información insuficiente",
        "comportamiento_24m": "Sin información",
        "historial_pagos": "Empresa nueva, sin historial crediticio significativo",
        "deudas_sistema_financiero": {
            "total_deudas": 35000000,  # $35M
            "numero_entidades": 1,
            "detalle_por_entidad": [
                {"banco": "Bancolombia", "monto": 35000000, "tipo": "Tarjeta Crédito Empresarial", "comportamiento": "Normal"}
            ]
        },
        "reportes_negativos": [],
        "demandas_ejecutivas": [],
        "embargos_vigentes": [],
        "concordatos": [],
        "experiencia_crediticia": "8 meses en sistema financiero",
        "ultima_actualizacion": "2024-09-01",
        "observaciones_buro": "Startup sin historial crediticio suficiente para evaluación robusta",
        "recomendacion_buro": "OBSERVAR - Empresa nueva requiere análisis de flujo de caja y proyecciones",
        "alertas": ["Empresa de reciente constitución", "Historial crediticio insuficiente"],
        "score_industria": "Sin referencia sectorial suficiente"
    },

    "400345678-9": {  # Transporte y Logística - Empresa con algunos problemas
        "entidad_consultora": "DataCrédito Experian",
        "fecha_consulta": "2024-09-12",
        "score_externo": 450,
        "categoria_riesgo": "C2",
        "calificacion": "BB",
        "comportamiento_12m": "Irregular",
        "comportamiento_24m": "Regular con incidencias",
        "historial_pagos": "3 moras mayores a 30 días en últimos 18 meses, 1 normalizada",
        "deudas_sistema_financiero": {
            "total_deudas": 750000000,  # $750M
            "numero_entidades": 4,
            "detalle_por_entidad": [
                {"banco": "Banco de Bogotá", "monto": 350000000, "tipo": "Crédito Comercial", "comportamiento": "Mora 45 días"},
                {"banco": "Bancolombia", "monto": 200000000, "tipo": "Leasing Vehículos", "comportamiento": "Normal"},
                {"banco": "Davivienda", "monto": 150000000, "tipo": "Capital de Trabajo", "comportamiento": "Normalizada"},
                {"banco": "Banco Popular", "monto": 50000000, "tipo": "Tarjeta Crédito", "comportamiento": "Mora 15 días"}
            ]
        },
        "reportes_negativos": [
            {
                "fecha": "2024-07-20",
                "entidad": "Banco de Bogotá",
                "monto": 350000000,
                "tipo": "Mora mayor a 30 días",
                "estado": "Vigente",
                "observacion": "Mora de 45 días vigente"
            },
            {
                "fecha": "2023-11-10", 
                "entidad": "Davivienda",
                "monto": 150000000,
                "tipo": "Mora mayor a 60 días",
                "estado": "Normalizada",
                "observacion": "Mora normalizada en enero 2024"
            }
        ],
        "demandas_ejecutivas": [],
        "embargos_vigentes": [],
        "concordatos": [],
        "experiencia_crediticia": "6 años en sistema financiero",
        "ultima_actualizacion": "2024-09-09",
        "observaciones_buro": "Empresa con dificultades de flujo de caja recientes, mora vigente significativa",
        "recomendacion_buro": "DESFAVORABLE - Mora vigente y comportamiento irregular",
        "alertas": ["Mora vigente superior a 30 días", "Comportamiento irregular últimos 18 meses"],
        "score_industria": "Por debajo del promedio del sector transporte (510)"
    },

    # CASOS ESPECIALES
    "100987654-3": {  # Empresa con problemas graves
        "entidad_consultora": "DataCrédito Experian",
        "fecha_consulta": "2024-09-12",
        "score_externo": 280,
        "categoria_riesgo": "D",
        "calificacion": "C",
        "comportamiento_12m": "Deficiente",
        "comportamiento_24m": "Deficiente",
        "historial_pagos": "Múltiples moras, demanda ejecutiva vigente",
        "deudas_sistema_financiero": {
            "total_deudas": 450000000,  # $450M
            "numero_entidades": 3,
            "detalle_por_entidad": [
                {"banco": "Banco de Bogotá", "monto": 250000000, "tipo": "Crédito Comercial", "comportamiento": "En demanda"},
                {"banco": "Bancolombia", "monto": 150000000, "tipo": "Capital de Trabajo", "comportamiento": "Mora 120 días"},
                {"banco": "Davivienda", "monto": 50000000, "tipo": "Sobregiro", "comportamiento": "Castigado"}
            ]
        },
        "reportes_negativos": [
            {
                "fecha": "2024-02-15",
                "entidad": "Banco de Bogotá", 
                "monto": 250000000,
                "tipo": "Demanda ejecutiva",
                "estado": "Vigente",
                "observacion": "Proceso ejecutivo en curso"
            }
        ],
        "demandas_ejecutivas": [
            {
                "fecha": "2024-02-15",
                "entidad": "Banco de Bogotá",
                "monto": 250000000,
                "estado": "En proceso",
                "juzgado": "Juzgado 15 Civil Circuito Bogotá"
            }
        ],
        "embargos_vigentes": [
            {
                "fecha": "2024-03-10", 
                "tipo": "Embargo preventivo",
                "monto": 250000000,
                "bien": "Cuenta corriente"
            }
        ],
        "concordatos": [],
        "experiencia_crediticia": "4 años en sistema financiero",
        "ultima_actualizacion": "2024-09-11",
        "observaciones_buro": "Empresa en situación financiera crítica con procesos legales vigentes",
        "recomendacion_buro": "RECHAZAR - Alto riesgo crediticio",
        "alertas": ["Demanda ejecutiva vigente", "Embargo preventivo", "Múltiples moras"],
        "score_industria": "Muy por debajo del promedio sectorial"
    }
}

def consultar_buro(nit):
    """
    Simula la consulta a centrales de riesgo colombianas
    
    Args:
        nit (str): NIT de la empresa a consultar
        
    Returns:
        dict: Reporte completo de buró o None si no existe información
    """
    # Limpiar el NIT
    nit_limpio = nit.strip().replace("-", "").replace(".", "").replace(" ", "")
    
    # Formatear NIT
    if len(nit_limpio) >= 9 and "-" not in nit:
        nit_formateado = f"{nit_limpio[:-1]}-{nit_limpio[-1]}"
    else:
        nit_formateado = nit
    
    # Buscar en reportes de buró
    reporte = REPORTES_BURO.get(nit_formateado)
    
    if reporte:
        return reporte
    else:
        # Generar reporte básico para empresa sin historial
        return {
            "entidad_consultora": "DataCrédito Experian",
            "fecha_consulta": datetime.now().strftime("%Y-%m-%d"),
            "score_externo": None,
            "categoria_riesgo": "SIN INFORMACIÓN",
            "calificacion": "NR",  # No Reporta
            "comportamiento_12m": "Sin información",
            "comportamiento_24m": "Sin información",
            "historial_pagos": "Empresa sin historial en centrales de riesgo",
            "deudas_sistema_financiero": {
                "total_deudas": 0,
                "numero_entidades": 0,
                "detalle_por_entidad": []
            },
            "reportes_negativos": [],
            "demandas_ejecutivas": [],
            "embargos_vigentes": [],
            "concordatos": [],
            "experiencia_crediticia": "Sin experiencia reportada",
            "ultima_actualizacion": "N/A",
            "observaciones_buro": "Empresa sin información en centrales de riesgo",
            "recomendacion_buro": "ANALIZAR - Sin historial crediticio para evaluar",
            "alertas": ["Sin información en centrales de riesgo"],
            "score_industria": "Sin referencia"
        }

def interpretar_score_buro(score):
    """
    Interpreta el score de buró según estándares colombianos
    """
    if score is None:
        return "Sin información suficiente"
    elif score >= 700:
        return "Excelente - Muy bajo riesgo"
    elif score >= 650:
        return "Bueno - Riesgo bajo"
    elif score >= 600:
        return "Aceptable - Riesgo medio-bajo"
    elif score >= 550:
        return "Regular - Riesgo medio"
    elif score >= 450:
        return "Deficiente - Riesgo alto"
    else:
        return "Malo - Riesgo muy alto"

def obtener_resumen_buro(nit):
    """
    Obtiene un resumen ejecutivo del reporte de buró
    """
    reporte = consultar_buro(nit)
    
    if not reporte:
        return None
    
    score = reporte.get("score_externo")
    interpretacion_score = interpretar_score_buro(score)
    
    # Calcular indicadores de riesgo
    tiene_moras_vigentes = any(r.get("estado") == "Vigente" for r in reporte.get("reportes_negativos", []))
    tiene_demandas = len(reporte.get("demandas_ejecutivas", [])) > 0
    tiene_embargos = len(reporte.get("embargos_vigentes", [])) > 0
    
    nivel_riesgo = "BAJO"
    if tiene_demandas or tiene_embargos or score and score < 400:
        nivel_riesgo = "ALTO"
    elif tiene_moras_vigentes or score and score < 550:
        nivel_riesgo = "MEDIO"
    
    return {
        "score": score,
        "interpretacion_score": interpretacion_score,
        "categoria_riesgo": reporte.get("categoria_riesgo"),
        "nivel_riesgo": nivel_riesgo,
        "total_deudas": reporte.get("deudas_sistema_financiero", {}).get("total_deudas", 0),
        "numero_entidades": reporte.get("deudas_sistema_financiero", {}).get("numero_entidades", 0),
        "tiene_moras_vigentes": tiene_moras_vigentes,
        "tiene_demandas": tiene_demandas,
        "tiene_embargos": tiene_embargos,
        "recomendacion": reporte.get("recomendacion_buro"),
        "alertas": reporte.get("alertas", []),
        "experiencia_anos": reporte.get("experiencia_crediticia", "").split()[0] if reporte.get("experiencia_crediticia") else "0"
    }