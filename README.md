# 🍪 Cookie Clicker Multiplayer

Ein Cookie Clicker Spiel mit Flask-Backend und Echtzeit-Multiplayer-Unterstützung!

## Features

### 🎮 Spielmodi

- **Solo Modus**: Spiele alleine und sammle Cookies
- **Versus Modus (⚔️)**: Spiele gegen einen Freund - stehle Cookies voneinander!
- **Coop Modus (🤝)**: Spielt zusammen an einem gemeinsamen Cookie

### 🛒 Upgrades

#### Manuelle Klick-Upgrades (👆)
| Upgrade | Bonus | Basis-Kosten |
|---------|-------|--------------|
| Verstärkter Finger | +1 pro Klick | 15 |
| Doppelklick | +5 pro Klick | 100 |
| Turbo-Finger | +25 pro Klick | 1.000 |
| Mega-Klick | +100 pro Klick | 10.000 |

#### Automatische Upgrades (🤖)
| Upgrade | Cookies/Sekunde | Basis-Kosten |
|---------|-----------------|--------------|
| Automatischer Cursor | +0.1 | 10 |
| Oma | +1 | 100 |
| Cookie-Farm | +5 | 500 |
| Cookie-Fabrik | +20 | 2.000 |
| Cookie-Mine | +50 | 10.000 |
| Cookie-Bank | +100 | 50.000 |
| Cookie-Tempel | +250 | 200.000 |
| Cookie-Portal | +1.000 | 1.000.000 |

### 🦹 Versus-Modus Spezial

- **Cookies stehlen**: Alle 30 Sekunden kannst du 5% der Cookies deines Gegners stehlen (mindestens 10 Cookies)

## Installation

### Voraussetzungen
- Python 3.8+
- pip

### Setup

```bash
# Repository klonen oder Dateien herunterladen
cd /workspace

# Virtuelle Umgebung erstellen (optional, aber empfohlen)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt
```

### Server starten

```bash
python app.py
```

Der Server startet auf `http://localhost:5000`

## Spielanleitung

### Solo spielen
1. Gib deinen Namen ein
2. Klicke auf "Solo Spielen"
3. Klicke auf den Cookie, um Cookies zu sammeln
4. Kaufe Upgrades, um mehr Cookies zu produzieren

### Versus-Modus
1. **Spieler 1**: Klicke auf "Versus-Raum erstellen"
2. **Spieler 1**: Teile den 6-stelligen Raum-Code mit deinem Freund
3. **Spieler 2**: Gib den Code ein und klicke "Beitreten"
4. Sammelt Cookies und stehlt euch gegenseitig welche!

### Coop-Modus
1. **Spieler 1**: Klicke auf "Coop-Raum erstellen"
2. **Spieler 1**: Teile den 6-stelligen Raum-Code mit deinem Freund
3. **Spieler 2**: Gib den Code ein und klicke "Beitreten"
4. Arbeitet zusammen am gemeinsamen Cookie!

## Tastaturkürzel

- **Leertaste**: Cookie klicken

## Technologie-Stack

- **Backend**: Flask + Flask-SocketIO
- **Frontend**: Vanilla JavaScript + HTML5 + CSS3
- **Echtzeit-Kommunikation**: WebSockets (Socket.IO)
- **Async-Server**: Eventlet

## Projektstruktur

```
/workspace/
├── app.py                 # Flask Backend
├── requirements.txt       # Python Abhängigkeiten
├── README.md              # Diese Datei
├── templates/
│   └── index.html         # HTML Template
└── static/
    ├── css/
    │   └── style.css      # Styles
    └── js/
        └── game.js        # Frontend Logik
```

## Lizenz

MIT License - Viel Spaß beim Spielen! 🍪
