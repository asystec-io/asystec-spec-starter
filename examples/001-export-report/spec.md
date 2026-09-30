# Reporte determinista de etiquetas activas

Ejemplo ficticio para enseñar trazabilidad. Consumidor: una función que necesita una vista JSON estable de etiquetas activas. R-001 filtra y ordena sin mutar datos; R-002 define validación y entrada vacía.

Alcance: función pura en Python, sin archivos, red, usuarios ni datos reales. Fuera de alcance: API HTTP, autenticación, base de datos, exportación CSV y ordenación por idioma. Comparación lexicográfica estándar, sensible a mayúsculas. No normaliza espacios ni deduplica nombres.

Datos: lista de objetos con exactamente name (texto no vacío tras strip) y active (booleano). Resultado: active_count y names. Un registro inválido invalida la petición completa. Riesgo: la función no es un contrato general para bases de datos externas.

Este ejemplo es pedagógico; adaptar y someter a revisión de producto antes de reutilizar su comportamiento.
