# =============================================================================
# Фоновые воркеры — запуск команд без блокировки UI
# =============================================================================
# Автор GUI: SkilinPur (https://github.com/SkilinPur) | Репозиторий: https://github.com/SkilinPur/zapret-GUI

import subprocess

from PySide6.QtCore import QThread, Signal


class CommandWorker(QThread):
    """Выполняет команду до завершения, стримит вывод построчно."""

    output = Signal(str)
    success = Signal(str)
    failed = Signal(str)

    def __init__(self, cmd, cwd=None, elevated=False, stdin=None, parent=None):
        super().__init__(parent)
        self._cmd = cmd
        self._cwd = cwd
        self._elevated = elevated
        self._stdin = stdin
        self._proc = None

    def run(self):
        cmd = (["sudo", "-n"] if self._elevated else []) + self._cmd
        try:
            self._proc = subprocess.Popen(
                cmd, cwd=self._cwd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE if self._stdin is not None else subprocess.DEVNULL,
                text=True, bufsize=1, encoding="utf-8", errors="replace",
            )
            if self._stdin is not None:
                self._proc.stdin.write(self._stdin)
                self._proc.stdin.close()
        except FileNotFoundError:
            self.failed.emit("Команда не найдена. Проверьте наличие service.sh")
            return
        except Exception as exc:
            self.failed.emit(str(exc))
            return

        for line in self._proc.stdout:
            self.output.emit(line.rstrip("\n"))

        rc = self._proc.wait()
        if rc == 0:
            self.success.emit("")
        else:
            self.failed.emit(f"Команда завершилась с кодом {rc}")

    def stop(self):
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()


class DaemonWorker(QThread):
    """Запускает долгоживущий процесс (демон zapret), стримит вывод."""

    output = Signal(str)
    stopped = Signal()
    failed = Signal(str)

    def __init__(self, cmd, cwd=None, elevated=False, parent=None):
        super().__init__(parent)
        self._cmd = cmd
        self._cwd = cwd
        self._elevated = elevated
        self._proc = None

    def run(self):
        cmd = (["sudo", "-n"] if self._elevated else []) + self._cmd
        try:
            self._proc = subprocess.Popen(
                cmd, cwd=self._cwd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True, bufsize=1, encoding="utf-8", errors="replace",
            )
        except Exception as exc:
            self.failed.emit(str(exc))
            return

        for line in self._proc.stdout:
            self.output.emit(line.rstrip("\n"))

        self._proc.wait()
        self.stopped.emit()

    def terminate(self):
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()

