const socket = io();
const segments = window.location.pathname.split('/');
const currentUid = segments.pop() || segments.pop();

socket.emit('join', { uid: currentUid });

socket.on('console_output', (msg) => {
    if(msg.uid === currentUid){
        addConsoleMessage(msg.data, 'info');
    }
});

socket.on('server_status', (msg) => {
    const statusEl = document.getElementById('serverStatus');
    if (msg.status === 'started') {
        statusEl.textContent = '🟢 伺服器運行中';
        statusEl.className = 'status-badge status-online';
    } else if (msg.status === 'stopped') {
        statusEl.textContent = '🔴 伺服器已停止';
        statusEl.className = 'status-badge status-offline';
    }
});

socket.on('system_usage', data => {
    document.getElementById('cpuUsage').textContent = data.cpu + '%';
    document.getElementById('memoryUsage').textContent = data.memory + '%';
    document.getElementById('storageUsage').textContent = data.storage + '%';

    // 如果你有進度條要同步更新，也可以加上：
    document.querySelector('.progress-fill.progress-cpu').style.width = data.cpu + '%';
    document.querySelector('.progress-fill.progress-memory').style.width = data.memory + '%';
    document.querySelector('.progress-fill.progress-storage').style.width = data.storage + '%';
});

window.addEventListener('DOMContentLoaded', () => {
    const segments = window.location.pathname.split('/');
    const uid = segments.pop() || segments.pop();

    fetch(`/get_logs/${uid}`)
        .then(res => res.json())
        .then(logs => {
            logs.forEach(line => {
                addConsoleMessage(line, 'info');
            });
        });
    fetch(`/get_system_logs/${uid}`)
    .then(res => res.json())
    .then(logs => {
        const logContainer = document.getElementById('systemLogs');
        logs.forEach(log => {
        const logEntry = document.createElement('div');
        logEntry.classList.add('log-entry');

        const timeSpan = document.createElement('span');
        timeSpan.classList.add('log-time');
        timeSpan.textContent = log.time || '';

        const levelSpan = document.createElement('span');
        levelSpan.classList.add('log-level');

        switch ((log.mark || '').toLowerCase()) {
            case 'info':
            levelSpan.classList.add('log-info');
            levelSpan.textContent = 'INFO';
            break;
            case 'warn':
            levelSpan.classList.add('log-warn');
            levelSpan.textContent = 'WARN';
            break;
            case 'error':
            levelSpan.classList.add('log-error');
            levelSpan.textContent = 'ERROR';
            break;
            default:
            levelSpan.textContent = log.mark || '';
        }

        const contentSpan = document.createElement('span');
        contentSpan.textContent = log.content || '';

        logEntry.appendChild(timeSpan);
        logEntry.appendChild(levelSpan);
        logEntry.appendChild(contentSpan);

        logContainer.appendChild(logEntry);
        });
    });
});

function logSystemEvent(uid, mark, content) {
    fetch('/log_system_event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ uid, mark, content })
    }).then(res => {
        if (res.ok) {
            const logContainer = document.getElementById('systemLogs');

            const logEntry = document.createElement('div');
            logEntry.classList.add('log-entry');

            const timeSpan = document.createElement('span');
            timeSpan.classList.add('log-time');
            timeSpan.textContent = new Date().toLocaleTimeString();

            const levelSpan = document.createElement('span');
            levelSpan.classList.add('log-level');

            switch (mark.toLowerCase()) {
                case 'info':
                    levelSpan.classList.add('log-info');
                    levelSpan.textContent = 'INFO';
                    break;
                case 'warn':
                    levelSpan.classList.add('log-warn');
                    levelSpan.textContent = 'WARN';
                    break;
                case 'error':
                    levelSpan.classList.add('log-error');
                    levelSpan.textContent = 'ERROR';
                    break;
                default:
                    levelSpan.textContent = mark;
            }

            const contentSpan = document.createElement('span');
            contentSpan.textContent = content;

            logEntry.appendChild(timeSpan);
            logEntry.appendChild(levelSpan);
            logEntry.appendChild(contentSpan);
            logContainer.appendChild(logEntry);
        }
    });
}

function startServer() {
    const segments = window.location.pathname.split('/');
    const uid = segments.pop() || segments.pop();
    document.getElementById('serverStatus').textContent = '🟢 伺服器運行中';
    document.getElementById('serverStatus').className = 'status-badge status-online';
    socket.emit('start_server', uid);
    addConsoleMessage('[System]: Server marked as starting...', 'info');
    logSystemEvent(uid, 'info', '伺服器啟動！');
}

function stopServer() {
    const segments = window.location.pathname.split('/');
    const uid = segments.pop() || segments.pop();
    document.getElementById('serverStatus').textContent = '🔴 伺服器已停止';
    document.getElementById('serverStatus').className = 'status-badge status-offline';
    socket.emit('stop_server', uid);
    addConsoleMessage('[System]: Server marked as stopping...', 'info');
    logSystemEvent(uid, 'info', '伺服器關閉！');
}

function emergencyStop() {
    const segments = window.location.pathname.split('/');
    const uid = segments.pop() || segments.pop();
    Swal.fire({
        title: '緊急停止',
        text: '緊急停止將立即終止伺服器，可能造成數據丟失。確定繼續嗎？',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: '確定',
        cancelButtonText: '取消',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            document.getElementById('serverStatus').textContent = '🔴 伺服器已停止';
            document.getElementById('serverStatus').className = 'status-badge status-offline';
            socket.emit('kill_server', uid);
            addConsoleMessage('[System]: Server marked as killing...', 'info');
            logSystemEvent(uid, 'warn', '伺服器強制關閉！');
        }
    });
}

function restartServer() {
    const segments = window.location.pathname.split('/');
    const uid = segments.pop() || segments.pop();
    document.getElementById('serverStatus').textContent = '🟡 伺服器重啟中';
    socket.emit('restart_server', uid);
    addConsoleMessage('[System]: Server marked as restarting...', 'info');

    document.getElementById('serverStatus').textContent = '🟢 伺服器運行中';
    document.getElementById('serverStatus').className = 'status-badge status-online';
    addConsoleMessage('[System]: Server marked as starting...', 'info');
    logSystemEvent(uid, 'info', '伺服器重新啟動！');
}

socket.on('player_update', (data) => {
    const playerListEl = document.querySelector('.player-list');
    const playerCountEl = document.getElementById('playerCount');

    playerListEl.innerHTML = '';

    data.players.forEach(player => {
        const div = document.createElement('div');
        div.className = 'player-item';
        div.innerHTML = `<div class="player-info"><div class="player-name">${player.name}</div></div>`;
        playerListEl.appendChild(div);
    });

    playerCountEl.textContent = data.count;
});

document.getElementById("copy-ip")?.addEventListener("click", function () {
    const serverIp = document.getElementById('copy-ip')?.dataset.ip || '';
    const serverPort = document.getElementById('copy-ip')?.dataset.port || '';
    const fallbackIp = document.getElementById('copy-ip')?.dataset.fallback || '';

    const text = (serverIp.trim() === "") ? `${fallbackIp}:${serverPort}` : `${serverIp}:${serverPort}`;

    navigator.clipboard.writeText(text);
});

document.querySelectorAll('.java-option').forEach(button => {
  button.addEventListener('click', () => {
    document.querySelectorAll('.java-option').forEach(btn => btn.classList.remove('active'));
    button.classList.add('active');

    const version = button.getAttribute('data-version');
    const uid = window.location.pathname.split('/').pop() || window.location.pathname.split('/').slice(-2, -1)[0];
    
    fetch('/set_java_version', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ uid, java_version: version })
    }).then(res => {
      if (!res.ok) {
        Swal.fire('錯誤', 'Java 版本設定失敗！', 'error');
      }
    });
  });
});

function addConsoleMessage(message, type = 'log') {
    const output = document.getElementById('consoleOutput');
    const timestamp = new Date().toLocaleTimeString();
    const div = document.createElement('div');
    div.className = `console-${type}`;
    div.innerHTML = `[${timestamp}] ${message}`;
    output.appendChild(div);
    output.scrollTop = output.scrollHeight;
}

function backupServer() {
    addConsoleMessage('[Server thread/INFO]: Creating backup...', 'info');
    addConsoleMessage('[Server thread/INFO]: Backup created successfully!', 'info');
}

function handleCommand(event) {
    if (event.key === 'Enter') {
        sendCommand();
    }
}

function sendCommand() {
    const input = document.getElementById('commandInput');
    const command = input.value.trim();

    const segments = window.location.pathname.split('/');
    const uid = segments.pop() || segments.pop();

    if (command) {
        socket.emit('send_command', { command, uid });
        addConsoleMessage(`[Server thread/INFO]: Executed command: ${command}`, 'command');
        input.value = '';
    }
}