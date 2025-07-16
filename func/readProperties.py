import os
import json

def read_server_properties(file_path):
    properties = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line == '' or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                properties[key.strip()] = value.strip()
    return properties

def read_ops_json(file_path):
    if not os.path.exists(file_path):
        return []

    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            return data
        except json.JSONDecodeError:
            return []
