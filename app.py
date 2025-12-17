"""
Cookie Clicker Multiplayer - Flask Backend
==========================================
Ein Cookie Clicker Spiel mit Multiplayer-Unterstützung (Coop & Versus Modus)
"""

from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
import time
import random
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cookie-clicker-secret-key-2024'

# Threading-Modus funktioniert auf allen Python-Versionen (inkl. 3.13)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# =============================================================================
# GAME CONFIGURATION
# =============================================================================

UPGRADES = {
    # Manuelle Klick-Upgrades
    'click_power_1': {
        'name': 'Verstärkter Finger',
        'description': '+1 Cookie pro Klick',
        'type': 'click',
        'bonus': 1,
        'base_cost': 15,
        'cost_multiplier': 1.15,
        'icon': '👆'
    },
    'click_power_2': {
        'name': 'Doppelklick',
        'description': '+5 Cookies pro Klick',
        'type': 'click',
        'bonus': 5,
        'base_cost': 100,
        'cost_multiplier': 1.2,
        'icon': '✌️'
    },
    'click_power_3': {
        'name': 'Turbo-Finger',
        'description': '+25 Cookies pro Klick',
        'type': 'click',
        'bonus': 25,
        'base_cost': 1000,
        'cost_multiplier': 1.25,
        'icon': '🖐️'
    },
    'click_power_4': {
        'name': 'Mega-Klick',
        'description': '+100 Cookies pro Klick',
        'type': 'click',
        'bonus': 100,
        'base_cost': 10000,
        'cost_multiplier': 1.3,
        'icon': '💪'
    },
    
    # Automatische Klick-Upgrades (Cookies pro Sekunde)
    'auto_cursor': {
        'name': 'Automatischer Cursor',
        'description': '+0.1 Cookies/Sekunde',
        'type': 'auto',
        'bonus': 0.1,
        'base_cost': 10,
        'cost_multiplier': 1.1,
        'icon': '🖱️'
    },
    'auto_grandma': {
        'name': 'Oma',
        'description': '+1 Cookie/Sekunde',
        'type': 'auto',
        'bonus': 1,
        'base_cost': 100,
        'cost_multiplier': 1.15,
        'icon': '👵'
    },
    'auto_farm': {
        'name': 'Cookie-Farm',
        'description': '+5 Cookies/Sekunde',
        'type': 'auto',
        'bonus': 5,
        'base_cost': 500,
        'cost_multiplier': 1.2,
        'icon': '🌾'
    },
    'auto_factory': {
        'name': 'Cookie-Fabrik',
        'description': '+20 Cookies/Sekunde',
        'type': 'auto',
        'bonus': 20,
        'base_cost': 2000,
        'cost_multiplier': 1.25,
        'icon': '🏭'
    },
    'auto_mine': {
        'name': 'Cookie-Mine',
        'description': '+50 Cookies/Sekunde',
        'type': 'auto',
        'bonus': 50,
        'base_cost': 10000,
        'cost_multiplier': 1.3,
        'icon': '⛏️'
    },
    'auto_bank': {
        'name': 'Cookie-Bank',
        'description': '+100 Cookies/Sekunde',
        'type': 'auto',
        'bonus': 100,
        'base_cost': 50000,
        'cost_multiplier': 1.35,
        'icon': '🏦'
    },
    'auto_temple': {
        'name': 'Cookie-Tempel',
        'description': '+250 Cookies/Sekunde',
        'type': 'auto',
        'bonus': 250,
        'base_cost': 200000,
        'cost_multiplier': 1.4,
        'icon': '🛕'
    },
    'auto_portal': {
        'name': 'Cookie-Portal',
        'description': '+1000 Cookies/Sekunde',
        'type': 'auto',
        'bonus': 1000,
        'base_cost': 1000000,
        'cost_multiplier': 1.5,
        'icon': '🌀'
    }
}

# Versus-Modus Spezial-Aktionen
STEAL_COOLDOWN = 30  # Sekunden zwischen Diebstählen
STEAL_PERCENTAGE = 0.05  # 5% der Cookies stehlen
STEAL_MIN = 10  # Mindestens 10 Cookies stehlen

# =============================================================================
# GAME STATE
# =============================================================================

# Spieler-Daten
players = {}  # player_id -> player_data

# Räume für Multiplayer
rooms = {}  # room_id -> room_data

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_player(player_id, name):
    """Erstellt einen neuen Spieler"""
    return {
        'id': player_id,
        'name': name,
        'cookies': 0,
        'total_cookies': 0,
        'click_power': 1,
        'cookies_per_second': 0,
        'upgrades': {key: 0 for key in UPGRADES.keys()},
        'last_steal': 0,
        'room_id': None,
        'last_update': time.time()
    }

def calculate_upgrade_cost(upgrade_id, owned_count):
    """Berechnet die Kosten für das nächste Upgrade"""
    upgrade = UPGRADES[upgrade_id]
    return int(upgrade['base_cost'] * (upgrade['cost_multiplier'] ** owned_count))

def calculate_player_stats(player):
    """Berechnet die Spielerstatistiken basierend auf Upgrades"""
    click_power = 1
    cookies_per_second = 0
    
    for upgrade_id, count in player['upgrades'].items():
        if count > 0:
            upgrade = UPGRADES[upgrade_id]
            if upgrade['type'] == 'click':
                click_power += upgrade['bonus'] * count
            elif upgrade['type'] == 'auto':
                cookies_per_second += upgrade['bonus'] * count
    
    player['click_power'] = click_power
    player['cookies_per_second'] = cookies_per_second
    return player

def get_player_state(player):
    """Gibt den Spielzustand für einen Spieler zurück"""
    upgrade_costs = {}
    for upgrade_id in UPGRADES.keys():
        upgrade_costs[upgrade_id] = calculate_upgrade_cost(upgrade_id, player['upgrades'][upgrade_id])
    
    return {
        'id': player['id'],
        'name': player['name'],
        'cookies': int(player['cookies']),
        'total_cookies': int(player['total_cookies']),
        'click_power': player['click_power'],
        'cookies_per_second': player['cookies_per_second'],
        'upgrades': player['upgrades'],
        'upgrade_costs': upgrade_costs,
        'last_steal': player['last_steal']
    }

def get_room_state(room_id):
    """Gibt den Raumzustand zurück"""
    if room_id not in rooms:
        return None
    
    room = rooms[room_id]
    player_states = []
    
    for pid in room['players']:
        if pid in players:
            player_states.append(get_player_state(players[pid]))
    
    return {
        'room_id': room_id,
        'mode': room['mode'],
        'players': player_states,
        'shared_cookies': room.get('shared_cookies', 0),
        'shared_total': room.get('shared_total', 0),
        'shared_cps': room.get('shared_cps', 0),
        'shared_click_power': room.get('shared_click_power', 1),
        'shared_upgrades': room.get('shared_upgrades', {})
    }

# =============================================================================
# ROUTES
# =============================================================================

@app.route('/')
def index():
    return render_template('index.html', upgrades=UPGRADES)

# =============================================================================
# SOCKET EVENTS
# =============================================================================

@socketio.on('connect')
def handle_connect():
    print(f'Client verbunden: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    player_id = request.sid
    if player_id in players:
        player = players[player_id]
        room_id = player.get('room_id')
        
        if room_id and room_id in rooms:
            rooms[room_id]['players'].remove(player_id)
            leave_room(room_id)
            
            # Informiere andere Spieler
            emit('player_left', {
                'player_id': player_id,
                'player_name': player['name']
            }, room=room_id)
            
            # Lösche leere Räume
            if len(rooms[room_id]['players']) == 0:
                del rooms[room_id]
        
        del players[player_id]
    print(f'Client getrennt: {player_id}')

@socketio.on('join_game')
def handle_join_game(data):
    """Spieler tritt dem Spiel bei"""
    player_id = request.sid
    name = data.get('name', f'Spieler_{player_id[:4]}')
    
    players[player_id] = create_player(player_id, name)
    
    emit('game_joined', {
        'player': get_player_state(players[player_id]),
        'upgrades_info': UPGRADES
    })

@socketio.on('create_room')
def handle_create_room(data):
    """Erstellt einen neuen Multiplayer-Raum"""
    player_id = request.sid
    mode = data.get('mode', 'versus')  # 'versus' oder 'coop'
    
    if player_id not in players:
        emit('error', {'message': 'Spieler nicht gefunden'})
        return
    
    room_id = str(uuid.uuid4())[:6].upper()
    
    rooms[room_id] = {
        'id': room_id,
        'mode': mode,
        'players': [player_id],
        'created_at': time.time()
    }
    
    # Coop-Modus: Gemeinsame Ressourcen
    if mode == 'coop':
        rooms[room_id]['shared_cookies'] = 0
        rooms[room_id]['shared_total'] = 0
        rooms[room_id]['shared_cps'] = 0
        rooms[room_id]['shared_click_power'] = 1
        rooms[room_id]['shared_upgrades'] = {key: 0 for key in UPGRADES.keys()}
    
    players[player_id]['room_id'] = room_id
    join_room(room_id)
    
    emit('room_created', {
        'room_id': room_id,
        'mode': mode,
        'room_state': get_room_state(room_id)
    })

@socketio.on('join_room')
def handle_join_room(data):
    """Spieler tritt einem bestehenden Raum bei"""
    player_id = request.sid
    room_id = data.get('room_id', '').upper()
    
    if player_id not in players:
        emit('error', {'message': 'Spieler nicht gefunden'})
        return
    
    if room_id not in rooms:
        emit('error', {'message': 'Raum nicht gefunden'})
        return
    
    if len(rooms[room_id]['players']) >= 2:
        emit('error', {'message': 'Raum ist voll'})
        return
    
    rooms[room_id]['players'].append(player_id)
    players[player_id]['room_id'] = room_id
    join_room(room_id)
    
    # Informiere alle Spieler im Raum
    emit('room_joined', {
        'room_id': room_id,
        'room_state': get_room_state(room_id)
    }, room=room_id)

@socketio.on('leave_room')
def handle_leave_room():
    """Spieler verlässt den Raum"""
    player_id = request.sid
    
    if player_id not in players:
        return
    
    player = players[player_id]
    room_id = player.get('room_id')
    
    if room_id and room_id in rooms:
        rooms[room_id]['players'].remove(player_id)
        leave_room(room_id)
        
        emit('player_left', {
            'player_id': player_id,
            'player_name': player['name']
        }, room=room_id)
        
        if len(rooms[room_id]['players']) == 0:
            del rooms[room_id]
    
    player['room_id'] = None
    emit('room_left', {'success': True})

@socketio.on('click_cookie')
def handle_click(data=None):
    """Cookie wurde geklickt"""
    player_id = request.sid
    
    if player_id not in players:
        return
    
    player = players[player_id]
    room_id = player.get('room_id')
    
    # Coop-Modus: Gemeinsame Cookies
    if room_id and room_id in rooms and rooms[room_id]['mode'] == 'coop':
        room = rooms[room_id]
        cookies_earned = room['shared_click_power']
        room['shared_cookies'] += cookies_earned
        room['shared_total'] += cookies_earned
        
        emit('cookie_clicked', {
            'player_id': player_id,
            'player_name': player['name'],
            'cookies_earned': cookies_earned,
            'room_state': get_room_state(room_id)
        }, room=room_id)
    else:
        # Solo oder Versus Modus
        cookies_earned = player['click_power']
        player['cookies'] += cookies_earned
        player['total_cookies'] += cookies_earned
        
        if room_id and room_id in rooms:
            emit('cookie_clicked', {
                'player_id': player_id,
                'player_name': player['name'],
                'cookies_earned': cookies_earned,
                'room_state': get_room_state(room_id)
            }, room=room_id)
        else:
            emit('game_update', {'player': get_player_state(player)})

@socketio.on('buy_upgrade')
def handle_buy_upgrade(data):
    """Upgrade kaufen"""
    player_id = request.sid
    upgrade_id = data.get('upgrade_id')
    
    if player_id not in players:
        return
    
    if upgrade_id not in UPGRADES:
        emit('error', {'message': 'Ungültiges Upgrade'})
        return
    
    player = players[player_id]
    room_id = player.get('room_id')
    
    # Coop-Modus: Gemeinsame Upgrades
    if room_id and room_id in rooms and rooms[room_id]['mode'] == 'coop':
        room = rooms[room_id]
        current_count = room['shared_upgrades'].get(upgrade_id, 0)
        cost = calculate_upgrade_cost(upgrade_id, current_count)
        
        if room['shared_cookies'] >= cost:
            room['shared_cookies'] -= cost
            room['shared_upgrades'][upgrade_id] = current_count + 1
            
            # Berechne neue Stats
            click_power = 1
            cps = 0
            for uid, count in room['shared_upgrades'].items():
                if count > 0:
                    upgrade = UPGRADES[uid]
                    if upgrade['type'] == 'click':
                        click_power += upgrade['bonus'] * count
                    elif upgrade['type'] == 'auto':
                        cps += upgrade['bonus'] * count
            
            room['shared_click_power'] = click_power
            room['shared_cps'] = cps
            
            emit('upgrade_bought', {
                'player_id': player_id,
                'player_name': player['name'],
                'upgrade_id': upgrade_id,
                'room_state': get_room_state(room_id)
            }, room=room_id)
        else:
            emit('error', {'message': 'Nicht genug Cookies'})
    else:
        # Solo oder Versus Modus
        current_count = player['upgrades'].get(upgrade_id, 0)
        cost = calculate_upgrade_cost(upgrade_id, current_count)
        
        if player['cookies'] >= cost:
            player['cookies'] -= cost
            player['upgrades'][upgrade_id] = current_count + 1
            player = calculate_player_stats(player)
            
            if room_id and room_id in rooms:
                emit('upgrade_bought', {
                    'player_id': player_id,
                    'player_name': player['name'],
                    'upgrade_id': upgrade_id,
                    'room_state': get_room_state(room_id)
                }, room=room_id)
            else:
                emit('game_update', {'player': get_player_state(player)})
        else:
            emit('error', {'message': 'Nicht genug Cookies'})

@socketio.on('steal_cookies')
def handle_steal(data):
    """Cookies vom Gegner stehlen (nur Versus-Modus)"""
    player_id = request.sid
    target_id = data.get('target_id')
    
    if player_id not in players:
        return
    
    player = players[player_id]
    room_id = player.get('room_id')
    
    if not room_id or room_id not in rooms:
        emit('error', {'message': 'Du bist in keinem Raum'})
        return
    
    room = rooms[room_id]
    
    if room['mode'] != 'versus':
        emit('error', {'message': 'Stehlen nur im Versus-Modus möglich'})
        return
    
    if target_id not in players or target_id not in room['players']:
        emit('error', {'message': 'Ziel nicht gefunden'})
        return
    
    # Cooldown prüfen
    current_time = time.time()
    time_since_steal = current_time - player['last_steal']
    
    if time_since_steal < STEAL_COOLDOWN:
        remaining = int(STEAL_COOLDOWN - time_since_steal)
        emit('error', {'message': f'Warte noch {remaining} Sekunden'})
        return
    
    target = players[target_id]
    
    # Berechne gestohlene Cookies
    steal_amount = max(STEAL_MIN, int(target['cookies'] * STEAL_PERCENTAGE))
    actual_stolen = min(steal_amount, int(target['cookies']))
    
    if actual_stolen <= 0:
        emit('error', {'message': 'Gegner hat keine Cookies zum Stehlen'})
        return
    
    target['cookies'] -= actual_stolen
    player['cookies'] += actual_stolen
    player['last_steal'] = current_time
    
    emit('cookies_stolen', {
        'thief_id': player_id,
        'thief_name': player['name'],
        'victim_id': target_id,
        'victim_name': target['name'],
        'amount': actual_stolen,
        'room_state': get_room_state(room_id)
    }, room=room_id)

@socketio.on('request_update')
def handle_request_update():
    """Fordert ein Spielupdate an"""
    player_id = request.sid
    
    if player_id not in players:
        return
    
    player = players[player_id]
    room_id = player.get('room_id')
    
    if room_id and room_id in rooms:
        emit('game_update', {'room_state': get_room_state(room_id)})
    else:
        emit('game_update', {'player': get_player_state(player)})

def auto_cookie_generator():
    """Hintergrund-Task für automatische Cookie-Generierung"""
    while True:
        socketio.sleep(0.1)  # 10 mal pro Sekunde
        
        current_time = time.time()
        
        # Solo & Versus: Individuelle CPS
        for player_id, player in list(players.items()):
            if player['cookies_per_second'] > 0:
                room_id = player.get('room_id')
                
                # Nicht für Coop-Spieler
                if room_id and room_id in rooms and rooms[room_id]['mode'] == 'coop':
                    continue
                
                cookies_earned = player['cookies_per_second'] * 0.1
                player['cookies'] += cookies_earned
                player['total_cookies'] += cookies_earned
        
        # Coop: Gemeinsame CPS
        for room_id, room in list(rooms.items()):
            if room['mode'] == 'coop' and room.get('shared_cps', 0) > 0:
                cookies_earned = room['shared_cps'] * 0.1
                room['shared_cookies'] += cookies_earned
                room['shared_total'] += cookies_earned

def broadcast_updates():
    """Sendet regelmäßige Updates an alle Spieler"""
    while True:
        socketio.sleep(1)  # Jede Sekunde
        
        # Update für alle Räume
        for room_id, room in list(rooms.items()):
            socketio.emit('game_update', {
                'room_state': get_room_state(room_id)
            }, room=room_id)
        
        # Update für Solo-Spieler
        for player_id, player in list(players.items()):
            if not player.get('room_id'):
                socketio.emit('game_update', {
                    'player': get_player_state(player)
                }, room=player_id)

# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    # Starte Hintergrund-Tasks
    socketio.start_background_task(auto_cookie_generator)
    socketio.start_background_task(broadcast_updates)
    
    print("🍪 Cookie Clicker Server startet...")
    print("🌐 Öffne http://localhost:5000 im Browser")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
