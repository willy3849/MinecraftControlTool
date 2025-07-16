import uuid
from mcstatus import JavaServer

def is_valid_uuid(u):
    try:
        uuid.UUID(u)
        return True
    except:
        return False

def is_minecraft_running(ip, port):
    server = JavaServer.lookup(f"{ip}:{port}")
    try:
        status = server.status()
        return True
    except Exception:
        return False
