<div align="center">

# 🎧 InIProject — Zapret GUI for Linux

[Русский](README.md) · **English**

### Graphical interface to bypass YouTube and Discord throttling

A GUI wrapper (PySide6) around [zapret-discord-youtube-linux](https://github.com/Sergeydigl3/zapret-discord-youtube-linux). It contains no bypass logic of its own — all functionality is performed by the existing adapter scripts.

[![GitHub stars](https://img.shields.io/github/stars/SkilinPur/zapret-GUI?style=social)](https://github.com/SkilinPur/zapret-GUI/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/SkilinPur/zapret-GUI?style=social)](https://github.com/SkilinPur/zapret-GUI/network/members)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)

</div>

---

## About

`zapret-GUI` is a graphical interface built on top of the
[Sergeydigl3/zapret-discord-youtube-linux](https://github.com/Sergeydigl3/zapret-discord-youtube-linux) adapter.
It drives the same CLI (`service.sh`) as the original port: start/stop,
configuration, system service, dependency download and strategy autotune — no terminal needed.

**Tested on:** Arch Linux

**This is a fork of the Linux port.** The original strategies belong to
[Flowseal](https://github.com/Flowseal/zapret-discord-youtube), the core belongs to
[bol-van/zapret](https://github.com/bol-van/zapret).

---

## Features

- **Status** — zapret status indicator, start/stop (background daemon or systemd service), live log
- **Configuration** — strategy, interface, firewall backend, GameFilterTCP/UDP (saved to `conf.env`)
- **Strategies** — list of `.bat`, download/update dependencies (nfqws + strategies)
- **Service** — install/remove autostart service, start/stop/restart, logs
- **Autotune** — automatic strategy selection (`auto_tune_youtube.sh`, domain checks)
- **Permissions** — passwordless operation (NOPASSWD sudo)
- **Credits** — project authors with avatars and links

---

## Requirements

- Linux (works on any distro with a graphical session)
- Python 3.9+ and `python3-venv`
- System libraries for PySide6 (libEGL, libGL, libxkbcommon, xcb)
- nftables or iptables
- On first launch the GUI automatically installs PySide6 into `gui/.venv`

---

## Quick start

```bash
git clone https://github.com/SkilinPur/zapret-GUI.git
cd zapret-GUI

./service.sh download-deps --default   # download nfqws and strategies
./service.sh setup-permissions         # passwordless operation (NOPASSWD)
./service.sh gui                       # launch the GUI
```

Or directly:

```bash
./gui/gui.sh
```

The first launch will create a virtual environment and install PySide6.

---

## Usage

| Tab | Purpose |
|---|---|
| **How to use** | quick guide |
| **Status** | start/stop, mode (daemon / systemd), log |
| **Configuration** | strategy, interface, backend, GameFilter |
| **Strategies** | list of `.bat`, download dependencies |
| **Service** | autostart, status, logs |
| **Autotune** | strategy selection (experimental) |
| **Permissions** | NOPASSWD for passwordless operation |
| **Credits** | project authors |

The full CLI of the original port is also available: `./service.sh --help`.

---

## Credits

| Role | Author | Repository |
|---|---|---|
| GUI (graphical interface) | [SkilinPur](https://github.com/SkilinPur) | [zapret-GUI](https://github.com/SkilinPur/zapret-GUI) |
| Linux port (adapter) | [Sergeydigl3](https://github.com/Sergeydigl3) | [zapret-discord-youtube-linux](https://github.com/Sergeydigl3/zapret-discord-youtube-linux) |
| Original (strategies) | [Flowseal](https://github.com/Flowseal) | [zapret-discord-youtube](https://github.com/Flowseal/zapret-discord-youtube) |
| zapret core (nfqws) | [bol-van](https://github.com/bol-van) | [zapret](https://github.com/bol-van/zapret) |

The project is built around the Linux port by **Sergeydigl3**.
Original strategies — **Flowseal**, core — **bol-van**.

---

## License

Licensing terms are inherited from the original projects
([zapret](https://github.com/bol-van/zapret), [zapret-discord-youtube](https://github.com/Flowseal/zapret-discord-youtube)).
