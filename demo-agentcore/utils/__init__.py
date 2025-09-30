# utils/__init__.py
# Inicialización del paquete utils

# Importar funciones principales de utils.py original
from .main_utils import clean_markdown, parse_json

# Importar funciones del verificador
from .verificador_utils import (
    construir_input_verificador,
    extraer_nit_de_mensaje, 
    validar_formato_nit,
    procesar_respuesta_verificador
)

# Importar funciones del buró
from .buro_utils import (
    construir_input_buro,
    procesar_respuesta_buro,
    combinar_analisis_interno_buro
)

__all__ = [
    # Funciones principales
    'clean_markdown',
    'parse_json',
    # Funciones del verificador
    'construir_input_verificador',
    'extraer_nit_de_mensaje',
    'validar_formato_nit', 
    'procesar_respuesta_verificador',
    # Funciones del buró
    'construir_input_buro',
    'procesar_respuesta_buro',
    'combinar_analisis_interno_buro'
]
