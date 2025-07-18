from flask import Flask, request, jsonify, render_template, Blueprint, abort
import os
from func.readProperties import read_server_properties, read_ops_json
from func.java import find_all_java_versions
from func.backup import backup_server
import socket
import json
import platform
import psutil

app = Blueprint('server', __name__)
uname = platform.uname()
cpu = psutil.cpu_freq()
mem = psutil.virtual_memory()
swap = psutil.swap_memory()

def get_size(bytes, suffix="B"):
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

@app.route('/server/<UID>')
def server(UID):
    prop_path = os.path.join('./servers', UID, 'server.properties')
    ops_path = os.path.join('./servers', UID, 'ops.json')
    with open("./lib/config.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    if UID not in data.get("ServerList", []):
        return render_template("404.html"), 404

    if not os.path.exists(prop_path):
        return render_template("404.html"), 404

    props = read_server_properties(prop_path)
    ops = read_ops_json(ops_path)
    systemInfo = {
        "cpuName": uname.processor,
        "maxFrequency": f"{cpu.max:.2f} MHz" if cpu else "未知",
        "minFrequency": f"{cpu.min:.2f} MHz" if cpu else "未知",
        "memTotal": get_size(mem.total),
        "storageTotal": get_size(swap.total)
    }
    ip = socket.gethostbyname(socket.gethostname())
    return render_template(
        'server.html',
        uid=UID,
        info=props,
        ops=ops,
        ip=ip,
        systemInfo=systemInfo
    )

@app.route('/api/java_versions')
def java_versions():
    results = find_all_java_versions()
    return jsonify([{'path': p, 'version': v} for p, v in results])

@app.route('/backup/<uid>')
def backup_route(uid):
    success, result = backup_server(uid)
    if success:
        return jsonify({"status": "success", "backup_file": result})
    else:
        return jsonify({"status": "error", "message": result}), 500