import re

with open("shop_agent.py", "r") as f:
    code = f.read()

old_hwid_func = """import platform
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

new_hwid_func = """import platform
import hashlib

# Military-Grade Hardware ID (Cross-Platform Silicon Tracking)
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
            # 1. Primary Windows Approach: Native Registry Cryptography Key (Fastest, zero-crash)
            try:
                import winreg
                registry = winreg.HKEY_LOCAL_MACHINE
                address = r"SOFTWARE\\Microsoft\\Cryptography"
                # KEY_WOW64_64KEY ensures we don't get redirected on 64-bit systems
                key = winreg.OpenKey(registry, address, 0, winreg.KEY_READ | 0x0100) 
                hw_string, _ = winreg.QueryValueEx(key, "MachineGuid")
                winreg.CloseKey(key)
            except Exception as e:
                pass
            
            # 2. Fallback: WMIC Motherboard UUID (Supresses command prompt window popup)
            if not hw_string:
                CREATE_NO_WINDOW = 0x08000000
                result = subprocess.run(['wmic', 'csproduct', 'get', 'uuid'], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
                lines = [l.strip() for l in result.stdout.split('\\n') if l.strip()]
                if len(lines) > 1:
                    hw_string = lines[1]
                    
        elif system == "Linux":
            with open('/etc/machine-id', 'r') as f:
                hw_string = f.read().strip()
    except Exception:
        pass
        
    # Catch empty strings or cheap motherboards with dummy UUIDs
    if not hw_string or hw_string == "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF":
        hw_string = str(uuid.getnode())
        
    # Cryptographic Salt to prevent hash reversing
    salt = "PRINTHUB_ENCLAVE_v1_"
    salted_string = salt + hw_string
    return hashlib.sha256(salted_string.encode()).hexdigest()[:16].upper()"""

if old_hwid_func in code:
    code = code.replace(old_hwid_func, new_hwid_func)
    with open("shop_agent.py", "w") as f:
        f.write(code)
    print("Windows Military-Grade HWID applied.")
else:
    print("Could not find old HWID function.")
