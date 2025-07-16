import subprocess
import sys
import urllib.request
import requests
import time
from flask import Flask, request, jsonify
from flask import render_template
from func.loadConfig import WEB_PORT
import json
from flask_socketio import SocketIO, emit, join_room
import threading
import os
import platform
import psutil

MINECRAFT_JAR = "server.jar"

app = Flask(__name__)
socketio = SocketIO(app)
uname = platform.uname()

minecraft_processes={}
console_logs = {}

def start_minecraft_server(uid):
    jar_path = os.path.abspath(os.path.join("servers", uid))
    if uid not in console_logs:
        console_logs[uid] = []
    proc = subprocess.Popen(['java', '-jar', "server.jar", 'nogui'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, cwd=jar_path)
    minecraft_processes[uid] = proc
    for line in proc.stdout:
        console_logs[uid].append(line.strip())
        socketio.emit('console_output', {'uid': uid, 'data': line.strip()}, room=uid)


def push_player_update(uid, players):
    players_data = [{'name': p.name} for p in players]
    socketio.emit('player_update', {'players': players_data, 'count': len(players)}, room=uid)

def emit_system_usage():
    while True:
        cpu_percent = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
        partitions = psutil.disk_partitions()
        for partition in partitions:
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
            except PermissionError:
                continue
        partition_usage_percent = partition_usage.percent

        data = {
            'cpu': cpu_percent,
            'memory': mem_percent,
            'storage': partition_usage_percent
        }
        socketio.emit('system_usage', data)
        time.sleep(1)

views_dir = os.path.join(os.path.dirname(__file__), 'views')
for filename in os.listdir(views_dir):
    if filename.endswith('.py') and filename != '__init__.py':
        module_name = filename[:-3]
        module = __import__(f'views.{module_name}', fromlist=['*'])
        print(f"  L {module_name}.py")
        if hasattr(module, 'app'):
            app.register_blueprint(module.app)

@app.errorhandler(404)
async def error_404(error):
    return render_template('404.html'), 404

@app.route('/get_logs/<uid>')
def get_logs(uid):
    return jsonify(console_logs.get(uid, []))

@app.route('/get_system_log/<uid>')
def get_system_log(uid):
    with open("lib/config.json", "r", encoding="utf-8") as file:
        data = json.load(file)
    logs = data.get("ServerSystemLog", {}).get(uid, [])
    latest_logs = logs[-5:]
    return jsonify(latest_logs)

@socketio.on('join')
def on_join(data):
    uid = data.get('uid')
    if uid:
        join_room(uid)
        emit('console_output', {'data': f'Joined room {uid}'})

@app.route('/log_system_event', methods=['POST'])
def log_system_event():
    data = request.get_json()
    uid = data.get('uid')
    mark = data.get('mark', 'info')
    content = data.get('content', '')

    with open("lib/config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    log_entry = {
        "time": time.strftime('%H:%M:%S'),
        "mark": mark,
        "content": content
    }

    if uid not in config.get("ServerSystemLog", {}):
        config["ServerSystemLog"][uid]=[]

    config["ServerSystemLog"][uid].append(log_entry)

    with open("lib/config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

    return jsonify({"status": "success"})

@app.route('/set_java_version', methods=['POST'])
def set_java_version():
    data = request.json
    uid = data.get('uid')
    version = data.get('java_version')

    if not uid or not version:
        return jsonify({'error': 'Missing uid or java_version'}), 400

    path = f'./servers/{uid}/java_version.json'
    with open(path, 'w') as f:
        json.dump({'java_version': version}, f)

    return jsonify({'message': 'Java version set successfully'})


@socketio.on('start_server')
def on_start_server(uid):
    try:
        with open("lib/config.json", "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}

    if "ServerSystemLog" not in data or not isinstance(data["ServerSystemLog"], dict):
        data["ServerSystemLog"] = {}

    if uid not in data["ServerSystemLog"]:
        data["ServerSystemLog"][uid] = []

    startLog = {
        "time": time.strftime('%H:%M:%S'),
        "mark": "info",
        "content": "伺服器啟動!"
    }
    data["ServerSystemLog"][uid].append(startLog)

    with open("lib/config.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    thread = threading.Thread(target=start_minecraft_server, args=(uid,))
    thread.start()

    emit('server_status', {'status': 'started'})


@socketio.on('stop_server')
def on_stop_server(uid):
    try:
        with open("lib/config.json", "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}

    if "ServerSystemLog" not in data or not isinstance(data["ServerSystemLog"], dict):
        data["ServerSystemLog"] = {}

    if uid not in data["ServerSystemLog"]:
        data["ServerSystemLog"][uid] = []

    startLog = {
        "time": time.strftime('%H:%M:%S'),
        "mark": "info",
        "content": "伺服器關閉!"
    }
    data["ServerSystemLog"][uid].append(startLog)

    with open("lib/config.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    proc = minecraft_processes.get(uid)
    if proc and proc.poll() is None:
        proc.stdin.write('stop\n')
        proc.stdin.flush()
        del minecraft_processes[uid]
        emit('server_status', {'status': 'stopping'})
    else:
        emit('server_status', {'status': 'not_running'})

@socketio.on('kill_server')
def on_kill_server(uid):
    try:
        with open("lib/config.json", "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}

    if "ServerSystemLog" not in data or not isinstance(data["ServerSystemLog"], dict):
        data["ServerSystemLog"] = {}

    if uid not in data["ServerSystemLog"]:
        data["ServerSystemLog"][uid] = []

    startLog = {
        "time": time.strftime('%H:%M:%S'),
        "mark": "warn",
        "content": "伺服器強制關閉!"
    }
    data["ServerSystemLog"][uid].append(startLog)

    with open("lib/config.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    proc = minecraft_processes.get(uid)
    if proc and proc.poll() is None:
        proc.terminate()
        proc.wait()
        del minecraft_processes[uid]
        emit('server_status', {'status': 'force_stopped'})
    else:
        emit('server_status', {'status': 'not_running'})

@socketio.on('restart_server')
def on_restart_server(uid):
    try:
        with open("lib/config.json", "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}

    if "ServerSystemLog" not in data or not isinstance(data["ServerSystemLog"], dict):
        data["ServerSystemLog"] = {}

    if uid not in data["ServerSystemLog"]:
        data["ServerSystemLog"][uid] = []

    startLog = {
        "time": time.strftime('%H:%M:%S'),
        "mark": "info",
        "content": "伺服器重新啟動!"
    }
    data["ServerSystemLog"][uid].append(startLog)

    with open("lib/config.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    proc = minecraft_processes.get(uid)

    def restart():
        proc.wait()
        minecraft_processes.pop(uid, None)
        start_minecraft_server(uid)
        socketio.emit('server_status', {'status': 'restarted'}, room=uid)

    if proc and proc.poll() is None:
        proc.stdin.write('stop\n')
        proc.stdin.flush()
        socketio.emit('server_status', {'status': 'restarting'}, room=uid)
        threading.Thread(target=restart).start()
    else:
        threading.Thread(target=start_minecraft_server, args=(uid,)).start()
        socketio.emit('server_status', {'status': 'started'}, room=uid)


@socketio.on('send_command')
def on_send_command(data):
    cmd = data.get('command')
    uid = data.get('uid')

    if uid and uid in minecraft_processes:
        proc = minecraft_processes[uid]
        if proc.poll() is None:
            proc.stdin.write(cmd + '\n')
            proc.stdin.flush()

    socketio.emit('console_output', {'uid': uid, 'data': f'Executed command: {cmd}'}, room=uid)

if __name__ == '__main__':
    threading.Thread(target=emit_system_usage, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=WEB_PORT, debug=False)