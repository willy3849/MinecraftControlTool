import shutil
import subprocess
import os
import re

def find_all_java_versions():
    java_paths = set()
    for path_dir in os.environ.get("PATH", "").split(os.pathsep):
        java_exe = os.path.join(path_dir, "java")
        if os.path.isfile(java_exe) and os.access(java_exe, os.X_OK):
            java_paths.add(java_exe)

    java_versions = []
    version_regex = re.compile(r'version\s+"([\d._]+)"')

    for path in java_paths:
        try:
            version_output = subprocess.check_output([path, '-version'], stderr=subprocess.STDOUT)
            version_text = version_output.decode('utf-8').strip()
            match = version_regex.search(version_text)
            if match:
                simple_version = match.group(1)
            else:
                simple_version = "未知版本"
            java_versions.append({
                "path": path,
                "version": f"Java {simple_version}"
            })
        except Exception as e:
            java_versions.append({"path": path, "version": f"錯誤: {e}"})

    return java_versions

