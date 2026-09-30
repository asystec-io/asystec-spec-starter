# Asystec Spec Starter

Un starter reutilizable para convertir una necesidad en una especificación revisable, un plan, tareas y criterios de aceptación trazables. Úselo en proyectos nuevos o existentes, independientemente del lenguaje de la aplicación.

**v0.1.0 · Python 3.11+ · sin dependencias externas · MIT**

No es un generador automático de aplicaciones ni un verificador de corrección semántica. Una validación verde solo confirma estructura y referencias declaradas.

## Inicio rápido

Clone este repositorio y revise el código/versionado antes de ejecutarlo. El destino debe existir.

```sh
git clone https://github.com/asystec-io/asystec-spec-starter.git
cd asystec-spec-starter
python3 kit/specctl.py install --target /ruta/a/mi-proyecto
python3 kit/specctl.py install --target /ruta/a/mi-proyecto --apply
cd /ruta/a/mi-proyecto
python3 .specify/specctl.py new 001-mi-feature --target .
python3 .specify/specctl.py new 001-mi-feature --target . --apply
python3 .specify/specctl.py validate --target .
```

Primero se muestra el plan: install, update y new no escriben sin --apply. Nunca ejecutar desde una fuente desconocida ni con sudo.

Para Laravel: agregar --adapter laravel a la instalación inicial. Para instalar también plantillas de issue/PR y workflow de validación: agregar --github al dry-run y al --apply. No se modifica composer.json, package.json, código ni dependencias de la aplicación. AGENTS.md se proporciona como fragmento para integrar manualmente.

## Qué incluye

- Plantillas españolas: spec.md, plan.md, tasks.md, acceptance.md y change.md
- spec.json como contrato de IDs R-xxx → AC-xxx → T-xxx y referencias a pruebas
- CLI instalable dentro del repositorio, sin servicio externo ni API keys
- Configuración por proyecto; adaptadores generic y laravel de comandos informativos
- Instalación/actualización con manifiesto de versión y SHA-256; conflictos bloquean antes de escribir
- Ejemplo completo y pruebas de CLI/instalación/validación
- Plantillas GitHub y CI con permisos de lectura, sin secretos ni publicación automática

## Flujo recomendado

1. Redactar problema, alcance, requisitos y casos límite
2. Resolver preguntas y revisar la especificación con una persona
3. Diseñar plan y tareas vinculadas a requisitos/criterios
4. Implementar un cambio pequeño y escribir pruebas reales
5. Actualizar referencias y ejecutar validación + pruebas del proyecto
6. Revisar aceptación, evidencia y riesgos; registrar cambios de alcance

Consulte [la guía](kit/GUIDE.md), [el contrato](docs/contract.md), [el ejemplo](examples/001-export-report/) y [la adopción/actualización](docs/adoption.md).

## Validación y evidencia

```sh
python3 .specify/specctl.py validate --target . --strict
python3 .specify/specctl.py commands --target .
```

--strict exige al menos una feature, documentos sin placeholders reconocidos y referencias de archivos existentes. Los estados ready/implemented aplican esa completitud por feature. Solo implemented exige tareas done. Ni el CLI ni CI interpretan que los requisitos sean buenos, ejecutan las pruebas citadas o prueban que la implementación las cumpla. Las pruebas reales se ejecutan por separado, con los comandos propios del proyecto.

## Actualizar sin perder personalizaciones

```sh
python3 /ruta/al/nuevo-starter/kit/specctl.py update --target /ruta/a/mi-proyecto
python3 /ruta/al/nuevo-starter/kit/specctl.py update --target /ruta/a/mi-proyecto --apply
```

El nuevo checkout debe tener otra versión para cambios del payload. Si un archivo administrado fue modificado/eliminado, la operación se detiene. project.json y las especificaciones del proyecto nunca se actualizan desde el paquete. No hay --force; no se eliminan archivos. Ver limitaciones de concurrencia y recuperación en la guía.

## Desarrollo del starter

```sh
python3 -m unittest discover -s tests -v
python3 tools/release_manifest.py --check
```

CI prueba Python 3.11, 3.12 y 3.13. No se distribuye en PyPI/npm/Packagist. La versión se consume mediante un checkout revisado del repositorio. El ejemplo es ficticio y no contiene datos de clientes.

## Compatibilidad

El paquete usa .specify/, que también usa GitHub Spec Kit. Ambos son independientes: no instalar encima sin revisar colisiones. El instalador conserva archivos ajenos y bloquea cualquier ruta que necesita pero no administra. El uso como template GitHub depende de que esa opción esté habilitada en el repositorio; clonar/instalar funciona sin ella.

## Licencia

[MIT](LICENSE). Contribuciones mediante pull request; describir especificación, pruebas y riesgos.
