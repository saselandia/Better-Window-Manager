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
    return {"version": version, "versionSource": source,
            "minimumVersion": check.get("min", ""), "testedVersion": check.get("tested", ""),
            "versionPolicy": ("commit exacto de Hyprland" if kind == "hyprland-plugin" else
                              f">= {check['min']}" if check.get("min") else "sin mínimo declarado")}
