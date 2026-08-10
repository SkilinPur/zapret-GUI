#!/usr/bin/env bash

# =============================================================================
# CLI: Настройка прав доступа
# =============================================================================

show_permissions_usage() {
    echo "Usage: $(basename "$0") setup-permissions [command]"
    echo
    echo "Настройка NOPASSWD для nft, iptables, ip6tables, nfqws и запуска service.sh."
    echo
    echo "Commands:"
    echo "    (без аргументов)  Создать /etc/sudoers.d/zapret"
    echo "    status            Показать текущие настройки"
    echo "    remove            Удалить настройки"
    echo "    USER              Имя пользователя для правил (по умолчанию — определить автоматически)"
}

handle_permissions_command() {
    case "${1:-}" in
        status)
            show_permissions_status
            ;;
        remove)
            remove_permissions
            ;;
        -h|--help)
            show_permissions_usage
            ;;
        *)
            # Всё остальное — имя пользователя, для которого настраиваем
            # NOPASSWD (пусто = определить автоматически). Например:
            #   service.sh setup-permissions            # авто-определение
            #   service.sh setup-permissions skilin     # явный пользователь
            setup_permissions "${1:-}"
            ;;
    esac
}
