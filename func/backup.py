import os
import zipfile
import time


def backup_server(uid):
    source_dir = os.path.join("servers", uid)
    if not os.path.exists(source_dir):
        return False, f"伺服器資料夾不存在: {source_dir}"

    timestamp = time.strftime('%Y%m%d_%H%M%S')
    backup_folder = os.path.join("backup", uid)

    os.makedirs(backup_folder, exist_ok=True)

    backup_filename = f"{uid}_{timestamp}.zip"
    backup_path = os.path.join(backup_folder, backup_filename)

    try:
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    filepath = os.path.join(root, file)
                    arcname = os.path.relpath(filepath, start=source_dir)
                    zipf.write(filepath, arcname)
        return True, backup_filename
    except Exception as e:
        return False, str(e)