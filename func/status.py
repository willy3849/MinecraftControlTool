import socket
import struct

def query_server(host='localhost', port=25565):
    # 创建 UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)

    try:
        # 1. 发送握手包（会话ID随机生成）
        session_id = 12345  # 随机数
        handshake = struct.pack('>B', 0xFE) + struct.pack('>B', 0xFD) + struct.pack('>B', 0x09) + struct.pack('>I', session_id) + struct.pack('>B', 0x00)
        sock.sendto(handshake, (host, port))

        # 2. 接收握手响应（获取新的会话ID）
        response = sock.recv(1024)
        new_session_id = struct.unpack('>I', response[5:9])[0]

        # 3. 发送完整查询请求
        query_pkg = struct.pack('>B', 0xFE) + struct.pack('>B', 0xFD) + struct.pack('>B', 0x00) + struct.pack('>I', new_session_id) + struct.pack('>B', 0x00)
        sock.sendto(query_pkg, (host, port))

        # 4. 解析响应（复杂格式）
        data = sock.recv(4096)
        result = {}

        # 提取基础信息（分割\x00字节）
        base_data = data.split(b'\x00\x01player_\x00\x00')[0]
        items = base_data.split(b'\x00')
        
        for i in range(0, len(items)-1, 2):
            key = items[i].decode('utf-8', errors='ignore')
            result[key] = items[i+1].decode('utf-8', errors='ignore')

        # 提取玩家列表（如果有）
        if b'player_' in data:
            players_section = data.split(b'\x00\x01player_\x00\x00')[1]
            result['players'] = players_section[:-1].decode('utf-8').split('\x00')

        return result

    except Exception as e:
        print(f"Query 失败: {e}")
        return None
    finally:
        sock.close()

# 使用示例
data = query_server
print(data)
