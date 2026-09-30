# Contrato spec.json v1

Todos los objetos rechazan campos desconocidos y claves JSON duplicadas. Cada feature requiere sus cinco archivos Markdown y spec.json.

- schema_version: 1
- id: igual al nombre del directorio
- title: texto no vacío
- status: draft, ready o implemented
- requirements: lista no vacía de {id: R-001, statement: texto}
- acceptance: lista no vacía de {id: AC-001, requirement_ids: [R-001], given, when, then, test_refs: [{path, assertion}]}
- tasks: lista no vacía de {id: T-001, title, requirement_ids: [R-001], acceptance_ids: [AC-001], status: todo|doing|done}

Los IDs son únicos dentro de la feature; se reutilizan entre features. Cada requisito debe estar en un criterio y una tarea. Cada criterio debe estar en una tarea. Una tarea debe listar todos los requisitos asociados con sus criterios. No se permiten referencias desconocidas, duplicadas o vacías.

Las rutas son relativas al proyecto, no al directorio de feature. Sin rutas absolutas, .., separadores invertidos, directorios .git ni enlaces simbólicos. Cada referencia debe apuntar a un archivo real. assertion es una descripción legible de la aserción, no código ejecutable.

Draft permite [TODO] y test_refs vacío. --strict o estado ready/implemented exige documentos sin [TODO]/{{ y referencias de prueba no vacías. implemented además exige todas las tareas done. El validador no verifica un informe de ejecución ni su contenido; no se deben interpretar estos estados como certificaciones automáticas.

Se revisa el contenido JSON y presencia de documentos; no se extraen automáticamente requisitos del Markdown. Si se cambia la narrativa, una persona debe verificar que siga coherente con el contrato. Los cambios de alcance se documentan en change.md.
