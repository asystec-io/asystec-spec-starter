# Plan

Una función pura build_report valida todos los registros antes de filtrar. Usa sorted para un resultado determinista y construye nuevas estructuras; no modifica la entrada.

No requiere dependencias. El contrato documenta orden lexicográfico en vez de asumir locale. Tests unittest cubren AC-001 (filtro, orden, conteo e inmutabilidad) y AC-002 (vacío y entradas inválidas).

No hay migración ni despliegue. Reversión del ejemplo: restaurar el commit anterior. Para una aplicación real, definir autenticación, límites de tamaño y observabilidad en una especificación propia.
