#!/usr/bin/env bash

# =============================================================================
# CLI: Управление desktop ярлыком
# =============================================================================

# Справка для desktop
show_desktop_usage() {
    echo "Usage: $(basename "$0") desktop <command>"
    echo
    echo "Commands:"
    echo "    install       Create system desktop shortcut (daemon, all users)"
    echo "    remove        Remove system desktop shortcut"
    echo "    install-gui   Create GUI shortcut in applications menu (no console, this user)"
    echo "    remove-gui    Remove GUI shortcut"
}

# Подменю управления desktop ярлыком
show_desktop_menu() {
    clear
    echo ""
    echo "=== Управление desktop ярлыком ==="
    echo "1. Создать ярлык GUI в меню (запуск без консоли)"
    echo "2. Удалить ярлык GUI из меню"
    echo "3. Создать системный ярлык (демон, для всех пользователей)"
    echo "4. Удалить системный ярлык"
    echo "0. Назад"
    read -p "Выберите действие: " choice
    case $choice in
    1)
        install_gui_desktop || show_error "Не удалось создать ярлык GUI"
        read -p "Нажмите Enter для продолжения..."
        ;;
    2)
        remove_gui_desktop && read -p "Нажмите Enter для продолжения..."
        ;;
    3)
        create_desktop_shortcut || show_error "Не удалось создать системный ярлык"
        read -p "Нажмите Enter для продолжения..."
        ;;
    4)
        remove_desktop_shortcut && read -p "Нажмите Enter для продолжения..."
        ;;
    0) return ;;
    *)
        show_error "Неверный выбор"
        show_desktop_menu
        ;;
    esac
}

# Обработчик команды desktop
handle_desktop_command() {
    case "${1:-}" in
        install)
            create_desktop_shortcut
            ;;
        remove)
            remove_desktop_shortcut
            ;;
        install-gui)
            install_gui_desktop
            ;;
        remove-gui)
            remove_gui_desktop
            ;;
        -h|--help|"")
            show_desktop_usage
            ;;
        *)
            echo "Unknown desktop command: $1"
            show_desktop_usage
            exit 1
            ;;
    esac
}
