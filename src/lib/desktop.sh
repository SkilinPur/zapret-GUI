#!/usr/bin/env bash

# =============================================================================
# Управление desktop ярлыком для zapret-discord-youtube-linux
# =============================================================================

# Guard: проверяем что файл не был уже загружен
[[ -n "${_DESKTOP_SH_LOADED:-}" ]] && return 0
_DESKTOP_SH_LOADED=1

# Подключаем константы и общие функции
source "$(dirname "${BASH_SOURCE[0]}")/constants.sh"
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

# -----------------------------------------------------------------------------
# Функции управления desktop ярлыком
# -----------------------------------------------------------------------------

# Функция создания desktop ярлыка
create_desktop_shortcut() {
    # Проверяем и создаём конфиг если нужно
    ensure_config_exists || return 1

    local desktop_file="/usr/share/applications/zapret-discord-youtube.desktop"
    local script_path="$BASE_DIR/service.sh"

    log "Создание системного ярлыка..."

    # Создаём desktop файл
    elevate tee "$desktop_file" > /dev/null <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Zapret Discord YouTube
Comment=Обход замедления YouTube и Discord
Exec=bash -c 'cd "${BASE_DIR}" && bash "${script_path}" daemon'
Icon=network-workgroup
Terminal=true
Categories=Network;System;
Keywords=zapret;youtube;discord;dpi;
EOF

    elevate chmod +x "$desktop_file" || handle_error "Не удалось установить права на ярлык"

    # Обновляем базу desktop файлов если есть update-desktop-database
    if command -v update-desktop-database >/dev/null 2>&1; then
        elevate update-desktop-database /usr/share/applications 2>/dev/null || true
    fi

    echo "Системный ярлык создан: $desktop_file"
    echo "Ярлык доступен всем пользователям в меню системы"
    echo ""
    echo "Для работы без пароля: ./service.sh setup-permissions"
}

# Функция удаления desktop ярлыка
remove_desktop_shortcut() {
    local desktop_file="/usr/share/applications/zapret-discord-youtube.desktop"

    if [[ -f "$desktop_file" ]]; then
        log "Удаление системного ярлыка..."
        elevate rm -f "$desktop_file" || handle_error "Не удалось удалить ярлык"

        # Обновляем базу desktop файлов если есть update-desktop-database
        if command -v update-desktop-database >/dev/null 2>&1; then
            elevate update-desktop-database /usr/share/applications 2>/dev/null || true
        fi

        echo "✓ Системный ярлык удалён: $desktop_file"
    else
        show_error "Ярлык не найден: $desktop_file"
        return 1
    fi
}

# -----------------------------------------------------------------------------
# Пользовательский ярлык GUI (запуск без консоли, без sudo)
# -----------------------------------------------------------------------------

GUI_DESKTOP_FILE="$HOME/.local/share/applications/zapret-discord-youtube-gui.desktop"

# Создание пользовательского ярлыка для запуска GUI из меню приложений
install_gui_desktop() {
    local apps_dir="$HOME/.local/share/applications"

    log "Создание ярлыка GUI в меню приложений..."

    mkdir -p "$apps_dir"

    cat > "$GUI_DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Zapret Discord YouTube
Comment=Обход замедления YouTube и Discord
Exec="${BASE_DIR}/gui/gui.sh"
Icon=network-workgroup
Terminal=false
Categories=Network;System;
Keywords=zapret;youtube;discord;dpi;
StartupNotify=true
EOF

    chmod +x "$GUI_DESKTOP_FILE"

    # Обновляем базу desktop файлов если есть update-desktop-database
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$apps_dir" 2>/dev/null || true
    fi

    echo "✓ Ярлык GUI создан: $GUI_DESKTOP_FILE"
    echo "Теперь Zapret Discord YouTube можно запускать из меню приложений без консоли."
}

# Удаление пользовательского ярлыка GUI
remove_gui_desktop() {
    if [[ -f "$GUI_DESKTOP_FILE" ]]; then
        log "Удаление ярлыка GUI..."
        rm -f "$GUI_DESKTOP_FILE" || handle_error "Не удалось удалить ярлык"

        # Обновляем базу desktop файлов если есть update-desktop-database
        if command -v update-desktop-database >/dev/null 2>&1; then
            update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
        fi

        echo "✓ Ярлык GUI удалён: $GUI_DESKTOP_FILE"
    else
        show_error "Ярлык не найден: $GUI_DESKTOP_FILE"
        return 1
    fi
}

# Показать справку по desktop
show_desktop_usage() {
    cat <<EOF
Управление desktop ярлыком

Использование:
  $(basename "$0") desktop install       - Системный ярлык (запуск демона, для всех пользователей)
  $(basename "$0") desktop remove        - Удалить системный ярлык
  $(basename "$0") desktop install-gui   - Ярлык GUI в меню (запуск без консоли, для этого пользователя)
  $(basename "$0") desktop remove-gui    - Удалить ярлык GUI
  $(basename "$0") desktop --help        - Показать эту справку

Примеры:
  # Создать ярлык GUI
  bash service.sh desktop install-gui

  # Удалить ярлык GUI
  bash service.sh desktop remove-gui

Системный ярлык появится в меню приложений всех пользователей в категории
"Сеть" или "Система", при запуске откроется терминал и zapret запустится с
настройками из conf.env. Ярлык GUI запускает графический интерфейс без консоли.
EOF
}
