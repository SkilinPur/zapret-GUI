# =============================================================================
# Обёртка над service.sh — единственное место, где вызываются bash-скрипты
# =============================================================================
# Автор GUI: SkilinPur (https://github.com/SkilinPur) | Репозиторий: https://github.com/SkilinPur/zapret-GUI

import os
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class Zapret:
    def __init__(self, repo_root=None):
        self.repo_root = Path(repo_root) if repo_root else REPO_ROOT
        self.service = self.repo_root / "service.sh"
        self.conf_file = self.repo_root / "conf.env"
        self.custom_strategies = self.repo_root / "custom-strategies"
        self.repo_dir = self.repo_root / "zapret-latest"
        self.gui_dir = self.repo_root / "gui"
        self.bash = "/bin/bash"

    # ------------------------------------------------------------------
    # Базовые помощники
    # ------------------------------------------------------------------

    def _cmd(self, args):
        return [self.bash, str(self.service), *args]

    def _run(self, args, elevated=False, timeout=60, stdin=None):
        cmd = (["sudo", "-n"] if elevated else []) + self._cmd(args)
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace", input=stdin,
        )

    def sudo_available(self):
        try:
            p = subprocess.run(["sudo", "-n", "true"], capture_output=True)
            return p.returncode == 0
        except FileNotFoundError:
            return False

    # ------------------------------------------------------------------
    # Списки для форм
    # ------------------------------------------------------------------

    def strategies(self):
        names = set()
        if self.custom_strategies.is_dir():
            names.update(f.name for f in self.custom_strategies.glob("*.bat"))
        if self.repo_dir.is_dir():
            names.update(
                f.name for f in self.repo_dir.glob("*.bat")
                if f.name.startswith(("general", "discord"))
            )
        return sorted(names)

    def interfaces(self):
        return ["any"] + sorted(os.listdir("/sys/class/net"))

    def backends(self):
        names = set()
        d = self.repo_root / "src" / "firewall-backends"
        for f in d.glob("*.sh"):
            m = re.match(r"^\d+-(.+)\.sh$", f.name)
            names.add(m.group(1) if m else f.stem)
        return sorted(names)

    # ------------------------------------------------------------------
    # Конфигурация (conf.env)
    # ------------------------------------------------------------------

    def read_config(self):
        cfg = {}
        if self.conf_file.exists():
            for line in self.conf_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    cfg[k.strip()] = v.strip()
        return cfg

    def config_set_cmd(self, strategy, interface, gamefiltertcp, gamefilterudp,
                       firewall_backend="auto", restart=True):
        args = ["config", "set", strategy, interface]
        if not restart:
            args.append("-n")
        if gamefiltertcp:
            args.append("-gt")
        if gamefilterudp:
            args.append("-gu")
        args += ["-fb", firewall_backend]
        return self._cmd(args)

    # ------------------------------------------------------------------
    # Статус
    # ------------------------------------------------------------------

    def nfqws_running(self):
        try:
            p = subprocess.run(["pgrep", "-f", "nfqws"], capture_output=True)
            return p.returncode == 0
        except FileNotFoundError:
            return False

    def nfqws_count(self):
        try:
            p = subprocess.run(["pgrep", "-f", "nfqws"],
                               capture_output=True, text=True)
            return len([l for l in p.stdout.splitlines() if l.strip()])
        except FileNotFoundError:
            return 0

    def init_system(self):
        try:
            p = subprocess.run(["cat", "/proc/1/comm"],
                               capture_output=True, text=True)
            return p.stdout.strip() or "unknown"
        except FileNotFoundError:
            return "unknown"

    def service_status_code(self):
        """Код статуса сервиса: 1 = не установлен, 2 = активен, 3 = установлен но не активен.

        Парсим вывод, т.к. CLI маскирует exit-код через `|| true`.
        """
        proc = self._run(["service", "status"])
        out = proc.stdout + proc.stderr
        if "не установлен" in out:
            return 1
        if "активен" in out:
            return 2
        return 3

    def service_status_output(self):
        proc = self._run(["service", "status"])
        return (proc.stdout + proc.stderr).strip()

    def service_active(self):
        return self.service_status_code() == 2

    # ------------------------------------------------------------------
    # Команды (запускаются через worker'ы)
    # ------------------------------------------------------------------

    def daemon_cmd(self):
        return self._cmd(["daemon"])

    def kill_cmd(self):
        return self._cmd(["kill"])

    def service_cmd(self, sub):
        return self._cmd(["service", sub])

    def download_deps_cmd(self):
        return self._cmd(["download-deps", "--default"])

    def update_strategies_cmd(self):
        return self._cmd(["update-strategies"])

    def download_nfqws_cmd(self):
        return self._cmd(["download-nfqws"])

    def nfqws_present(self):
        return (self.repo_root / "nfqws").exists()

    def setup_permissions_cmd(self):
        return self._cmd(["setup-permissions"])

    def autotune_youtube_cmd(self):
        return [self.bash, str(self.repo_root / "auto_tune_youtube.sh")]

    def autotune_cmd(self, domains, quic):
        stdin = f"{domains}\n{'Y' if quic else 'N'}\n"
        return ([self.bash, str(self.repo_root / "auto_tune.sh")], stdin)

    def autotune_results_file(self, youtube=False):
        name = "auto_tune_youtube_results.txt" if youtube else "auto_tune_results.txt"
        path = self.repo_root / name
        return path if path.exists() else None

    def downloads_present(self):
        return self.repo_dir.is_dir() and any(self.repo_dir.glob("*.bat"))

