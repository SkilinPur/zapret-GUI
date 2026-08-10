#!/usr/bin/env bash

# =============================================================================
# Настройка прав доступа для работы без пароля (sudo/doas)
# =============================================================================

SUDOERS_FILE="/etc/sudoers.d/zapret"
DOAS_CONF="/etc/doas.conf"

# Получить путь к команде
get_cmd_path() {
    command -v "$1" 2>/dev/null || echo "/usr/bin/$1"
}

# Безопасное чтение строки. При запуске без терминала (GUI) запрос пропускается
# и возвращается значение по умолчанию — иначе read при EOF вернёт ошибку,
# а `set -e` оборвёт скрипт.
safe_read() {
    local prompt="$1" default="${2:-}"
    if ! [ -t 0 ]; then
        printf '%s\n' "$default"
        return 0
    fi
    local answer=""
    if read -r -p "$prompt" answer; then
        printf '%s\n' "${answer:-$default}"
    else
        printf '%s\n' "$default"
    fi
    return 0
}

# Определяет, для какого пользователя настраивать NOPASSWD.
# Приоритет: явный аргумент > SUDO_USER (sudo) > PKEXEC_UID (pkexec) > текущий пользователь.
# Нужно, т.к. при запуске через sudo/pkexec $USER внутри скрипта = root.
resolve_setup_user() {
    local explicit="${1:-}"
    if [[ -n "$explicit" ]]; then
        echo "$explicit"
        return 0
    fi
    if [[ -n "${SUDO_USER:-}" ]]; then
        echo "$SUDO_USER"
        return 0
    fi
    if [[ -n "${PKEXEC_UID:-}" ]]; then
        id -nu "$PKEXEC_UID" 2>/dev/null || echo "$PKEXEC_UID"
        return 0
    fi
    id -un
}

# -----------------------------------------------------------------------------
# Генерация sudoers
# -----------------------------------------------------------------------------

generate_sudoers_content() {
    local user="$1"
    local nfqws_path="${2:-$NFQWS_PATH}"
    local base_dir="${3:-$BASE_DIR}"
    local nft_path=$(get_cmd_path nft)
    local pkill_path=$(get_cmd_path pkill)
    local chown_path=$(get_cmd_path chown)
    local bash_path=$(get_cmd_path bash)

    local iptables_path=$(get_cmd_path iptables)
    local ip6tables_path=$(get_cmd_path ip6tables)

    # Право на запуск service.sh через bash — так GUI выполняет все команды
    local bash_line=""
    if [[ -n "$base_dir" && -n "$user" ]]; then
        bash_line="$user ALL=(root) NOPASSWD: $bash_path $base_dir/service.sh *"
    fi

    # Право на восстановление владельца каталога проекта
    # (нужно, если zapret-latest был создан от root и мешает обновлению)
    local chown_line=""
    if [[ -n "$base_dir" && -n "$user" ]]; then
        chown_line="$user ALL=(root) NOPASSWD: $chown_path -R $user $base_dir"
    fi

    cat <<EOF
# Zapret Discord YouTube - NOPASSWD для $user
# Файл: $SUDOERS_FILE

${bash_line:+$bash_line}
$user ALL=(root) NOPASSWD: $nft_path *
$user ALL=(root) NOPASSWD: $iptables_path *
$user ALL=(root) NOPASSWD: $ip6tables_path *
$user ALL=(root) NOPASSWD: $nfqws_path *
$user ALL=(root) NOPASSWD: $pkill_path -f nfqws
${chown_line:+$chown_line}
EOF
}

setup_sudoers() {
    local user="${1:-$USER}"

    echo "Настройка sudoers для $user..."

    # Проверяем директорию sudoers.d
    if [[ ! -d "/etc/sudoers.d" ]]; then
        show_error "Ошибка: /etc/sudoers.d не существует"
        return 0
    fi

    local content
    content=$(generate_sudoers_content "$user" "$NFQWS_PATH" "$BASE_DIR")

    echo ""
    echo "Будет создан $SUDOERS_FILE:"
    echo "─────────────────────────────────────────"
    echo "$content"
    echo "─────────────────────────────────────────"
    echo ""

    local confirm
    confirm=$(safe_read "Создать? [Y/n]: " "Y")
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "Отменено"
        safe_read "Нажмите Enter для продолжения..." > /dev/null
        return 0
    fi

    echo "$content" | elevate tee "$SUDOERS_FILE" > /dev/null || {
        show_error "Ошибка записи $SUDOERS_FILE"
        return 0
    }

    elevate chmod 440 "$SUDOERS_FILE"

    # Проверяем синтаксис
    if command -v visudo >/dev/null 2>&1; then
        if ! elevate visudo -c -f "$SUDOERS_FILE" 2>/dev/null; then
            show_error "Ошибка синтаксиса! Удаляю файл..."
            elevate rm -f "$SUDOERS_FILE"
            return 0
        fi
    fi

    echo "Готово: $SUDOERS_FILE"
    safe_read "Нажмите Enter для продолжения..." > /dev/null
    return 0
}

# -----------------------------------------------------------------------------
# Генерация doas.conf
# -----------------------------------------------------------------------------

generate_doas_rules() {
    local user="$1"
    local nfqws_path="${2:-$NFQWS_PATH}"
    local base_dir="${3:-$BASE_DIR}"
    local nft_path=$(get_cmd_path nft)

    local iptables_path=$(get_cmd_path iptables)
    local ip6tables_path=$(get_cmd_path ip6tables)

    # Право на запуск service.sh через bash
    local bash_line=""
    if [[ -n "$base_dir" && -n "$user" ]]; then
        bash_line="permit nopass $user as root cmd bash args $base_dir/service.sh *"
    fi

    # Право на восстановление владельца каталога проекта
    local chown_line=""
    if [[ -n "$base_dir" && -n "$user" ]]; then
        chown_line="permit nopass $user as root cmd chown args -R $user $base_dir"
    fi

    cat <<EOF
# Zapret Discord YouTube - nopass для $user
permit nopass $user as root cmd $nft_path
permit nopass $user as root cmd $iptables_path
permit nopass $user as root cmd $ip6tables_path
permit nopass $user as root cmd $nfqws_path
permit nopass $user as root cmd pkill args -f nfqws
${bash_line:+$bash_line}
${chown_line:+$chown_line}
EOF
}

setup_doas() {
    local user="${1:-$USER}"

    echo "Настройка doas для $user..."

    local rules
    rules=$(generate_doas_rules "$user" "$NFQWS_PATH" "$BASE_DIR")

    echo ""
    echo "Будут добавлены в $DOAS_CONF:"
    echo "─────────────────────────────────────────"
    echo "$rules"
    echo "─────────────────────────────────────────"
    echo ""

    local confirm
    confirm=$(safe_read "Добавить? [Y/n]: " "Y")
    if [[ "$confirm" =~ ^[Nn]$ ]]; then
        echo "Отменено"
        safe_read "Нажмите Enter для продолжения..." > /dev/null
        return 0
    fi

    # Проверяем, есть ли уже наши правила
    if [[ -f "$DOAS_CONF" ]] && grep -q "# Zapret Discord YouTube" "$DOAS_CONF"; then
        echo "Правила уже есть в $DOAS_CONF"
        local replace
        replace=$(safe_read "Заменить? [Y/n]: " "Y")
        if [[ "$replace" =~ ^[Yy]$ ]]; then
            # Удаляем старый блок (от маркера до пустой строки или конца)
            elevate sed -i '/# Zapret Discord YouTube/,/^$/d' "$DOAS_CONF"
        else
            echo "Отменено"
            safe_read "Нажмите Enter для продолжения..." > /dev/null
            return 0
        fi
    fi

    # Добавляем правила
    {
        echo ""
        echo "$rules"
    } | elevate tee -a "$DOAS_CONF" > /dev/null || {
        show_error "Ошибка записи в $DOAS_CONF"
        return 0
    }

    echo "Готово: правила добавлены в $DOAS_CONF"
    safe_read "Нажмите Enter для продолжения..." > /dev/null
    return 0
}

# -----------------------------------------------------------------------------
# Главные функции
# -----------------------------------------------------------------------------

setup_permissions() {
    local user
    user=$(resolve_setup_user "${1:-}")
    local system
    system=$(get_elevate_cmd) || {
        show_error "Ошибка: не найден sudo или doas"
        return 0
    }

    echo "Настройка NOPASSWD для $user..."
    echo ""

    case "$system" in
        sudo)
            setup_sudoers "$user"
            ;;
        doas)
            setup_doas "$user"
            ;;
        "")
            # Для запуска от root
            setup_sudoers "$user"
            ;;
    esac
}

remove_permissions() {
    local removed=false

    # Удаляем sudoers
    if [[ -f "$SUDOERS_FILE" ]]; then
        elevate rm -f "$SUDOERS_FILE"
        echo "Удалён $SUDOERS_FILE"
        removed=true
    fi

    # Удаляем правила из doas.conf
    if [[ -f "$DOAS_CONF" ]] && grep -q "# Zapret Discord YouTube" "$DOAS_CONF"; then
        elevate sed -i '/# Zapret Discord YouTube/,/^$/d' "$DOAS_CONF"
        echo "Удалены правила из $DOAS_CONF"
        removed=true
    fi

    if ! $removed; then
        echo "Настройки не найдены"
    fi
}

show_permissions_status() {
    local system
    system=$(get_elevate_cmd 2>/dev/null) || system="none"

    echo "Система: $system"
    echo ""

    # Sudoers
    if [[ -f "$SUDOERS_FILE" ]]; then
        echo "sudoers: $SUDOERS_FILE"
        echo "─────────────────────────────────────────"
        cat "$SUDOERS_FILE" 2>/dev/null || elevate cat "$SUDOERS_FILE"
        echo "─────────────────────────────────────────"
    else
        echo "sudoers: не настроен"
    fi

    echo ""

    # Doas
    if [[ -f "$DOAS_CONF" ]] && grep -q "# Zapret Discord YouTube" "$DOAS_CONF"; then
        echo "doas: настроен"
        echo "─────────────────────────────────────────"
        grep -A3 "# Zapret Discord YouTube" "$DOAS_CONF"
        echo "─────────────────────────────────────────"
    else
        echo "doas: не настроен"
    fi
}
