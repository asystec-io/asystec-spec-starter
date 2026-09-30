#!/usr/bin/env python3
"""Asystec Spec Starter: dependency-free, conservative repository scaffolding."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile

VERSION = "0.1.0"
SCHEMA = 1
PACKAGE = "asystec-spec-starter"
MAX_JSON = 2 * 1024 * 1024


class SpecError(Exception):
    """Expected input or safety error."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def read_json(path: Path):
    try:
        if not path.is_file() or path.is_symlink():
            raise SpecError(f"Se requiere un archivo regular sin enlaces: {path}")
        if path.stat().st_size > MAX_JSON:
            raise SpecError(f"JSON demasiado grande: {path}")
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    except (OSError, ValueError) as exc:
        raise SpecError(f"JSON inválido en {path}: {exc}") from exc


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"clave duplicada: {key}")
        result[key] = value
    return result


def relative(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or ":" in value or any(ord(c) < 32 for c in value):
        raise SpecError(f"Ruta relativa insegura: {value!r}")
    parts = value.split("/")
    if any(p in ("", ".", "..") or p.rstrip(" .") != p for p in parts):
        raise SpecError(f"Ruta relativa insegura: {value!r}")
    reserved = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
    if any(p.split(".")[0].lower() in reserved for p in parts):
        raise SpecError(f"Nombre reservado de sistema: {value!r}")
    if PurePosixPath(value).is_absolute() or any(p.lower() == ".git" for p in parts):
        raise SpecError(f"Ruta relativa insegura: {value!r}")
    return value


def no_symlinks(path: Path) -> None:
    for part in (path, *path.parents):
        if part.is_symlink():
            raise SpecError(f"No se permiten enlaces simbólicos: {part}")


def root_path(value: str) -> Path:
    path = Path(os.path.abspath(value))
    no_symlinks(path)
    if not path.is_dir():
        raise SpecError(f"El destino debe ser un directorio existente: {path}")
    return path


def safe_path(root: Path, name: str) -> Path:
    path = root.joinpath(*relative(name).split("/"))
    no_symlinks(path)
    for parent in path.parents:
        if parent == root:
            break
        if parent.exists() and not parent.is_dir():
            raise SpecError(f"Un archivo bloquea la ruta: {parent}")
    return path


def file_bytes(root: Path, name: str) -> bytes:
    path = safe_path(root, name)
    if not path.is_file():
        raise SpecError(f"Falta un archivo regular: {path}")
    return path.read_bytes()


def fields(value, required, optional=(), label="objeto"):
    if not isinstance(value, dict):
        raise SpecError(f"{label}: debe ser un objeto")
    missing = set(required) - value.keys()
    extra = value.keys() - set(required) - set(optional)
    if missing or extra:
        raise SpecError(f"{label}: faltan {sorted(missing)}; desconocidas {sorted(extra)}")


def text_field(value, label):
    if not isinstance(value, str) or not value.strip():
        raise SpecError(f"{label}: texto vacío o inválido")


def version_tuple(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d+\.\d+\.\d+", value):
        raise SpecError("Versión inválida")
    return tuple(map(int, value.split(".")))


def hashes(value, label):
    if not isinstance(value, dict) or not value:
        raise SpecError(f"{label}: mapa de archivos vacío o inválido")
    for name, checksum in value.items():
        relative(name)
        if not isinstance(checksum, str) or not re.fullmatch(r"[a-f0-9]{64}", checksum):
            raise SpecError(f"{label}: hash inválido para {name}")


def load_release(source: Path):
    no_symlinks(source)
    release = read_json(safe_path(source, "release.json"))
    fields(release, ("schema_version", "package", "version", "files"), label="release")
    if type(release["schema_version"]) is not int or release["schema_version"] != SCHEMA or release["package"] != PACKAGE:
        raise SpecError("Release incompatible")
    version_tuple(release["version"])
    if release["version"] != VERSION:
        raise SpecError("La versión del CLI y release.json no coincide")
    hashes(release["files"], "release")
    if "specctl.py" not in release["files"]:
        raise SpecError("Release sin specctl.py")
    payload = {}
    for name, expected in release["files"].items():
        if name in ("release.json", "manifest.json", "project.json"):
            raise SpecError(f"Ruta reservada en release: {name}")
        data = file_bytes(source, name)
        if digest(data) != expected:
            raise SpecError(f"Release alterado o desactualizado: {name}")
        payload[f".specify/{name}"] = data
    payload[".specify/release.json"] = json_bytes(release)
    return release, payload


def load_manifest(root: Path):
    path = safe_path(root, ".specify/manifest.json")
    if not path.exists():
        return None
    manifest = read_json(path)
    fields(manifest, ("schema_version", "package", "version", "release_sha256", "github", "files"), label="manifest")
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != SCHEMA or manifest["package"] != PACKAGE:
        raise SpecError("Manifest incompatible")
    version_tuple(manifest["version"])
    if type(manifest["github"]) is not bool:
        raise SpecError("manifest.github debe ser booleano")
    if not isinstance(manifest["release_sha256"], str) or not re.fullmatch(r"[a-f0-9]{64}", manifest["release_sha256"]):
        raise SpecError("Hash de release inválido en manifest")
    hashes(manifest["files"], "manifest")
    for name in manifest["files"]:
        if not (name.startswith(".specify/") or name.startswith(".github/")):
            raise SpecError(f"Manifest fuera del alcance permitido: {name}")
        if name in (".specify/manifest.json", ".specify/project.json"):
            raise SpecError(f"Archivo reservado en manifest: {name}")
    return manifest


def project_config(root: Path):
    config = read_json(safe_path(root, ".specify/project.json"))
    fields(config, ("schema_version", "adapter", "specs_dir", "commands"), label="project")
    if type(config["schema_version"]) is not int or config["schema_version"] != SCHEMA or config["adapter"] not in ("generic", "laravel"):
        raise SpecError("Configuración incompatible")
    name = relative(config["specs_dir"])
    if name.split("/")[0].startswith("."):
        raise SpecError("specs_dir no puede usar un directorio oculto/reservado")
    if not isinstance(config["commands"], dict):
        raise SpecError("commands debe ser un objeto")
    for key, command in config["commands"].items():
        text_field(key, "nombre de comando")
        if not isinstance(command, list) or not command or any(not isinstance(x, str) or not x for x in command):
            raise SpecError(f"Comando inválido: {key}; usar lista de argumentos")
    return config


def plan_install(root: Path, source: Path, command: str, github: bool, adapter: str):
    release, payload = load_release(source)
    previous = load_manifest(root)
    if command == "update" and previous is None:
        raise SpecError("No hay instalación administrada; use install")
    if previous:
        if github and not previous["github"]:
            raise SpecError("No se puede ampliar GitHub en una actualización; copie/revise los snippets manualmente")
        github = previous["github"]
        if version_tuple(release["version"]) < version_tuple(previous["version"]):
            raise SpecError("No se permiten downgrades")
        if release["version"] == previous["version"] and digest(json_bytes(release)) != previous["release_sha256"]:
            raise SpecError("Misma versión con contenido diferente; use una nueva versión")
        project_config(root)
    if github:
        prefix = ".specify/assets/github/"
        for name, data in list(payload.items()):
            if name.startswith(prefix):
                payload[".github/" + name[len(prefix):]] = data
    prior_files = previous["files"] if previous else {}
    # Never infer ownership from byte equality. Existing untracked paths collide.
    errors = []
    for name, expected in prior_files.items():
        path = safe_path(root, name)
        if not path.is_file() or digest(path.read_bytes()) != expected:
            errors.append(f"modificado o ausente: {name}")
    for name in payload:
        if name not in prior_files and safe_path(root, name).exists():
            errors.append(f"colisión no administrada: {name}")
    removed = set(prior_files) - payload.keys()
    if removed:
        errors.append("la nueva versión retira archivos; resolución manual requerida: " + ", ".join(sorted(removed)))
    if errors:
        raise SpecError("Instalación bloqueada; no se escribió nada:\n- " + "\n- ".join(errors))
    managed = {name: digest(data) for name, data in payload.items()}
    if previous is None:
        config_path = safe_path(root, ".specify/project.json")
        if config_path.exists():
            raise SpecError("Colisión no administrada: .specify/project.json")
        config = read_json(safe_path(source, f"adapters/{adapter}.json"))
        payload[".specify/project.json"] = json_bytes(config)
    manifest = {"schema_version": SCHEMA, "package": PACKAGE, "version": release["version"],
                "release_sha256": digest(json_bytes(release)), "github": github, "files": managed}
    payload[".specify/manifest.json"] = json_bytes(manifest)
    changes = {}
    for name, data in payload.items():
        path = safe_path(root, name)
        old = path.read_bytes() if path.is_file() else None
        if old != data:
            changes[name] = (old, data)
    return changes


def write_transaction(root: Path, changes):
    """Preflight all paths, write atomically per file, roll back ordinary I/O failures."""
    for name, (old, _) in changes.items():
        path = safe_path(root, name)
        current = path.read_bytes() if path.is_file() else None
        if current != old:
            raise SpecError(f"El destino cambió durante la operación: {name}")
    written = []
    made_dirs = []
    try:
        for name, (old, data) in changes.items():
            path = safe_path(root, name)
            missing = []
            parent = path.parent
            while not parent.exists():
                missing.append(parent)
                parent = parent.parent
            for directory in reversed(missing):
                directory.mkdir()
                made_dirs.append(directory)
            if old is not None and path.read_bytes() != old:
                raise SpecError(f"El destino cambió durante la operación: {name}")
            fd, temp = tempfile.mkstemp(prefix=".specctl-", dir=path.parent)
            try:
                with os.fdopen(fd, "wb") as handle:
                    if handle.write(data) != len(data):
                        raise OSError("Escritura incompleta")
                if old is None:
                    # Same-filesystem exclusive link publishes complete bytes only.
                    os.link(temp, path)
                else:
                    os.replace(temp, path)
            finally:
                if os.path.exists(temp):
                    os.unlink(temp)
            written.append(name)
    except Exception:
        for name in reversed(written):
            old, new = changes[name]
            path = root / name
            # Do not clobber another writer's later changes during rollback.
            if path.is_file() and not path.is_symlink() and path.read_bytes() == new:
                if old is None:
                    path.unlink()
                else:
                    path.write_bytes(old)
        for directory in reversed(made_dirs):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise


def install(args):
    root = root_path(args.target)
    source = Path(__file__).absolute().parent
    changes = plan_install(root, source, args.command, args.github, args.adapter)
    for name, (old, _) in changes.items():
        print(("ADD " if old is None else "UPDATE ") + name)
    if not args.apply:
        print(f"DRY RUN: {len(changes)} archivos; use --apply para escribir")
        return
    lock = safe_path(root, ".specify-install.lock")
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise SpecError("Otra instalación está activa o dejó .specify-install.lock; revise antes de retirarlo") from exc
    try:
        os.close(fd)
        changes = plan_install(root, source, args.command, args.github, args.adapter)
        write_transaction(root, changes)
    finally:
        lock.unlink()
    print(f"OK: {len(changes)} archivos escritos (versión {VERSION})")


def feature(args):
    root = root_path(args.target)
    config = project_config(root)
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.slug) or len(args.slug) > 80:
        raise SpecError("Use un slug kebab-case, máximo 80 caracteres")
    destination = f"{config['specs_dir']}/{args.slug}"
    if safe_path(root, destination).exists():
        raise SpecError(f"La feature ya existe: {destination}")
    changes = {}
    for name in ("spec.md", "plan.md", "tasks.md", "acceptance.md", "change.md", "spec.json"):
        data = file_bytes(root, ".specify/templates/" + name).decode("utf-8").replace("{{FEATURE_ID}}", args.slug).encode()
        changes[destination + "/" + name] = (None, data)
    # Serialize JSON placeholders before touching disk.
    json.loads(changes[destination + "/spec.json"][1])
    for name in changes:
        print("ADD " + name)
    if args.apply:
        write_transaction(root, changes)
        print("OK: feature creada como borrador; complete decisiones y criterios antes de implementar")
    else:
        print("DRY RUN: use --apply para escribir")


def records(value, prefix, required, label):
    if not isinstance(value, list) or not value:
        raise SpecError(f"{label}: lista vacía o inválida")
    ids = set()
    for row in value:
        fields(row, required, label=label)
        identifier = row["id"]
        if not isinstance(identifier, str) or not re.fullmatch(prefix + r"-[0-9]{3,}", identifier):
            raise SpecError(f"{label}: ID inválido {identifier!r}")
        if identifier in ids:
            raise SpecError(f"{label}: ID duplicado {identifier}")
        ids.add(identifier)
    return ids


def references(value, known, label):
    if not isinstance(value, list) or not value or any(not isinstance(x, str) for x in value):
        raise SpecError(f"{label}: referencias vacías o inválidas")
    if len(set(value)) != len(value) or not set(value) <= known:
        raise SpecError(f"{label}: referencias duplicadas o desconocidas")
    return set(value)


def validate_feature(root: Path, directory: Path, strict: bool):
    data = read_json(safe_path(root, (directory / "spec.json").relative_to(root).as_posix()))
    fields(data, ("schema_version", "id", "title", "status", "requirements", "acceptance", "tasks"), label=str(directory))
    if type(data["schema_version"]) is not int or data["schema_version"] != SCHEMA:
        raise SpecError("schema_version no soportado")
    if data["id"] != directory.name:
        raise SpecError("El id debe coincidir con el directorio de la feature")
    text_field(data["title"], "title")
    if data["status"] not in ("draft", "ready", "implemented"):
        raise SpecError("status debe ser draft, ready o implemented")
    enforce = strict or data["status"] != "draft"
    for name in ("spec.md", "plan.md", "tasks.md", "acceptance.md", "change.md"):
        text = file_bytes(root, (directory / name).relative_to(root).as_posix()).decode("utf-8")
        if not text.strip() or (enforce and ("[TODO]" in text or "{{" in text)):
            raise SpecError(f"Documento vacío o sin completar: {name}")
    if enforce and ("[TODO]" in json.dumps(data) or "{{" in json.dumps(data)):
        raise SpecError("Contrato con placeholders pendientes")
    req_ids = records(data["requirements"], "R", ("id", "statement"), "requirements")
    ac_ids = records(data["acceptance"], "AC", ("id", "requirement_ids", "given", "when", "then", "test_refs"), "acceptance")
    records(data["tasks"], "T", ("id", "title", "requirement_ids", "acceptance_ids", "status"), "tasks")
    covered_req, tasked_req, tasked_ac = set(), set(), set()
    for req in data["requirements"]:
        text_field(req["statement"], req["id"])
    acceptance_requirements = {}
    for ac in data["acceptance"]:
        linked = references(ac["requirement_ids"], req_ids, ac["id"])
        acceptance_requirements[ac["id"]] = linked
        covered_req |= linked
        for key in ("given", "when", "then"):
            text_field(ac[key], ac["id"] + "." + key)
        if not isinstance(ac["test_refs"], list) or (enforce and not ac["test_refs"]):
            raise SpecError(f"{ac['id']}: test_refs requerido para validación estricta/ready")
        for ref in ac["test_refs"]:
            fields(ref, ("path", "assertion"), label=ac["id"] + ".test_refs")
            text_field(ref["assertion"], "assertion")
            file_bytes(root, relative(ref["path"]))
    for task in data["tasks"]:
        text_field(task["title"], task["id"])
        linked_req = references(task["requirement_ids"], req_ids, task["id"])
        linked_ac = references(task["acceptance_ids"], ac_ids, task["id"])
        if any(not acceptance_requirements[ac] <= linked_req for ac in linked_ac):
            raise SpecError(f"{task['id']}: incluye criterios cuyos requisitos no están en la tarea")
        tasked_req |= linked_req
        tasked_ac |= linked_ac
        if task["status"] not in ("todo", "doing", "done"):
            raise SpecError(f"{task['id']}: estado inválido")
        if data["status"] == "implemented" and task["status"] != "done":
            raise SpecError("Feature implemented con tareas incompletas")
    if covered_req != req_ids or tasked_req != req_ids or tasked_ac != ac_ids:
        raise SpecError("Trazabilidad incompleta: cada requisito necesita criterio y tarea; cada criterio necesita tarea")


def validate(args):
    root = root_path(args.target)
    config = project_config(root)
    specs = safe_path(root, config["specs_dir"])
    if not specs.exists():
        if args.strict:
            raise SpecError("No hay features; validación estricta requiere al menos una")
        print("OK: 0 features (sin validar comportamiento)")
        return
    if not specs.is_dir():
        raise SpecError("specs_dir no es un directorio")
    failures, count = [], 0
    for directory in sorted(specs.iterdir()):
        no_symlinks(directory)
        if not directory.is_dir():
            continue
        count += 1
        try:
            validate_feature(root, directory, args.strict)
            print("OK " + directory.name)
        except (SpecError, UnicodeError) as exc:
            failures.append(f"{directory.name}: {exc}")
    if args.strict and not count:
        raise SpecError("No hay features; validación estricta requiere al menos una")
    if failures:
        raise SpecError("\n".join(failures))
    print(f"OK: {count} features; estructura y referencias solamente, no ejecución ni garantía semántica")


def commands(args):
    config = project_config(root_path(args.target))
    print(json.dumps(config["commands"], ensure_ascii=False, indent=2))
    print("Informativo: revise y ejecute manualmente estos comandos; el CLI no los ejecuta")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    subs = parser.add_subparsers(dest="command", required=True)
    for name in ("install", "update"):
        sub = subs.add_parser(name)
        sub.add_argument("--target", required=True)
        sub.add_argument("--apply", action="store_true")
        sub.add_argument("--github", action="store_true", help="Activa snippets GitHub solo en instalación inicial")
        sub.add_argument("--adapter", choices=("generic", "laravel"), default="generic", help="Solo instalación inicial")
        sub.set_defaults(func=install)
    sub = subs.add_parser("new")
    sub.add_argument("slug")
    sub.add_argument("--target", required=True)
    sub.add_argument("--apply", action="store_true")
    sub.set_defaults(func=feature)
    sub = subs.add_parser("validate")
    sub.add_argument("--target", required=True)
    sub.add_argument("--strict", action="store_true")
    sub.set_defaults(func=validate)
    sub = subs.add_parser("commands")
    sub.add_argument("--target", required=True)
    sub.set_defaults(func=commands)
    args = parser.parse_args(argv)
    try:
        args.func(args)
        return 0
    except (SpecError, OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
