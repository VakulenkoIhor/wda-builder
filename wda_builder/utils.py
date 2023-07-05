import subprocess
import hashlib
import re

def md5(data: str) -> str:
    return hashlib.md5(data.encode()).hexdigest()

def get_current_xcode_version() -> str|None:
    try:
        result = subprocess.run(['xcodebuild -version'], capture_output=True, text=True, check=True, shell=True)
        matches = re.match(r"^Xcode ([0-9]+.[0-9]+(.[0-9]+)?)", result.stdout)
        if matches == None: return None
        return matches.group(1)
    except:
        return None