#!/usr/bin/env bash

# =============================================================================
# Лаунчер GUI для zapret-discord-youtube-linux
# Создаёт venv при первом запуске, устанавливает PySide6 и запускает приложение
#
# GUI: SkilinPur (https://github.com/SkilinPur/zapret-GUI)
# Базируется на: Sergeydigl3/zapret-discord-youtube-linux
# Стратегии: Flowseal/zapret-discord-youtube | Ядро: bol-van/zapret
# =============================================================================

set -e

GUI_DIR="$(realpath "$(dirname "$0")")"
VENV="$GUI_DIR/.venv"
REQ="$GUI_DIR/requirements.txt"

PREFIX_DIR="$(realpath "$GUI_DIR/..")"
CONF_FILE="$PREFIX_DIR/conf.env"

show_usage() {
    echo "Usage: $(basename "$0") [options]"
    echo
    echo "Options:"
    echo "    --update       Обновить зависимости PySide6"
    echo "    --reset        Полностью пересоздать venv"
    echo "    --no-install   Не создавать venv (ошибка если PySide6 не установлен)"
    echo "    -h, --help     Показать эту справку"
}

# 1. Проверка python3
command -v python3 >/dev/null 2>&1 || {
    echo "Ошибка: python3 не установлен. Установите его для работы GUI." >&2
    exit 1
}

# 2. Обработка флагов
for arg in "$@"; do
    case "$arg" in
        -h|--help)
            show_usage
            exit 0
            ;;
        --reset)
            rm -rf "$VENV"
            echo "venv удалён, пересоздаю..."
            ;;
        --no-install)
            "$VENV/bin/python" -c "import PySide6" 2>/dev/null || {
                echo "Ошибка: PySide6 не установлен (venv: $VENV)." >&2
                echo "Запустите $(basename "$0") --update" >&2
                exit 1
            }
            ;;
    esac
done

# 3. Создание venv при первом запуске
if [ ! -d "$VENV" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv "$VENV"
    echo "Установка зависимостей GUI (первый запуск)..."
    "$VENV/bin/pip" install --upgrade pip -q
    "$VENV/bin/pip" install -r "$REQ"
fi

# 4. --update: обновляем зависимости
for arg in "$@"; do
    if [ "$arg" = "--update" ]; then
        echo "Обновление зависимостей GUI..."
        "$VENV/bin/pip" install --upgrade -r "$REQ"
        break
    fi
done

# 5. Проверка что PySide6 на месте — иначе пересоздание
if ! "$VENV/bin/python" -c "import PySide6" >/dev/null 2>&1; then
    echo "PySide6 не найден, пересоздаю виртуальное окружение..."
    rm -rf "$VENV"
    exec "$0" "$@"
fi

# 6. Запуск GUI (через -m, чтобы работали относительные импорты)
cd "$PREFIX_DIR"
exec "$VENV/bin/python" -m gui.app.main "$@"
