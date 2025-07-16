from flask import Flask, request, jsonify, render_template, Blueprint
import os
from func.readProperties import read_server_properties
from func.verify import is_valid_uuid
import uuid
import json

app = Blueprint('index', __name__)

@app.route("/")
def index():
    folder_path = './servers'
    server_infos = []
    with open("./lib/config.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    server_list = data.get("ServerList", [])
    folders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
    for folder in folders:
        if not is_valid_uuid(folder):
            uid = str(uuid.uuid4())
            os.rename(os.path.join(folder_path, folder), os.path.join(folder_path, uid))
            server_list.append(uid)
            with open("./lib/config.json", "w", encoding="utf-8") as f:
                data["ServerList"] = server_list
                json.dump(data, f, indent=4, ensure_ascii=False)
        elif folder not in server_list:
            server_list.append(folder)
            with open("./lib/config.json", "w", encoding="utf-8") as f:
                data["ServerList"] = server_list
                json.dump(data, f, indent=4, ensure_ascii=False)
        else:
            uid = folder
        prop_path = os.path.join(folder_path, uid, 'server.properties')
        if os.path.exists(prop_path):
            props = read_server_properties(prop_path)
            motd = props.get('motd', '未知名稱')
        else:
            motd = '找不到 server.properties'

        server_infos.append({
            'folder': uid,
            'motd': motd
        })
    return render_template('index.html', servers=server_infos)