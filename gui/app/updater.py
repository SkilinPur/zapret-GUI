# =============================================================================
# Обновления — версия приложения, проверка релизов, команда git pull
# =============================================================================
# Автор GUI: SkilinPur (https://github.com/SkilinPur) | Репозиторий: https://github.com/SkilinPur/zapret-GUI

import json
import subprocess
import urllib.request

from PySide6.QtCore import QThread, Signal

APP_VERSION = "1.0.2"
GITHUB_REPO = "SkilinPur/zapret-GUI"
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def parse_version(text):
    """Преобразует тег вида 'v1.2.3' в числовой кортеж (1, 2, 3)."""
    clean = (text or "").strip()
    if clean.startswith("v"):
        clean = clean[1:]
    parts = []
    for chunk in clean.split("."):
        try:
            parts.append(int(chunk))
        except ValueError:
            break
    return tuple(parts) or (0,)


def is_newer(tag):
    """True, если тег новее текущей версии приложения."""
    return parse_version(tag) > parse_version(APP_VERSION)


class CheckWorker(QThread):
    """В фоне запрашивает последний релиз с GitHub API."""

    result = Signal(object)  # (tag, notes, error)

    def run(self):
        try:
            req = urllib.request.Request(
                API_URL, headers={"User-Agent": f"zapret-gui/{APP_VERSION}"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.load(resp)
            tag = data.get("tag_name") or ""
            notes = data.get("body") or ""
            self.result.emit((tag, notes, None))
        except Exception as exc:
            self.result.emit((None, None, str(exc)))


def git_pull_cmd(repo_root):
    """Команда обновления через git pull (предпочитает remote 'github')."""
    remote = "origin"
    branch = "main"
    try:
        remotes = subprocess.check_output(
            ["git", "remote"], cwd=repo_root, text=True, stderr=subprocess.DEVNULL
        ).split()
        if "github" in remotes:
            remote = "github"
        elif remotes:
            remote = remotes[0]
    except Exception:
        pass
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_root, text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        pass
    return ["git", "pull", "--ff-only", remote, branch]
