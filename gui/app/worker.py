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

    def __init__(self, cmd, cwd=None, elevated=False, password=None, stdin=None, parent=None):
        super().__init__(parent)
        self._cmd = cmd
        self._cwd = cwd
        self._elevated = elevated
        self._password = password
        self._stdin = stdin
        self._proc = None

    def run(self):
        stdin_data = self._stdin
        if self._password is not None:
            # Пароль sudo передаём один раз через stdin (sudo -S)
            cmd = ["sudo", "-S"] + self._cmd
            stdin_data = self._password + "\n"
        elif self._elevated:
            cmd = ["sudo", "-n"] + self._cmd
        else:
            cmd = self._cmd
        try:
            self._proc = subprocess.Popen(
                cmd, cwd=self._cwd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE if stdin_data is not None else subprocess.DEVNULL,
                text=True, bufsize=1, encoding="utf-8", errors="replace",
            )
            if stdin_data is not None:
                self._proc.stdin.write(stdin_data)
                self._proc.stdin.close()
            # Пароль больше не нужен — не держим его в памяти
            self._password = None
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

