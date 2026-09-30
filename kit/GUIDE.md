# Guía del proyecto

Flujo: problema → spec → revisión humana → plan → tareas → implementación → pruebas → aceptación.

- Configuración local: .specify/project.json. Editar commands y specs_dir según el proyecto.
- Crear feature: python3 .specify/specctl.py new 001-mi-feature --target . (vista previa); repetir con --apply.
- Validar estructura: python3 .specify/specctl.py validate --target .
- Exigir borradores completos/evidencia existente: agregar --strict.
- Ver comandos del adaptador: python3 .specify/specctl.py commands --target .

El CLI muestra comandos; no los ejecuta. El adaptador Laravel propone php artisan test y vendor/bin/pint --test. Deben existir PHP, dependencias y configuración del propio proyecto. El genérico deja commands vacío para evitar supuestos.

Cada feature incluye spec.md, plan.md, tasks.md, acceptance.md, change.md y spec.json. Los IDs y relaciones se definen en JSON; los Markdown contienen contexto y decisiones. El validador no interpreta ni sincroniza semánticamente los documentos.

Estados: draft admite placeholders y criterios sin referencias de prueba; ready e implemented exigen documentos sin [TODO], referencias no vacías y archivos existentes. implemented además exige tareas done. --strict aplica requisitos de completitud incluso a draft. No exige que el estado sea implemented ni ejecuta pruebas. Actualizar el estado es una afirmación humana, no una certificación.

Cada R necesita AC y T; cada AC necesita T. Los test_refs son rutas relativas de archivos reales y una descripción de la aserción; su existencia no demuestra que contengan o ejecuten esa aserción. Cada T debe listar todos los requisitos de sus AC. IDs: R-001, AC-001, T-001 (tres o más dígitos).

Actualizar desde un checkout verificado de una versión nueva: python3 /ruta/al/starter/kit/specctl.py update --target .; revisar y repetir con --apply. Los archivos administrados modificados o ausentes bloquean toda la actualización. project.json y tus specs se conservan. No modificar el manifest para forzar una actualización. Copiar ediciones y resolver en una rama de trabajo revisable.

Los snippets de GitHub solo se activan al instalar con --github. Revisar permisos/rama principal y compatibilidad antes de aplicar; CI de estructura no sustituye CI de pruebas. AGENTS.md se entrega como snippet en .specify/assets/AGENTS.md para integrarlo manualmente sin sobrescribir instrucciones existentes.

Seguridad: no ejecutar con permisos elevados; usar una copia de trabajo estable y sin escritores concurrentes. Dry-run no escribe. El instalador rechaza rutas inseguras, enlaces simbólicos, colisiones y versiones anteriores. Usa bloqueo cooperativo y escrituras atómicas por archivo donde reemplaza archivos gestionados; no es una transacción de sistema de archivos ni una barrera contra un proceso hostil que cambie rutas simultáneamente. Si una operación se interrumpe por corte de energía, restaurar desde Git/backup y revisar .specify-install.lock. Los hashes detectan cambios, no autentican al autor del release.

Este starter usa .specify/, también utilizado por otras herramientas como GitHub Spec Kit. No es un plugin oficial de Spec Kit y no garantiza interoperabilidad: revise colisiones y flujos antes de combinarlos. No copiar su contenido encima de una instalación existente.
