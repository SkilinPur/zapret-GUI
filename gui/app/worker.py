# =============================================================================
# Фоновые воркеры — запуск команд без блокировки UI
# =============================================================================
# Автор GUI: SkilinPur (https://github.com/SkilinPur) | Репозиторий: https://github.com/SkilinPur/zapret-GUI

import os
import select
import signal
import subprocess

from PySide6.QtCore import QThread, Signal

from .zapret import log_to_file

PASSWORD_HINT = ("Требуется пароль sudo (NOPASSWD не настроен). "
                 "Откройте вкладку «Права» и настройте работу без пароля.")


def _kill_tree(proc):
    """Завершает дерево процессов (process group). Возвращает сам proc."""
    if proc is None or proc.poll() is not None:
        return proc
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except (OSError, ProcessLookupError):
        try:
            proc.terminate()
        except OSError:
            pass
    return proc


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
        self._stop_requested = False
        self._needs_password_hint = False

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
                start_new_session=True,
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

        self._read_stream(self._proc.stdout, cmd, self._emit_worker_line)

        try:
            rc = self._proc.wait()
        except Exception:
            rc = -1
        if rc == 0:
            self.success.emit("")
        elif self._needs_password_hint:
            self.failed.emit(PASSWORD_HINT)
        else:
            self.failed.emit(f"Команда завершилась с кодом {rc}")

    def _emit_worker_line(self, line):
        if ("password is required" in line.lower()
                or "a password is required" in line.lower()
                or "пароль" in line.lower()):
            self._needs_password_hint = True
        self.output.emit(line)

    def _read_stream(self, stream, cmd, emit):
        """Читает stdout неблокирующе: раз в 0.2 с проверяет флаг остановки.

        Иначе демонизированный потомок (setsid, например nfqws), ушедший из
        process group, вечно держит pipe и поток никогда не завершается.
        """
        try:
            fd = stream.fileno()
        except (ValueError, OSError):
            return
        while not self._stop_requested:
            try:
                ready, _, _ = select.select([fd], [], [], 0.2)
            except (ValueError, OSError):
                break
            if not ready:
                continue
            try:
                line = stream.readline()
            except (ValueError, OSError):
                break
            if not line:
                break
            line = line.rstrip("\n")
            log_to_file(f"{' '.join(cmd)}: {line}")
            emit(line)

    def stop(self):
        self._stop_requested = True
        _kill_tree(self._proc)


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
        self._stop_requested = False

    def run(self):
        cmd = (["sudo", "-n"] if self._elevated else []) + self._cmd
        try:
            self._proc = subprocess.Popen(
                cmd, cwd=self._cwd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True, bufsize=1, encoding="utf-8", errors="replace",
                start_new_session=True,
            )
        except Exception as exc:
            self.failed.emit(str(exc))
            return

        self._read_stream(self._proc.stdout, cmd, self._emit_daemon_line)

        try:
            self._proc.wait()
        except Exception:
            pass
        self.stopped.emit()

    def _emit_daemon_line(self, line):
        self.output.emit(line)

    def _read_stream(self, stream, cmd, emit):
        try:
            fd = stream.fileno()
        except (ValueError, OSError):
            return
        while not self._stop_requested:
            try:
                ready, _, _ = select.select([fd], [], [], 0.2)
            except (ValueError, OSError):
                break
            if not ready:
                continue
            try:
                line = stream.readline()
            except (ValueError, OSError):
                break
            if not line:
                break
            line = line.rstrip("\n")
            log_to_file(f"{' '.join(cmd)}: {line}")
            emit(line)

    def terminate(self):
        self._stop_requested = True
        _kill_tree(self._proc)

