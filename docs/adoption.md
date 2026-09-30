# Adopción segura

## Proyecto existente

Trabajar en una rama limpia y guardar un commit/backup antes de aplicar. El directorio destino debe existir. Ejecutar dry-run, revisar cada ADD/UPDATE y luego repetir con --apply. Se crea .specify/project.json con el adaptador; personalizar commands y specs_dir. No se leen ni ejecutan scripts del proyecto.

Sin --github todo el contenido nuevo queda bajo .specify/. El payload incorpora .gitattributes para conservar hashes en clones con core.autocrlf. Con --github se crean además .github/.gitattributes (reglas limitadas a los archivos del kit), .github/ISSUE_TEMPLATE/spec-feature.md, .github/pull_request_template.md y .github/workflows/spec-validation.yml. Las colisiones bloquean toda la instalación aunque el contenido sea idéntico; no se asume propiedad. Si el proyecto ya tiene esos archivos, no use --github e integre los fragmentos manualmente. El workflow propone main; ajustar para otra rama.

El snippet AGENTS.md siempre queda en .specify/assets/AGENTS.md; combinar a mano con las instrucciones actuales. No se modifica el AGENTS.md raíz.

## Proyecto nuevo

Crear un directorio/repo vacío o usar el template GitHub si está habilitado. Este repositorio es la distribución del starter, no un esqueleto de Laravel/React. Instale el kit en el repositorio de su aplicación y mantenga la documentación de su producto allí.

## Actualizaciones

Usar el CLI de una versión nueva, no esperar que el CLI instalado descargue nada. Revisar procedencia y cambios; los hashes no son firmas. update verifica el manifest, cada archivo administrado, ausencia de downgrade y consistencia de la versión. Se permiten cambios solo en archivos cuyo contenido aún coincide con el hash registrado. Ediciones locales, eliminaciones o rutas retiradas por el release requieren revisión manual. No hay eliminación automática ni force. La configuración y specs son del proyecto.

Si una plantilla necesita personalización permanente, copie la información a la feature o mantenga una rama del starter. Un cambio deliberado en .specify/templates bloqueará posteriores updates hasta reconciliarlo. Nunca cambie hashes a ciegas.

## Recuperación

El bloqueo es cooperativo, no protege contra otros editores. No ejecutar simultáneamente instalación y edición. Ante error normal de E/S se intenta revertir los archivos escritos; caída del proceso o energía puede dejar aplicación parcial. Revisar git diff, restaurar con su mecanismo normal de Git/backup y revisar el lock antes de retirarlo. El programa no ejecuta comandos destructivos de recuperación.

## Alcance v0.1

No incluye ejecutor de tareas, IA, inferencia semántica, auto-merge, despliegue, SDK oficial Spec Kit, firma de releases ni distribución en registros. Es un repositorio reutilizable y un instalador local, extensible mediante adaptadores de comandos informativos.
