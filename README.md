<div align="center">

# ⚡ zapret-GUI — Linux

### Графический интерфейс для обхода замедления YouTube и Discord

Управляет существующими скриптами [zapret-discord-youtube-linux](https://github.com/Sergeydigl3/zapret-discord-youtube-linux) — вся логика обхода выполняется проверенными bash-скриптами адаптера, GUI их просто удобно запускает.

[![Релиз](https://img.shields.io/github/v/release/SkilinPur/zapret-GUI?color=8b5cf6&label=релиз&logo=github)](https://github.com/SkilinPur/zapret-GUI/releases)
[![Платформа](https://img.shields.io/badge/платформа-Linux-2ea44f?logo=linux&logoColor=white)]()
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)]()
[![UI](https://img.shields.io/badge/UI-PySide6-41cd52)]()
[![Ядро](https://img.shields.io/badge/ядро-nfqws%20(zapret)-informational)]()
[![Стратегии](https://img.shields.io/badge/стратегии-Flowseal-red)]()

</div>

---

## О проекте

**zapret-GUI** — это самодостаточная графическая обёртка над Linux-портом zapret.
Она не содержит собственной логики обхода: запуск/остановка, выбор способа,
фаервол и обновления выполняют существующие скрипты адаптера — те же команды,
что и через CLI.

Протестировано на **Arch Linux** (работает на любом дистрибутиве с графической
сессией).

> Windows-версия того же GUI: [SkilinPur/zapret-GUI-Windows](https://github.com/SkilinPur/zapret-GUI-Windows)

## Возможности

- **Самодостаточность** — в одном окне версии и обновление трёх компонентов:
  программа (GUI), ядро nfqws, стратегии Flowseal. Проверка обновлений
  автоматически при открытии вкладки.
- **Статус** — запуск/остановка, живой лог, состояние.
- **Способ обхода с описанием** — каждый `.bat` автоматически расшифровывается
  (что обходит, какие порты и метод), чтобы было понятно без словаря.
- **Мастер первого запуска** — пошагово: права → ядро → способ обхода → запуск.
- **Тёмная тема, системный трей** — окно сворачивается в трей, из трея —
  показать/выйти и быстрый запуск/остановка.
- **Понятные термины** — GameFilter, бэкенд фаервола и пр. с пояснениями.
- **CLI адаптера** полностью доступен: `./service.sh --help`.

## Как это устроено

```
┌──────────────┐   команды    ┌─────────────────────┐
│  zapret-GUI  │ ───────────▶ │  service.sh (адаптер)│
│  (PySide6)   │              └──────────┬──────────┘
└──────────────┘                         │
                                         ▼
              ┌──────────────┬─────────────────────┐
              │ ядро: nfqws  │ фаервол: nftables/   │
              │ (bol-van)    │ iptables             │
              └──────────────┴─────────────────────┘
  стратегии: Flowseal/zapret-discord-youtube (.bat + списки)
```

- **Ядро** — `nfqws` из релизов [bol-van/zapret](https://github.com/bol-van/zapret).
- **Стратегии** — `.bat`-наборы параметров из [Flowseal/zapret-discord-youtube](https://github.com/Flowseal/zapret-discord-youtube).
- **Перехват** — nftables/iptables (netfilter queue).

## Быстрый старт

```bash
git clone https://github.com/SkilinPur/zapret-GUI.git
cd zapret-GUI

./service.sh download-nfqws         # ядро, если ещё не установлено
./service.sh setup-permissions      # работа без пароля (спросит пароль sudo)
./gui/gui.sh                        # запуск GUI
```

Первый запуск создаст виртуальное окружение и установит PySide6.
Стратегии уже в комплекте; списки и шаблоны `bin/*.bin` подтягиваются сами.
Приложение можно запускать и из меню: вкладка «Сервис» → «Установить ярлык».

## Вкладки

| Вкладка | Что делает |
|---|---|
| **Статус** | запуск/остановка, режим (фон / systemd-сервис), живой лог |
| **Конфигурация** | способ обхода (с описанием), интерфейс, бэкенд фаервола, GameFilter |
| **Обновление** | модули «Программа / Ядро nfqws / Стратегии»: версии, статус, обновление; история изменений |
| **Как пользоваться** | короткое руководство + «🚀 Мастер настройки» |
| **Сервис** | автозапуск (системная служба), ярлык в меню приложений |
| **Автоподбор** | подбор рабочей стратегии |
| **Права** | запуск без запроса пароля (NOPASSWD sudo) |
| **Авторство** | авторы проекта |

## Обновление

Всё обновляется из вкладки **«Обновление»**:

- **Программа** — обновление GUI через git (предложение перезапуска);
- **Ядро nfqws** — скачивание последнего стабильного релиза bol-van/zapret;
- **Стратегии Flowseal** — актуальные `.bat`, списки и шаблоны.

Ядро и стратегии обновляются **одной проверенной связкой**, чтобы не разъезжаться
с версиями параметров.

## Требования

- Linux с графической сессией
- Python 3.9+ и `python3-venv`
- Системные библиотеки PySide6 (libEGL, libGL, libxkbcommon, xcb)
- nftables или iptables

## Авторство

| Роль | Автор | Репозиторий |
|---|---|---|
| GUI (этот проект) | [SkilinPur](https://github.com/SkilinPur) | [zapret-GUI](https://github.com/SkilinPur/zapret-GUI) |
| Порт на Linux (адаптер) | [Sergeydigl3](https://github.com/Sergeydigl3) | [zapret-discord-youtube-linux](https://github.com/Sergeydigl3/zapret-discord-youtube-linux) |
| Стратегии | [Flowseal](https://github.com/Flowseal) | [zapret-discord-youtube](https://github.com/Flowseal/zapret-discord-youtube) |
| Ядро zapret | [bol-van](https://github.com/bol-van) | [zapret](https://github.com/bol-van/zapret) |

## Лицензия и предупреждение

Лицензионные условия наследуются от исходных проектов
([zapret](https://github.com/bol-van/zapret),
[zapret-discord-youtube](https://github.com/Flowseal/zapret-discord-youtube),
[zapret-discord-youtube-linux](https://github.com/Sergeydigl3/zapret-discord-youtube-linux)).

Программа предназначена для обхода технических ограничений и замедлений
в странах, где это разрешено законом. Используйте её ответственно — соблюдайте
законодательство вашей юрисдикции.
