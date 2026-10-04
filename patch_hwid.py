import re

with open("shop_agent.py", "r") as f:
    code = f.read()

old_hwid_func = """# Cryptographic Hardware ID (Motherboard/MAC hash)
def get_hwid():
    return str(uuid.getnode())"""

new_hwid_func = """import platform
import hashlib

# Enterprise Hardware ID (Deep OS-level Silicon tracking)
def get_hwid():
    system = platform.system()
    hw_string = ""
    try:
        if system == "Darwin": # macOS
            result = subprocess.run(['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice'], capture_output=True, text=True)
            for line in result.stdout.split('\\n'):
                if 'IOPlatformUUID' in line:
                    hw_string = line.split('=')[1].strip().strip('"')
                    break
        elif system == "Windows":
            result = subprocess.run(['wmic', 'csproduct', 'get', 'uuid'], capture_output=True, text=True)
            hw_string = result.stdout.split('\\n')[1].strip()
        elif system == "Linux":
            with open('/etc/machine-id', 'r') as f:
                hw_string = f.read().strip()
    except Exception:
        pass
        
    if not hw_string:
        hw_string = str(uuid.getnode())
        
    return hashlib.sha256(hw_string.encode()).hexdigest()[:16]"""

if old_hwid_func in code:
    code = code.replace(old_hwid_func, new_hwid_func)
else:
    print("Could not find old HWID function.")

with open("shop_agent.py", "w") as f:
    f.write(code)
print("HWID Engine patched to use OS-level Motherboard UUID.")
