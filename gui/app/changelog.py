# =============================================================================
# CHANGELOG.md — чтение и парсинг истории версий
# =============================================================================
# Автор GUI: SkilinPur (https://github.com/SkilinPur) | Репозиторий: https://github.com/SkilinPur/zapret-GUI

import re
from pathlib import Path

_SECTION_RE = re.compile(r"^##\s+[\[(]?\s*(.+?)\s*[\])]?\s*(?:—|-)\s*(.*)$")


def changelog_path(repo_root):
    """Путь к CHANGELOG.md в корне проекта."""
    return Path(repo_root) / "CHANGELOG.md"


def changelog_versions(repo_root):
    """Разделы CHANGELOG.md в порядке файла: список (версия, дата, текст).

    Возвращает пустой список, если файла нет или в нём нет секций версий.
    """
    path = changelog_path(repo_root)
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    versions = []
    current = None
    for line in text.splitlines():
        m = _SECTION_RE.match(line)
        if m:
            if current is not None:
                versions.append(current)
            current = (m.group(1).strip(), m.group(2).strip(), [])
        elif current is not None:
            current[2].append(line)
    if current is not None:
        versions.append(current)
    return [(v, d, "\n".join(lines).strip()) for v, d, lines in versions]
