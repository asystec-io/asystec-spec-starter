# Asystec Spec Starter

Paquete genérico público; no incluir datos internos ni código de proyectos privados.

- Requisitos: Python 3.11+; solo biblioteca estándar.
- CLI y payload distribuido: kit/. No editar artefactos de proyectos ajenos.
- Ejecutar: python3 -m unittest discover -s tests -v
- Regenerar hashes tras cambiar kit/: python3 tools/release_manifest.py
- Verificar: python3 tools/release_manifest.py --check
- Conservar seguridad: dry-run por defecto, --apply explícito, colisiones bloqueantes, configuración de proyecto preservada, rutas relativas sin symlinks.
- Toda feature del starter requiere pruebas de regresión. La validación de spec.json no demuestra corrección semántica.
- Evitar dependencias, llamadas de red, ejecución de comandos configurados y modificaciones fuera del destino.
- No publicar en registros de paquetes ni hacer despliegues como parte de tests.
