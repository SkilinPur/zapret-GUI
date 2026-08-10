<div align="center">

# 🎧 InIProject — Zapret GUI for Linux

**Русский** · [English](README_EN.md)

### Графический интерфейс для обхода замедления YouTube и Discord

GUI-обёртка (PySide6) вокруг [zapret-discord-youtube-linux](https://github.com/Sergeydigl3/zapret-discord-youtube-linux). Не содержит собственной логики обхода — весь функционал выполняют существующие скрипты адаптера.

[![GitHub stars](https://img.shields.io/github/stars/SkilinPur/zapret-GUI?style=social)](https://github.com/SkilinPur/zapret-GUI/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/SkilinPur/zapret-GUI?style=social)](https://github.com/SkilinPur/zapret-GUI/network/members)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)

</div>

---

## О проекте

`zapret-GUI` — это графический интерфейс поверх адаптера
[Sergeydigl3/zapret-discord-youtube-linux](https://github.com/Sergeydigl3/zapret-discord-youtube-linux).
Скрипт управляет тем же CLI (`service.sh`), что и оригинальный порт: запуск/остановка,
конфигурация, системный сервис, загрузка зависимостей и автоподбор стратегий — без работы в терминале.

**Протестировано на:** Arch Linux

**Это форк порта на Linux.** Исходные стратегии принадлежат проекту
[Flowseal](https://github.com/Flowseal/zapret-discord-youtube), ядро — проекту
[bol-van/zapret](https://github.com/bol-van/zapret).

---

## Возможности

- **Статус** — индикатор работы zapret, запуск/остановка (фоновый демон или systemd-сервис), живой лог
- **Конфигурация** — стратегия, интерфейс, бэкенд фаервола, GameFilterTCP/UDP (сохраняется в `conf.env`)
- **Стратегии** — список `.bat` (23 в комплекте), обновление стратегий и скачивание nfqws по отдельности
- **Сервис** — установка/удаление службы автозагрузки, запуск/остановка/перезапуск, логи
- **Автоподбор** — автоматический подбор рабочей стратегии (`auto_tune_youtube.sh`, проверка доменов)
- **Права** — настройка работы без пароля (NOPASSWD sudo)
- **Авторство** — авторы проекта с аватарками и ссылками

---

## Требования

- Linux (работает на любом дистрибутиве с графической сессией)
- Python 3.9+ и `python3-venv`
- Системные библиотеки для PySide6 (libEGL, libGL, libxkbcommon, xcb)
- nftables или iptables
- При первом запуске GUI автоматически устанавливает PySide6 в `gui/.venv`

---

## Быстрый старт

```bash
git clone https://github.com/SkilinPur/zapret-GUI.git
cd zapret-GUI

./service.sh download-nfqws         # скачать nfqws, если ещё не установлен
./service.sh setup-permissions      # работа без пароля (NOPASSWD)
./service.sh gui                    # запуск GUI
```

Стратегии уже в комплекте (папка `zapret-latest`), ничего скачивать для них не нужно.
При необходимости стратегии можно обновить: `./service.sh update-strategies`.

Или напрямую:

```bash
./gui/gui.sh
```

Первый запуск создаст виртуальное окружение и установит PySide6.

---

## Использование

| Вкладка | Назначение |
|---|---|
| **Как пользоваться** | краткое руководство |
| **Статус** | запуск/остановка, режим (демон / systemd), лог |
| **Конфигурация** | стратегия, интерфейс, бэкенд, GameFilter |
| **Стратегии** | список `.bat` (23 в комплекте), обновление стратегий, скачивание nfqws |
| **Обновление** | проверка версии и обновление программы |
| **Сервис** | автозагрузка, статус, логи |
| **Автоподбор** | подбор рабочей стратегии (экспериментально) |
| **Права** | NOPASSWD для запуска без пароля |
| **Авторство** | авторы проекта |

Также доступен полноценный CLI оригинального порта: `./service.sh --help`.

---

## Авторство

| Роль | Автор | Репозиторий |
|---|---|---|
| GUI (графический интерфейс) | [SkilinPur](https://github.com/SkilinPur) | [zapret-GUI](https://github.com/SkilinPur/zapret-GUI) |
| Порт на Linux (адаптер) | [Sergeydigl3](https://github.com/Sergeydigl3) | [zapret-discord-youtube-linux](https://github.com/Sergeydigl3/zapret-discord-youtube-linux) |
| Исходник (стратегии) | [Flowseal](https://github.com/Flowseal) | [zapret-discord-youtube](https://github.com/Flowseal/zapret-discord-youtube) |
| Ядро zapret (nfqws) | [bol-van](https://github.com/bol-van) | [zapret](https://github.com/bol-van/zapret) |

Проект собран вокруг порта на Linux от **Sergeydigl3**.
Исходные стратегии — **Flowseal**, ядро — **bol-van**.

---

## Лицензия

Лицензионные условия наследуются от оригинальных проектов
([zapret](https://github.com/bol-van/zapret), [zapret-discord-youtube](https://github.com/Flowseal/zapret-discord-youtube)).
