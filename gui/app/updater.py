# =============================================================================
# Обновления — версия приложения, проверка релизов, команда git pull
# =============================================================================
# Автор GUI: SkilinPur (https://github.com/SkilinPur) | Репозиторий: https://github.com/SkilinPur/zapret-GUI

import json
import subprocess
import urllib.request

from PySide6.QtCore import QThread, Signal

APP_VERSION = "1.0.11"
GITHUB_REPO = "SkilinPur/zapret-GUI"
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
REPO_GIT_URL = f"https://github.com/{GITHUB_REPO}.git"


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
    """В фоне определяет последнюю версию: через GitHub API, иначе через git ls-remote."""

    result = Signal(object)  # (tag, notes, error)

    def run(self):
        tag, notes, api_error = self._check_api()
        if tag:
            self.result.emit((tag, notes, None))
            return
        tag = self._check_git()
        if tag:
            self.result.emit((tag, "", None))
            return
        self.result.emit(("", "", api_error or "не удалось проверить обновления"))

    def _check_api(self):
        try:
            req = urllib.request.Request(
                API_URL, headers={"User-Agent": f"zapret-gui/{APP_VERSION}"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.load(resp)
            return (data.get("tag_name") or "", data.get("body") or "", "")
        except Exception as exc:
            return ("", "", str(exc))

    def _check_git(self):
        """Запасной способ: список тегов через git (работает даже если профиль скрыт)."""
        try:
            out = subprocess.check_output(
                ["git", "ls-remote", "--tags", REPO_GIT_URL],
                timeout=15, text=True, stderr=subprocess.DEVNULL,
            )
        except Exception:
            return ""
        tags = []
        for line in out.splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            ref = parts[-1]
            if not ref.startswith("refs/tags/"):
                continue
            tag = ref[len("refs/tags/"):]
            if tag.endswith("^{}"):
                continue
            if parse_version(tag) == (0,):
                continue
            tags.append(tag)
        if not tags:
            return ""
        return max(tags, key=parse_version)


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
