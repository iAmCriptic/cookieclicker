/**
 * Cookie Clicker Multiplayer - Game Client
 * =========================================
 */

// =============================================================================
// GLOBAL STATE
// =============================================================================

const socket = io();

let gameState = {
    player: null,
    roomId: null,
    roomMode: null,
    opponent: null,
    isInRoom: false,
    currentTab: 'click',
    stealCooldown: 0
};

// =============================================================================
// DOM ELEMENTS
// =============================================================================

const elements = {
    // Screens
    startScreen: document.getElementById('start-screen'),
    gameScreen: document.getElementById('game-screen'),
    
    // Start Screen
    playerNameInput: document.getElementById('player-name'),
    btnStartSolo: document.getElementById('btn-start-solo'),
    btnCreateVersus: document.getElementById('btn-create-versus'),
    btnCreateCoop: document.getElementById('btn-create-coop'),
    roomCodeInput: document.getElementById('room-code'),
    btnJoinRoom: document.getElementById('btn-join-room'),
    
    // Game Screen
    playerDisplayName: document.getElementById('player-display-name'),
    roomInfo: document.getElementById('room-info'),
    btnLeaveRoom: document.getElementById('btn-leave-room'),
    
    // Cookie Area
    cookieCount: document.getElementById('cookie-count'),
    cps: document.getElementById('cps'),
    clickPower: document.getElementById('click-power'),
    cookieBtn: document.getElementById('cookie-btn'),
    clickParticles: document.getElementById('click-particles'),
    totalCount: document.getElementById('total-count'),
    
    // Opponent Area
    opponentArea: document.getElementById('opponent-area'),
    opponentName: document.getElementById('opponent-name'),
    opponentCookies: document.getElementById('opponent-cookies'),
    opponentCps: document.getElementById('opponent-cps'),
    btnSteal: document.getElementById('btn-steal'),
    stealCooldown: document.getElementById('steal-cooldown'),
    cooldownTime: document.getElementById('cooldown-time'),
    
    // Coop Area
    coopArea: document.getElementById('coop-area'),
    coopPartnerName: document.getElementById('coop-partner-name'),
    
    // Upgrades
    upgradesContainer: document.getElementById('upgrades-container'),
    tabButtons: document.querySelectorAll('.tab-btn'),
    
    // Notifications
    notifications: document.getElementById('notifications')
};

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

function formatNumber(num) {
    if (num >= 1e12) return (num / 1e12).toFixed(2) + 'T';
    if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K';
    return Math.floor(num).toString();
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    elements.notifications.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    document.getElementById(screenId).classList.add('active');
}

function createClickParticle(amount) {
    const particle = document.createElement('div');
    particle.className = 'click-particle';
    particle.textContent = '+' + formatNumber(amount);
    
    // Zufällige Position um den Cookie herum
    const angle = Math.random() * Math.PI * 2;
    const distance = 50 + Math.random() * 50;
    const x = 100 + Math.cos(angle) * distance;
    const y = 100 + Math.sin(angle) * distance;
    
    particle.style.left = x + 'px';
    particle.style.top = y + 'px';
    
    elements.clickParticles.appendChild(particle);
    
    setTimeout(() => {
        particle.remove();
    }, 1000);
}

// =============================================================================
// UI UPDATE FUNCTIONS
// =============================================================================

function updatePlayerUI(player) {
    if (!player) return;
    
    elements.cookieCount.textContent = formatNumber(player.cookies);
    elements.cps.textContent = formatNumber(player.cookies_per_second);
    elements.clickPower.textContent = formatNumber(player.click_power);
    elements.totalCount.textContent = formatNumber(player.total_cookies);
    
    gameState.player = player;
    renderUpgrades();
}

function updateRoomUI(roomState) {
    if (!roomState) return;
    
    gameState.roomId = roomState.room_id;
    gameState.roomMode = roomState.mode;
    
    elements.roomInfo.textContent = `${roomState.mode === 'coop' ? '🤝 Coop' : '⚔️ Versus'} | ${roomState.room_id}`;
    elements.roomInfo.classList.remove('hidden');
    elements.btnLeaveRoom.classList.remove('hidden');
    
    if (roomState.mode === 'coop') {
        // Coop Mode: Gemeinsame Cookies
        elements.cookieCount.textContent = formatNumber(roomState.shared_cookies);
        elements.cps.textContent = formatNumber(roomState.shared_cps);
        elements.clickPower.textContent = formatNumber(roomState.shared_click_power);
        elements.totalCount.textContent = formatNumber(roomState.shared_total);
        
        elements.opponentArea.classList.add('hidden');
        elements.coopArea.classList.remove('hidden');
        
        // Partner anzeigen
        const partner = roomState.players.find(p => p.id !== socket.id);
        if (partner) {
            elements.coopPartnerName.textContent = partner.name;
        } else {
            elements.coopPartnerName.textContent = 'Warte auf Partner...';
        }
        
        // Speichere Coop-State für Upgrades
        gameState.player = {
            cookies: roomState.shared_cookies,
            upgrades: roomState.shared_upgrades,
            click_power: roomState.shared_click_power,
            cookies_per_second: roomState.shared_cps
        };
        
        // Berechne Upgrade-Kosten für Coop
        gameState.player.upgrade_costs = {};
        for (const [id, data] of Object.entries(UPGRADES_DATA)) {
            const owned = roomState.shared_upgrades[id] || 0;
            gameState.player.upgrade_costs[id] = Math.floor(data.base_cost * Math.pow(data.cost_multiplier, owned));
        }
        
    } else {
        // Versus Mode
        elements.coopArea.classList.add('hidden');
        elements.opponentArea.classList.remove('hidden');
        
        // Eigene Stats
        const myPlayer = roomState.players.find(p => p.id === socket.id);
        if (myPlayer) {
            updatePlayerUI(myPlayer);
        }
        
        // Gegner-Stats
        const opponent = roomState.players.find(p => p.id !== socket.id);
        if (opponent) {
            gameState.opponent = opponent;
            elements.opponentName.textContent = opponent.name;
            elements.opponentCookies.textContent = formatNumber(opponent.cookies);
            elements.opponentCps.textContent = formatNumber(opponent.cookies_per_second);
            elements.btnSteal.classList.remove('hidden');
            elements.btnSteal.dataset.targetId = opponent.id;
        } else {
            elements.opponentName.textContent = 'Warte auf Gegner...';
            elements.opponentCookies.textContent = '0';
            elements.opponentCps.textContent = '0';
            elements.btnSteal.classList.add('hidden');
        }
    }
    
    renderUpgrades();
}

function renderUpgrades() {
    if (!gameState.player) return;
    
    elements.upgradesContainer.innerHTML = '';
    
    const filterType = gameState.currentTab === 'click' ? 'click' : 'auto';
    
    for (const [id, data] of Object.entries(UPGRADES_DATA)) {
        if (data.type !== filterType) continue;
        
        const owned = gameState.player.upgrades[id] || 0;
        const cost = gameState.player.upgrade_costs ? gameState.player.upgrade_costs[id] : 
                     Math.floor(data.base_cost * Math.pow(data.cost_multiplier, owned));
        const canAfford = gameState.player.cookies >= cost;
        
        const card = document.createElement('div');
        card.className = `upgrade-card ${canAfford ? 'affordable' : 'disabled'}`;
        card.dataset.upgradeId = id;
        
        card.innerHTML = `
            <div class="upgrade-icon">${data.icon}</div>
            <div class="upgrade-info">
                <div class="upgrade-name">${data.name}</div>
                <div class="upgrade-desc">${data.description}</div>
                <div class="upgrade-owned">Besitzt: ${owned}</div>
            </div>
            <div class="upgrade-cost">
                <div class="cost-value">${formatNumber(cost)}</div>
                <div class="cost-label">🍪</div>
            </div>
        `;
        
        card.addEventListener('click', () => {
            if (canAfford) {
                buyUpgrade(id);
            }
        });
        
        elements.upgradesContainer.appendChild(card);
    }
}

// =============================================================================
// GAME ACTIONS
// =============================================================================

function clickCookie() {
    socket.emit('click_cookie');
    
    // Sofortiges visuelles Feedback
    const clickPower = gameState.player ? gameState.player.click_power : 1;
    createClickParticle(clickPower);
}

function buyUpgrade(upgradeId) {
    socket.emit('buy_upgrade', { upgrade_id: upgradeId });
}

function stealCookies() {
    if (!gameState.opponent) return;
    socket.emit('steal_cookies', { target_id: gameState.opponent.id });
}

function updateStealCooldown() {
    if (!gameState.player || !gameState.isInRoom || gameState.roomMode !== 'versus') return;
    
    const now = Date.now() / 1000;
    const lastSteal = gameState.player.last_steal || 0;
    const cooldownRemaining = Math.max(0, 30 - (now - lastSteal));
    
    if (cooldownRemaining > 0) {
        elements.btnSteal.classList.add('hidden');
        elements.stealCooldown.classList.remove('hidden');
        elements.cooldownTime.textContent = Math.ceil(cooldownRemaining);
    } else {
        elements.btnSteal.classList.remove('hidden');
        elements.stealCooldown.classList.add('hidden');
    }
}

// =============================================================================
// SOCKET EVENT HANDLERS
// =============================================================================

socket.on('connect', () => {
    console.log('Mit Server verbunden');
});

socket.on('disconnect', () => {
    console.log('Verbindung getrennt');
    showNotification('Verbindung zum Server verloren!', 'error');
});

socket.on('game_joined', (data) => {
    gameState.player = data.player;
    elements.playerDisplayName.textContent = data.player.name;
    showScreen('game-screen');
    updatePlayerUI(data.player);
    showNotification('Willkommen, ' + data.player.name + '!', 'success');
});

socket.on('room_created', (data) => {
    gameState.isInRoom = true;
    showNotification(`Raum ${data.room_id} erstellt! Teile diesen Code.`, 'success');
    updateRoomUI(data.room_state);
});

socket.on('room_joined', (data) => {
    gameState.isInRoom = true;
    showNotification('Raum beigetreten!', 'success');
    updateRoomUI(data.room_state);
});

socket.on('room_left', () => {
    gameState.isInRoom = false;
    gameState.roomId = null;
    gameState.roomMode = null;
    gameState.opponent = null;
    
    elements.roomInfo.classList.add('hidden');
    elements.btnLeaveRoom.classList.add('hidden');
    elements.opponentArea.classList.add('hidden');
    elements.coopArea.classList.add('hidden');
    
    showNotification('Raum verlassen', 'info');
});

socket.on('player_left', (data) => {
    showNotification(`${data.player_name} hat den Raum verlassen`, 'warning');
});

socket.on('game_update', (data) => {
    if (data.room_state) {
        updateRoomUI(data.room_state);
    } else if (data.player) {
        updatePlayerUI(data.player);
    }
});

socket.on('cookie_clicked', (data) => {
    if (data.room_state) {
        updateRoomUI(data.room_state);
    }
    
    // Zeige Klick-Info wenn anderer Spieler klickt
    if (data.player_id !== socket.id) {
        createClickParticle(data.cookies_earned);
    }
});

socket.on('upgrade_bought', (data) => {
    if (data.room_state) {
        updateRoomUI(data.room_state);
    }
    
    const upgrade = UPGRADES_DATA[data.upgrade_id];
    if (data.player_id === socket.id) {
        showNotification(`${upgrade.icon} ${upgrade.name} gekauft!`, 'success');
    } else {
        showNotification(`${data.player_name} kaufte ${upgrade.icon} ${upgrade.name}`, 'info');
    }
});

socket.on('cookies_stolen', (data) => {
    updateRoomUI(data.room_state);
    
    if (data.thief_id === socket.id) {
        showNotification(`🦹 Du hast ${formatNumber(data.amount)} Cookies von ${data.victim_name} gestohlen!`, 'success');
    } else {
        showNotification(`🦹 ${data.thief_name} hat dir ${formatNumber(data.amount)} Cookies gestohlen!`, 'error');
    }
});

socket.on('error', (data) => {
    showNotification(data.message, 'error');
});

// =============================================================================
// EVENT LISTENERS
// =============================================================================

// Start Screen
elements.btnStartSolo.addEventListener('click', () => {
    const name = elements.playerNameInput.value.trim() || 'Spieler';
    socket.emit('join_game', { name });
});

elements.btnCreateVersus.addEventListener('click', () => {
    const name = elements.playerNameInput.value.trim() || 'Spieler';
    socket.emit('join_game', { name });
    
    socket.once('game_joined', () => {
        socket.emit('create_room', { mode: 'versus' });
    });
});

elements.btnCreateCoop.addEventListener('click', () => {
    const name = elements.playerNameInput.value.trim() || 'Spieler';
    socket.emit('join_game', { name });
    
    socket.once('game_joined', () => {
        socket.emit('create_room', { mode: 'coop' });
    });
});

elements.btnJoinRoom.addEventListener('click', () => {
    const code = elements.roomCodeInput.value.trim().toUpperCase();
    if (!code) {
        showNotification('Bitte Raum-Code eingeben', 'error');
        return;
    }
    
    const name = elements.playerNameInput.value.trim() || 'Spieler';
    socket.emit('join_game', { name });
    
    socket.once('game_joined', () => {
        socket.emit('join_room', { room_id: code });
    });
});

// Enter key for inputs
elements.playerNameInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        elements.btnStartSolo.click();
    }
});

elements.roomCodeInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        elements.btnJoinRoom.click();
    }
});

// Game Screen
elements.cookieBtn.addEventListener('click', clickCookie);

elements.btnLeaveRoom.addEventListener('click', () => {
    socket.emit('leave_room');
});

elements.btnSteal.addEventListener('click', stealCookies);

// Tab switching
elements.tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        elements.tabButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        gameState.currentTab = btn.dataset.tab;
        renderUpgrades();
    });
});

// Keyboard shortcut for clicking
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && document.getElementById('game-screen').classList.contains('active')) {
        e.preventDefault();
        clickCookie();
    }
});

// =============================================================================
// GAME LOOP
// =============================================================================

setInterval(updateStealCooldown, 1000);

// =============================================================================
// INITIALIZE
// =============================================================================

console.log('🍪 Cookie Clicker Multiplayer geladen!');
