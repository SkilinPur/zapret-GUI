# GUI для zapret-discord-youtube-linux

Графический интерфейс (PySide6) для управления обходом замедления YouTube и Discord.

## Запуск

```bash
./service.sh gui
# или напрямую:
./gui/gui.sh
```

При первом запуске автоматически создаётся виртуальное окружение `gui/.venv`
и устанавливается PySide6. Зависимости: `python3` (>= 3.9).

## Возможности

- **Статус** — индикатор работы zapret, запуск/остановка (фоновый демон или systemd-сервис), живой лог
- **Конфигурация** — стратегия, интерфейс, бэкенд файрвола, GameFilter (сохраняется в `conf.env`)
- **Стратегии** — список `.bat`, скачивание/обновление зависимостей
- **Сервис** — установка/удаление/запуск systemd-сервиса, просмотр логов
- **Автоподбор** — `auto_tune_youtube.sh` и проверка произвольных доменов
- **Права** — настройка NOPASSWD для работы без пароля

## Авторство

Проект собран вокруг порта на Linux от **Sergeydigl3**. Исходные стратегии — **Flowseal**, ядро — **bol-van**.

| Роль | Автор | Репозиторий |
|---|---|---|
| GUI (графический интерфейс) | [SkilinPur](https://github.com/SkilinPur) | [zapret-GUI](https://github.com/SkilinPur/zapret-GUI) |
| Порт на Linux (адаптер) | [Sergeydigl3](https://github.com/Sergeydigl3) | [zapret-discord-youtube-linux](https://github.com/Sergeydigl3/zapret-discord-youtube-linux) |
| Исходник (стратегии) | [Flowseal](https://github.com/Flowseal) | [zapret-discord-youtube](https://github.com/Flowseal/zapret-discord-youtube) |
| Ядро zapret (nfqws) | [bol-van](https://github.com/bol-van) | [zapret](https://github.com/bol-van/zapret) |

## Портативность

GUI не привязан к конкретной папке: все пути вычисляются от расположения файлов
(`realpath` в bash, `Path(__file__).resolve()` в Python). Скрипт можно перемещать
или копировать в любое место (например, `/opt/zapret-gui`) — `service.sh`
и `gui.sh` найдут друг друга автоматически.

> Примечание: PySide6 требует системные библиотеки X11/OpenGL
> (libEGL, libGL, libxkbcommon, xcb). На минимальных дистрибутивах их нужно
> доставить через пакетный менеджер.
