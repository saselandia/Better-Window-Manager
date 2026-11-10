"""Versiones locales para BWMenu y bwm check --versions. Sólo consultas, sin red."""
import re
import subprocess
import sys
from pathlib import Path


def output(argv, timeout=4, stderr=False):
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return (result.stdout + (result.stderr if stderr else "")).strip() if result.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def bwm_version(repo):
    version = output(["git", "-C", str(repo), "describe", "--tags", "--always", "--dirty"])
    if version:
        return version
    # Un archivo exportado no tiene por qué conservar .git.
    try:
        return (Path(repo) / "VERSION").read_text().strip()
    except OSError:
        return "sin datos de revisión (copia sin Git)"


def package_versions(spec, family, database=Path("/var/db/pkg")):
    """Consulta sólo los paquetes declarados en el catálogo; no ejecuta sus programas."""
    found = []
    for token in (spec.get("packages", {}).get(family) or "").split():
        package = token.rsplit(":", 1)[-1].split("[", 1)[0]
        if family == "gentoo":
            category, sep, name = package.partition("/")
            if not sep:
                continue
            # No confundir foo-1.2 con foo-extra-1.2; puede haber varios slots.
            pattern = re.compile(re.escape(name) + r"-(\d.*)")
            for path in sorted((database / category).glob(name + "-*")):
                match = pattern.fullmatch(path.name)
                if match and path.is_dir():
                    found.append(f"{name} {match[1]}")
        elif family == "arch":
            value = output(["pacman", "-Q", package])
            if value:
                found.append(value)
        elif family in ("fedora", "opensuse"):
            value = output(["rpm", "-q", "--qf", "%{NAME} %{VERSION}-%{RELEASE}\n", package])
            if value:
                found.append(value)
        elif family == "debian":
            value = output(["dpkg-query", "-W", "-f=${db:Status-Abbrev} ${Package} ${Version}\n", package])
            found.extend(line[4:] for line in value.splitlines() if line.startswith("ii "))
    return "; ".join(dict.fromkeys(found))


def requirement_versions(spec, family, detail, status):
    check = spec.get("check", {})
    kind = check.get("type")
    version = ""
    source = ""
    if kind in ("version", "python"):
        match = re.match(r"\d[\w.+-]*", detail)
        if match:
            version, source = match[0], "comprobación"
    if kind == "python":
        version, source = ".".join(map(str, sys.version_info[:3])), "intérprete actual"
    if kind == "hyprland-plugin":
        match = re.search(r"compilado para Hyprland ([0-9a-f]+)", detail)
        if match:
            version, source = match[1], "commit de Hyprland del plugin"
    # Sondas explícitas del catálogo: nunca se prueba --version a una app gráfica al azar.
    if not version and status == "ok":
        for probe in spec.get("versionProbes", []):
            match = re.search(probe["regex"], output(probe["cmd"], stderr=probe.get("stderr", False)), re.MULTILINE)
            if match:
                version, source = match[1], "programa instalado"
                break
    if not version and status == "ok":
        version = package_versions(spec, family)
        if version:
            source = "paquetes instalados"
    if not version and status == "ok":
        # Metadatos del proyecto original para instalaciones compiladas a mano.
        # Nunca tomar la versión del directorio de compilación como si estuviera instalada.
        for probe in spec.get("versionFiles", []):
            path = Path(probe["path"]).expanduser()
            try:
                match = re.search(probe["regex"], path.read_text(encoding="utf-8"), re.MULTILINE)
            except (OSError, UnicodeError):
                continue
            if match:
                version, source = match[1], str(path)
                break
    reference = spec.get("referenceVersion") or check.get("tested") or check.get("min", "")
    # Las versiones de paquetes se muestran con su nombre; para comparar se usa
    # la versión del único paquete, no los dígitos que pudiera contener su nombre.
    comparable = version
    if source == "paquetes instalados":
        comparable = version.rsplit(" ", 1)[-1] if ";" not in version else ""
    state, reason = version_state(status, comparable, reference, kind)
    return {"version": version, "versionSource": source, "versionState": state, "versionReason": reason,
            "referenceVersion": reference,
            "minimumVersion": check.get("min", ""), "testedVersion": check.get("tested", ""),
            "versionPolicy": ("commit exacto de Hyprland" if kind == "hyprland-plugin" else
                              f">= {check['min']}" if check.get("min") else "sin mínimo declarado")}


def numeric_version(value):
    match = re.match(r"^v?(\d+(?:\.\d+)*)", str(value).strip())
    if not match:
        return None
    parts = [int(x) for x in match[1].split(".")]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)


def version_state(status, installed, reference, kind=""):
    """Semáforo respecto a la referencia de BWM; no consulta actualizaciones remotas."""
    if status != "ok":
        return "error", {"missing": "Falta este requisito", "outdated": "Versión inferior a la requerida", "build": "Necesita recompilarse",
                         "pending": "Instalación pendiente"}.get(status, "Requisito ausente o incompatible")
    if kind == "hyprland-plugin":
        return "ok", "Coincide con el commit de Hyprland en ejecución"
    if not reference:
        return "ok", "Comprobación correcta; sin versión mínima declarada"
    actual, required = numeric_version(installed), numeric_version(reference)
    if actual is None or required is None:
        return "unknown", "No se puede comparar esta versión"
    if actual < required:
        return "error", f"Inferior a la referencia de BWM ({reference})"
    if actual > required:
        return "newer", f"Referencia de BWM desactualizada ({reference}); instalada más reciente ({installed})"
    return "ok", f"Coincide con la referencia de BWM ({reference})"


def version_health(rows):
    # Un requisito compartido sólo se cuenta una vez en el resumen de una skin.
    unique = {row["id"]: row for row in rows}
    counts = {key: 0 for key in ("ok", "newer", "error", "unknown")}
    for row in unique.values():
        state = row.get("versionState", "error" if row.get("status") != "ok" else "unknown")
        counts[state] += 1
    state = next((key for key in ("error", "newer", "ok") if counts[key]), "unknown")
    labels = {"error": "Hay dependencias ausentes, antiguas o incompatibles",
              "newer": "Referencia de BWM desactualizada: hay versiones instaladas más recientes",
              "ok": "Todas las comprobaciones son correctas", "unknown": "Sin diagnóstico"}
    return {"state": state, "description": labels[state], "counts": counts}
