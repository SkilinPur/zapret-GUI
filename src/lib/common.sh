#!/usr/bin/env bash

# =============================================================================
# Общие функции для всех скриптов zapret-discord-youtube-linux
# =============================================================================

# Guard: проверяем что файл не был уже загружен
[[ -n "${_COMMON_SH_LOADED:-}" ]] && return 0
_COMMON_SH_LOADED=1

# Подключаем константы
source "$(dirname "${BASH_SOURCE[0]}")/constants.sh"

# Флаг отладки (можно переопределить в скрипте)
DEBUG=${DEBUG:-false}

# -----------------------------------------------------------------------------
# Логирование
# -----------------------------------------------------------------------------

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

debug_log() {
    if $DEBUG; then
        echo "[DEBUG] $1"
    fi
}

handle_error() {
    log "Ошибка: $1"
    exit 1
}

show_error() {
    echo -e "\e[31mОшибка: $1\e[0m"
    # При запуске без терминала (GUI) не ждём Enter и не падаем
    if [ -t 0 ]; then
        read -p "Нажмите Enter для продолжения..."
    fi
}

# -----------------------------------------------------------------------------
# Проверка зависимостей
# -----------------------------------------------------------------------------

check_dependencies() {
    export PATH="$PATH:/usr/local/sbin:/usr/sbin:/sbin"
    local deps=("git" "grep" "sed" "curl")

    for dep in "${deps[@]}"; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            handle_error "Не установлена утилита $dep"
        fi
    done

    # Проверяем наличие хотя бы одного бэкенда файрвола
    if ! command -v nft &>/dev/null && ! command -v iptables &>/dev/null; then
        handle_error "Не установлен nftables или iptables. Установите один из них."
    fi
}

# -----------------------------------------------------------------------------
# Работа с конфигурацией
# -----------------------------------------------------------------------------

# Проверка существования conf.env и обязательных полей
# Использование: if check_conf_file "$CONF_FILE"; then ...
check_conf_file() {
    local conf_file="${1:-$CONF_FILE}"

    if [[ ! -f "$conf_file" ]]; then
        return 1
    fi

    local required_fields=("interface" "gamefiltertcp" "gamefilterudp" "strategy")
    for field in "${required_fields[@]}"; do
        if ! grep -q "^${field}=[^[:space:]]" "$conf_file"; then
            return 1
        fi
    done

    # firewall_backend опционален — по умолчанию auto
    if ! grep -q "^firewall_backend=" "$conf_file"; then
        if [[ -w "$conf_file" ]]; then
            echo "firewall_backend=auto" >> "$conf_file"
        elif type elevate >/dev/null 2>&1 && type is_root >/dev/null 2>&1 && ! is_root; then
            # Файл мог быть создан от root — дописываем через elevate
            elevate bash -c "echo 'firewall_backend=auto' >> '$conf_file'" 2>/dev/null || true
        fi
    fi

    return 0
}

# Загрузка конфигурации из файла
load_config() {
    local conf_file="${1:-$CONF_FILE}"

    if [[ ! -f "$conf_file" ]]; then
        handle_error "Файл конфигурации $conf_file не найден"
    fi

    source "$conf_file"

    if [[ -z "$interface" ]] || [[ -z "$gamefiltertcp" ]] || [[ -z "$gamefilterudp" ]] || [[ -z "$strategy" ]]; then
        handle_error "Отсутствуют обязательные параметры в конфигурационном файле"
    fi

    # По умолчанию автоопределение бэкенда
    FIREWALL_BACKEND="${firewall_backend:-auto}"
}

# -----------------------------------------------------------------------------
# Управление nfqws
# -----------------------------------------------------------------------------

check_nfqws_status() {
    if pgrep -f "nfqws" >/dev/null; then
        echo "Демоны nfqws запущены."
    else
        echo "Демоны nfqws не запущены."
    fi
}

# Остановка всех процессов nfqws
stop_nfqws() {
    elevate pkill -f nfqws 2>/dev/null || true
}

# -----------------------------------------------------------------------------
# Работа со стратегиями
# -----------------------------------------------------------------------------

# Обеспечивает наличие пользовательских списков (*-user.txt) в каталоге стратегий.
# nfqws запускается из $REPO_DIR и обращается к lists/*-user.txt; этих файлов нет
# в git, поэтому их создают здесь. Файлы живут в $BASE_DIR/user-lists и
# хардлинкуются в $REPO_DIR/lists, чтобы правки пользователя видел и nfqws.
ensure_user_lists() {
    local user_lists_dir="$BASE_DIR/user-lists"
    local list_dir="$REPO_DIR/lists"

    mkdir -p "$list_dir" "$user_lists_dir"

    local f user_file
    for f in ipset-exclude-user.txt list-general-user.txt list-exclude-user.txt; do
        user_file="$user_lists_dir/$f"
        touch "$user_file"
        chmod 644 "$user_file"
        # Хардлинк (не симлинк!); если не выходит (разные ФС) — копируем
        if ! ln -f "$user_file" "$list_dir/$f" 2>/dev/null; then
            cp -f "$user_file" "$list_dir/$f" 2>/dev/null || true
        fi
    done
}

# Обеспечивает наличие шаблонов поддельных пакетов bin/*.bin в каталоге стратегий.
# Стратегии ссылаются на %BIN%quic_initial_*.bin и %BIN%tls_clienthello_*.bin, но
# этих файлов нет ни в git-клоне стратегий (Flowseal), ни в архиве релиза zapret.
# Оригиналы лежат в bol-van/zapret в files/fake. Копии кешируются в $BASE_DIR/bin,
# чтобы при повторных запусках не качать заново.
ensure_bin_files() {
    local bin_dir="$REPO_DIR/bin"
    local cache_dir="$BASE_DIR/bin"
    local zapret_ref="${ZAPRET_BIN_REF:-$ZAPRET_RECOMMENDED_VERSION}"
    local base_url="https://raw.githubusercontent.com/bol-van/zapret/${zapret_ref}/files/fake"

    mkdir -p "$bin_dir" "$cache_dir"

    # Имена, которых нет в files/fake zapret: подставляем шаблон того же типа.
    local -A alias_map=(
        [quic_initial_dbankcloud_ru.bin]=quic_initial_www_google_com.bin
        [tls_clienthello_max_ru.bin]=tls_clienthello_www_google_com.bin
        [tls_clienthello_4pda_to.bin]=tls_clienthello_www_google_com.bin
    )

    local name file source
    for name in quic_initial_www_google_com.bin quic_initial_dbankcloud_ru.bin \
                tls_clienthello_www_google_com.bin tls_clienthello_max_ru.bin \
                tls_clienthello_4pda_to.bin stun.bin; do
        file="$bin_dir/$name"
        [[ -s "$file" ]] && continue

        # 1) Кеш: сначала прямой файл, затем алиас к нему
        source="${alias_map[$name]:-$name}"
        if [[ -s "$cache_dir/$source" ]]; then
            cp -f "$cache_dir/$source" "$file" && continue
        fi

        # 2) Алиас: берём уже готовый шаблон того же типа (quic_/tls_clienthello_)
        if [[ -n "${alias_map[$name]}" ]]; then
            local like
            if [[ "$name" == quic_* ]]; then
                like="quic_initial_www_google_com.bin"
            else
                like="tls_clienthello_www_google_com.bin"
            fi
            if [[ -s "$bin_dir/$like" || -s "$cache_dir/$like" ]]; then
                cp -f "${bin_dir}/$like" "$file" 2>/dev/null || cp -f "$cache_dir/$like" "$file"
                continue
            fi
        fi

        # 3) Скачиваем оригинал из bol-van/zapret
        if curl -fsSL --max-time 30 "$base_url/$source" -o "$cache_dir/$source" 2>/dev/null; then
            cp -f "$cache_dir/$source" "$file"
        fi
    done
}

# Настройка репозитория со стратегиями
# Требует: REPO_DIR, REPO_URL, MAIN_REPO_REV, BASE_DIR, INTERACTIVE_MODE (опционально)
# Аргументы:
#   $1 - версия (коммит/тег/ветка), по умолчанию MAIN_REPO_REV
setup_repository() {
    local version="${1:-$MAIN_REPO_REV}"
    local tmp_dir

    # В интерактивном режиме спрашиваем подтверждение на обновление
    if [ -d "$REPO_DIR" ] && [[ "${INTERACTIVE_MODE:-false}" == "true" ]]; then
        log "Обнаружен существующий репозиторий стратегий."
        read -p "Удалить существующий репозиторий и загрузить заново? [y/N]: " confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            log "Использование существующей версии репозитория."
            return 0
        fi
    fi

    log "Клонирование стратегий (версия: $version)..."
    tmp_dir=$(mktemp -d)

    # Проверяем, является ли версия хешем коммита (40 символов hex)
    if [[ "$version" =~ ^[0-9a-f]{40}$ ]]; then
        # Для хеша коммита клонируем весь репозиторий и делаем checkout
        timeout 180 git clone "$REPO_URL" "$tmp_dir/strategies" || {
            rm -rf "$tmp_dir"
            handle_error "Ошибка при клонировании репозитория"
        }

        (cd "$tmp_dir/strategies" && git checkout "$version") || {
            rm -rf "$tmp_dir"
            handle_error "Ошибка при переключении на коммит '$version'. Проверьте, что коммит существует."
        }
    else
        # Для тега или ветки используем shallow clone
        timeout 180 git clone --branch "$version" --depth 1 "$REPO_URL" "$tmp_dir/strategies" || {
            rm -rf "$tmp_dir"
            handle_error "Ошибка при клонировании репозитория. Проверьте, что версия '$version' существует."
        }
    fi

    # Переименовываем bat-файлы во временном клоне
    chmod +x "$BASE_DIR/src/rename_bat.sh"
    TARGET_DIR="$tmp_dir/strategies" "$BASE_DIR/src/rename_bat.sh" || {
        rm -rf "$tmp_dir"
        handle_error "Ошибка при переименовании файлов"
    }

    # Обновляем на месте только нужные файлы: bat-стратегии и списки.
    # Каталог не удаляется, чтобы не задеть файлы комплекта и пользовательские списки.
    # Если каталог ранее был создан от root, git/rm не смогут в него писать — чиним владельца.
    if [ -d "$REPO_DIR" ] && ! [ -w "$REPO_DIR" ]; then
        local current_user
        current_user=$(id -un)
        log "Каталог $REPO_DIR создан от root, восстанавливаю владельца ($current_user)..."
        elevate chown -R "$current_user" "$REPO_DIR" || {
            handle_error "Не удалось восстановить владельца $REPO_DIR. Выполните вручную: sudo chown -R $current_user $REPO_DIR"
        }
    fi

    mkdir -p "$REPO_DIR"
    rm -f "$REPO_DIR"/*.bat
    cp "$tmp_dir/strategies"/*.bat "$REPO_DIR/" 2>/dev/null || true

    if [[ -d "$tmp_dir/strategies/lists" ]]; then
        mkdir -p "$REPO_DIR/lists"
        # Пользовательские списки (*-user.txt) не перезаписываем
        cp "$tmp_dir/strategies/lists"/*.txt "$REPO_DIR/lists/" 2>/dev/null || true
    fi

    # Обеспечиваем наличие пользовательских списков
    ensure_user_lists
    # Обеспечиваем наличие шаблонов поддельных пакетов (bin/*.bin)
    ensure_bin_files

    rm -rf "$tmp_dir"
    log "Стратегии обновлены в $REPO_DIR"
}

# Проверка и создание конфига (helper для install_service и desktop)
ensure_config_exists() {
    if ! check_conf_file; then
        read -p "Конфигурация отсутствует или неполная. Создать конфигурацию сейчас? (y/n): " answer
        if [[ $answer =~ ^[Yy]$ ]]; then
            create_conf_file
        else
            echo "Операция отменена."
            read -p "Нажмите Enter для продолжения..."
            return 0
        fi
        # Перепроверяем конфигурацию
        if ! check_conf_file; then
            show_error "Файл конфигурации всё ещё некорректен. Операция отменена."
            return 0
        fi
    fi
    return 0
}

# Получение списка доступных стратегий (имена файлов)
# Требует: REPO_DIR, CUSTOM_STRATEGIES_DIR
get_strategies() {
    {
        # Кастомные стратегии
        if [ -d "$CUSTOM_STRATEGIES_DIR" ]; then
            find "$CUSTOM_STRATEGIES_DIR" -maxdepth 1 -type f -name "*.bat" -printf "%f\n" 2>/dev/null
        fi
        # Стратегии из репозитория
        if [ -d "$REPO_DIR" ]; then
            find "$REPO_DIR" -maxdepth 1 -type f \( -name "general*.bat" -o -name "discord*.bat" \) -printf "%f\n" 2>/dev/null
        fi
    } | sort -u
}

# Вывод списка стратегий
show_strategies() {
    echo "Доступные стратегии:"
    echo
    get_strategies
}

# Валидация и нормализация названия стратегии
# Возвращает 0 и выводит нормализованное имя, или 1 при ошибке
# Сравнение строковое, без regex — имена с пробелами/скобками/точками работают
normalize_strategy() {
    local s="$1"
    local candidate

    # Поиск точного совпадения
    while IFS= read -r candidate; do
        [[ -z "$candidate" ]] && continue
        if [[ "$candidate" == "$s" ]] || \
           [[ "$candidate" == "$s.bat" ]] || \
           [[ "$candidate" == "general_$s" ]] || \
           [[ "$candidate" == "general_$s.bat" ]]; then
            echo "$candidate"
            return 0
        fi
    done < <(get_strategies)

    # Регистронезависимый поиск
    local sl="${s,,}"
    while IFS= read -r candidate; do
        [[ -z "$candidate" ]] && continue
        local cl="${candidate,,}"
        if [[ "$cl" == "$sl" ]] || \
           [[ "$cl" == "$sl.bat" ]] || \
           [[ "$cl" == "general_$sl" ]] || \
           [[ "$cl" == "general_$sl.bat" ]]; then
            echo "$candidate"
            return 0
        fi
    done < <(get_strategies)

    return 1
}

# Интерактивный выбор стратегии
# Записывает результат в переменную $selected_strategy
select_strategy_interactive() {
    local strategies_list
    mapfile -t strategies_list < <(get_strategies)

    if [ ${#strategies_list[@]} -eq 0 ]; then
        handle_error "Не найдены файлы стратегий .bat"
    fi

    echo "Доступные стратегии:"
    select selected_strategy in "${strategies_list[@]}"; do
        if [ -n "$selected_strategy" ]; then
            log "Выбрана стратегия: $selected_strategy"
            return 0
        fi
        show_error "Неверный выбор. Попробуйте еще раз."
done
}

# Получение полного пути к файлу стратегии
# Возвращает путь к файлу или пустую строку если не найден
get_strategy_path() {
    local strategy="$1"

    if [ -f "$CUSTOM_STRATEGIES_DIR/$strategy" ]; then
        echo "$CUSTOM_STRATEGIES_DIR/$strategy"
    elif [ -f "$REPO_DIR/$strategy" ]; then
        echo "$REPO_DIR/$strategy"
    else
        echo ""
    fi
}

# -----------------------------------------------------------------------------
# Парсинг .bat файлов стратегий
# -----------------------------------------------------------------------------

# Парсинг параметров из bat файла
# Устанавливает глобальные переменные: tcp_ports, udp_ports, nfqws_params[]
# Требует: USE_GAME_FILTER, GAME_FILTER_PORTS
parse_bat_file() {
    local file="$1"
    local bin_path="bin/"
    debug_log "Parsing .bat file: $file"

    # Читаем весь файл целиком
    local content=$(cat "$file" | tr -d '\r')

    debug_log "File content loaded"

    # Заменяем переменные
    content="${content//%BIN%/$bin_path}"
    content="${content//%LISTS%/lists/}"

    # Обрабатываем GameFilter
    if [ "$USE_GAME_FILTER" = true ]; then
        content="${content//%GameFilter%/$GAME_FILTER_PORTS}"
        #TCP and UDP
        if [ "$USE_GAME_FILTER_TCP" = true ]; then
            content="${content//%GameFilterTCP%/$GAME_FILTER_PORTS}"
        else
            content="${content//%GameFilterTCP%/$GAME_FILTER_OFF_PORTS}"
        fi

        if [ "$USE_GAME_FILTER_UDP" = true ]; then
            content="${content//%GameFilterUDP%/$GAME_FILTER_PORTS}"
        else
            content="${content//%GameFilterUDP%/$GAME_FILTER_OFF_PORTS}"
        fi
    else
        content="${content//,%GameFilter%/}"
        content="${content//%GameFilter%,/}"
        #TCP and UDP
        content="${content//,%GameFilterTCP%/}"
        content="${content//%GameFilterTCP%,/}"
        content="${content//,%GameFilterUDP%/}"
        content="${content//%GameFilterUDP%,/}"
    fi

    # Ищем --wf-tcp и --wf-udp
    local wf_tcp_count=$(echo "$content" | grep -oP -- '--wf-tcp=' | wc -l)
    local wf_udp_count=$(echo "$content" | grep -oP -- '--wf-udp=' | wc -l)

    # Проверяем количество вхождений
    if [ "$wf_tcp_count" -eq 0 ] || [ "$wf_udp_count" -eq 0 ]; then
        echo "ERROR: --wf-tcp or --wf-udp not found in $file"
        exit 1
    fi

    if [ "$wf_tcp_count" -gt 1 ]; then
        echo "ERROR: Multiple --wf-tcp entries found in $file (found: $wf_tcp_count)"
        exit 1
    fi

    if [ "$wf_udp_count" -gt 1 ]; then
        echo "ERROR: Multiple --wf-udp entries found in $file (found: $wf_udp_count)"
        exit 1
    fi

    # Извлекаем порты
    tcp_ports=$(echo "$content" | grep -oP -- '--wf-tcp=\K[0-9,-]+' | head -n1)
    udp_ports=$(echo "$content" | grep -oP -- '--wf-udp=\K[0-9,-]+' | head -n1)

    debug_log "TCP ports: $tcp_ports"
    debug_log "UDP ports: $udp_ports"

    # Парсим с помощью grep -oP (Perl regex)
    nfqws_params=()
    while IFS= read -r match; do
        if [[ "$match" =~ --filter-(tcp|udp)=([0-9,%-]+)[[:space:]]+(.*) ]]; then
            local protocol="${BASH_REMATCH[1]}"
            local ports="${BASH_REMATCH[2]}"
            local nfqws_args="${BASH_REMATCH[3]}"

            # Очищаем лишние пробелы
            nfqws_args=$(echo "$match" | xargs)
            nfqws_args="${nfqws_args//=^!/=!}"

            nfqws_params+=("$nfqws_args")
            debug_log "Matched protocol: $protocol, ports: $ports"
            debug_log "NFQWS parameters: $nfqws_args"
        fi
    done < <(echo "$content" | grep -oP -- '--filter-(tcp|udp)=([0-9,-]+)\s+(?:[\s\S]*?--new|.*)')
}

# -----------------------------------------------------------------------------
# Запуск nfqws
# -----------------------------------------------------------------------------

# Запуск процесса nfqws
# Требует: NFQWS_PATH, REPO_DIR, NFT_MARK, NFT_QUEUE_NUM, nfqws_params[]
start_nfqws() {
    log "Запуск процесса nfqws..."
    stop_nfqws

    # nfqws ссылается на lists/*-user.txt из $REPO_DIR — гарантируем их наличие
    ensure_user_lists
    # nfqws ссылается на bin/*.bin из $REPO_DIR — гарантируем их наличие
    ensure_bin_files

    cd "$REPO_DIR" || handle_error "Не удалось перейти в директорию $REPO_DIR"

    local full_params=(
        "$NFQWS_PATH"
        --daemon
        --dpi-desync-fwmark="$NFT_MARK"
        --qnum="$NFT_QUEUE_NUM"
    )

    for params in "${nfqws_params[@]}"; do
        full_params+=($params)
    done

    debug_log "Запуск NFQWS с параметрами: ${full_params[@]}"
    elevate "${full_params[@]}" ||
        handle_error "Ошибка при запуске nfqws"
}

# -----------------------------------------------------------------------------
# Основная функция запуска zapret
# -----------------------------------------------------------------------------

# Запуск zapret с указанной конфигурацией
# Использует глобальные переменные из conf.env: interface, gamefiltertcp, gamefilterudp, strategy
# Требует: REPO_DIR, NFQWS_PATH, STOP_SCRIPT
run_zapret() {
    # Остановка предыдущего экземпляра
    stop_nfqws
    firewall_clear
    sleep 1

    # Установка USE_GAME_FILTER
    if [ "$gamefiltertcp" == "true" -a "$gamefilterudp" == "true" ]; then
        USE_GAME_FILTER=true
        USE_GAME_FILTER_TCP=true
        USE_GAME_FILTER_UDP=true
        log "GameFilterTCP и GameFilterUDP включен"

    elif [ "$gamefiltertcp" == "true" ]; then
        USE_GAME_FILTER=true
        USE_GAME_FILTER_TCP=true
        USE_GAME_FILTER_UDP=false
        log "GameFilterTCP включен"

    elif [ "$gamefilterudp" == "true" ]; then
        USE_GAME_FILTER=true
        USE_GAME_FILTER_TCP=false
        USE_GAME_FILTER_UDP=true
        log "GameFilterUDP включен"

    else
        USE_GAME_FILTER=false
        USE_GAME_FILTER_TCP=false
        USE_GAME_FILTER_UDP=false
        log "GameFilter выключен"
    fi

    # Получаем путь к стратегии
    local strategy_path
    strategy_path=$(get_strategy_path "$strategy")
    if [ -z "$strategy_path" ]; then
        handle_error "Указанный .bat файл стратегии $strategy не найден"
    fi

    # Парсим стратегию
    parse_bat_file "$strategy_path"

    # Настройка файрвола
    local backend
    backend=$(detect_firewall_backend) || handle_error "Не удалось определить бэкенд файрвола"
    log "Настройка $backend..."
    firewall_setup "$tcp_ports" "$udp_ports" "$interface" ||
        handle_error "Ошибка при настройке $backend"

    # Запуск nfqws
    start_nfqws
    log "Настройка успешно завершена"
}
