import os
import sys
import base64
import time
import subprocess
import json
import logging
import requests
import platform
import hashlib
import uuid
from getpass import getpass
from dotenv import load_dotenv
from supabase import create_client, Client
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

def get_hwid():
    system = platform.system()
    hw_string = ""
    try:
        if system == "Darwin":
            result = subprocess.run(['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'IOPlatformUUID' in line:
                    hw_string = line.split('=')[1].strip().strip('"')
                    break
        elif system == "Windows":
            try:
                import winreg
                registry = winreg.HKEY_LOCAL_MACHINE
                address = r"SOFTWARE\Microsoft\Cryptography"
                key = winreg.OpenKey(registry, address, 0, winreg.KEY_READ | 0x0100)
                hw_string, _ = winreg.QueryValueEx(key, "MachineGuid")
                winreg.CloseKey(key)
            except Exception:
                pass
            if not hw_string:
                CREATE_NO_WINDOW = 0x08000000
                result = subprocess.run(['wmic', 'csproduct', 'get', 'uuid'], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
                lines = [l.strip() for l in result.stdout.split('\n') if l.strip()]
                if len(lines) > 1:
                    hw_string = lines[1]
        elif system == "Linux":
            with open('/etc/machine-id', 'r') as f:
                hw_string = f.read().strip()
    except Exception:
        pass
        
    if not hw_string or hw_string == "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF":
        hw_string = str(uuid.getnode())
        
    salt = "PRINTHUB_ENCLAVE_v1_"
    return hashlib.sha256((salt + hw_string).encode()).hexdigest()[:16].upper()

HWID = get_hwid()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger('PrintBridge')

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://mzkizzakuporgzljealz.supabase.co")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im16a2l6emFrdXBvcmd6bGplYWx6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTEyNTY0MzQsImV4cCI6MjEwNjgzMjQzNH0.6s21aw_xhbaAJiNeT5x_qi3sZeDfi68yKflj-3M0Z-o")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

TEMP_DIR = "temp_print_spool"
CONFIG_FILE = "shop_config.json"
os.makedirs(TEMP_DIR, exist_ok=True)

def get_local_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading config: {e}")
    return {"printer_bw": "", "printer_color": ""}

def print_file(file_path, copies, color_mode, sides):
    system = platform.system()
    local_cfg = get_local_config()
    
    if system == "Windows":
        target_printer = local_cfg.get("printer_color") if color_mode == 'color' else local_cfg.get("printer_bw")
        try:
            original_default = None
            if target_printer:
                logger.info(f"Routing to specific Windows printer: {target_printer}")
                # Hack: Temporarily set the default printer because PrintTo verb is often unregistered for PDFs/JPGs
                try:
                    res = subprocess.run(['powershell', '-Command', '(Get-WmiObject -Query "SELECT * FROM Win32_Printer WHERE Default=$true").Name'], capture_output=True, text=True)
                    original_default = res.stdout.strip()
                    subprocess.run(['powershell', '-Command', f'(New-Object -ComObject WScript.Network).SetDefaultPrinter("{target_printer}")'], check=True)
                except Exception as e:
                    logger.error(f"Failed to swap default printer: {e}")
            else:
                logger.info(f"Using current default Windows printer for {file_path}")
            
            # The standard 'print' verb is highly reliable because it uses the OS default handler
            os.startfile(file_path, "print")
            time.sleep(10)  # Wait for the GUI print spooler to catch the job before swapping back
            
            # Restore original printer
            if target_printer and original_default and original_default != target_printer:
                subprocess.run(['powershell', '-Command', f'(New-Object -ComObject WScript.Network).SetDefaultPrinter("{original_default}")'])
                
            return True
        except Exception as e:
            logger.error(f"Windows print failed: {e}")
            return False
    else:
        # macOS / Linux
        cmd = ["lp", "-n", str(copies)]
        if color_mode == 'bw':
            cmd.extend(["-o", "ColorModel=Gray"])
            if local_cfg.get("printer_bw"):
                cmd.extend(["-d", local_cfg["printer_bw"]])
        else:
            if local_cfg.get("printer_color"):
                cmd.extend(["-d", local_cfg["printer_color"]])
                
        if sides == 'double':
            cmd.extend(["-o", "sides=two-sided-long-edge"])
        else:
            cmd.extend(["-o", "sides=one-sided"])
            
        cmd.append(file_path)
        logger.info(f"Running print command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Print failed: {result.stderr}")
            return False
        logger.info(f"Print successful: {result.stdout.strip()}")
        return True

def process_order(order):
    order_id = order['id']
    shop_id = order['shop_id']
    logger.info(f"Processing Order #{order_id[:8]}...")
    
    # 1. Update status to 'Printing...' to prevent double processing
    supabase.table('printhub_orders').update({'status': 'Printing...'}).eq('id', order_id).execute()
    
    # 2. Fetch associated files
    files_res = supabase.table('printhub_files').select('*').eq('order_id', order_id).execute()
    if not files_res.data:
        logger.warning(f"No files found for Order #{order_id[:8]}")
        supabase.table('printhub_orders').update({'status': 'Error: No Files'}).eq('id', order_id).execute()
        return

    all_printed = True
    for file_record in files_res.data:
        storage_path = file_record['storage_path']
        local_filename = os.path.join(TEMP_DIR, os.path.basename(storage_path))
        
        # Security: Prevent printing malware or unsupported types
        ext = os.path.splitext(local_filename)[1].lower()
        if ext not in ['.pdf', '.png', '.jpg', '.jpeg']:
            logger.error(f"Security Error: Unsupported file format {ext} for {storage_path}")
            all_printed = False
            continue

        # Download (Authenticated)
        logger.info(f"Downloading {storage_path}...")
        try:
            # We use the native supabase python client which uses the auth session
            file_bytes = supabase.storage.from_('print-files').download(storage_path)
            if len(file_bytes) > 50 * 1024 * 1024:
                logger.error(f"File {storage_path} exceeds 50MB limit. DoS blocked.")
                all_printed = False
                continue
            with open(local_filename, 'wb') as f:
                f.write(file_bytes)
        except Exception as e:
            logger.error(f"Network error downloading {storage_path}: {e}")
            all_printed = False
            continue

        # Print
        success = print_file(
            local_filename, 
            copies=file_record.get('copies', 1), 
            color_mode=file_record.get('color_mode', 'bw'), 
            sides=file_record.get('sides', 'single')
        )
        if not success:
            all_printed = False

        # Secure wipe (Zero-Trace Privacy)
        if os.path.exists(local_filename):
            try:
                os.remove(local_filename)
                logger.info(f"Securely deleted local payload: {local_filename}")
            except Exception as e:
                logger.error(f"Failed to delete {local_filename}: {e}")
                
    # 3. Update final status
    if all_printed:
        supabase.table('printhub_orders').update({'status': 'Printed'}).eq('id', order_id).execute()
        logger.info(f"Order #{order_id[:8]} completed successfully.")
    else:
        supabase.table('printhub_orders').update({'status': 'Print Failed'}).eq('id', order_id).execute()
        logger.error(f"Order #{order_id[:8]} encountered errors during printing.")


# ==========================================
# LOCAL CONFIGURATION SERVER (LOCALHOST:9090)
# ==========================================
def get_system_printers():
    system = platform.system()
    printers = []
    try:
        if system == "Windows":
            res = subprocess.run(['powershell', '-Command', 'Get-Printer | Select-Object -ExpandProperty Name'], capture_output=True, text=True)
            printers = [p.strip() for p in res.stdout.split('\n') if p.strip()]
        else:
            res = subprocess.run(['lpstat', '-a'], capture_output=True, text=True)
            printers = [line.split(' ')[0] for line in res.stdout.split('\n') if line.strip()]
    except Exception as e:
        logger.error(f"Failed to list printers: {e}")
    return printers

class ConfigHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            cfg = get_local_config()
            printers = get_system_printers()
            
            options_bw = "<option value=''>-- System Default --</option>"
            options_color = "<option value=''>-- System Default --</option>"
            
            for p in printers:
                sel_bw = "selected" if p == cfg.get('printer_bw') else ""
                sel_color = "selected" if p == cfg.get('printer_color') else ""
                options_bw += f"<option value='{p}' {sel_bw}>{p}</option>"
                options_color += f"<option value='{p}' {sel_color}>{p}</option>"

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>PrintHub Local Config</title>
                <style>
                    body {{ font-family: -apple-system, system-ui, sans-serif; background: #f8fafc; color: #0f172a; max-width: 600px; margin: 40px auto; padding: 20px; }}
                    .card {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }}
                    h1 {{ margin-top: 0; font-size: 24px; }}
                    label {{ display: block; font-weight: bold; margin-top: 20px; margin-bottom: 8px; font-size: 14px; color: #475569; }}
                    select {{ width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #cbd5e1; font-size: 16px; margin-bottom: 10px; }}
                    button {{ background: #10b981; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; margin-top: 20px; width: 100%; }}
                    button:hover {{ background: #059669; }}
                    .success {{ background: #dcfce7; color: #166534; padding: 10px; border-radius: 6px; margin-bottom: 20px; display: none; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>Hardware Configuration</h1>
                    <p style="color: #64748b; font-size: 14px;">Select the physical printers connected to this computer. This page is only visible to you.</p>
                    <form method="POST" action="/save">
                        <label>Black & White Printer Routing</label>
                        <select name="printer_bw">{options_bw}</select>
                        
                        <label>Color Printer Routing</label>
                        <select name="printer_color">{options_color}</select>
                        
                        <button type="submit">Save Hardware Routing</button>
                    </form>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
            
    def do_POST(self):
        if self.path == '/save':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode()
            params = urllib.parse.parse_qs(body)
            
            cfg = get_local_config()
            cfg['printer_bw'] = params.get('printer_bw', [''])[0]
            cfg['printer_color'] = params.get('printer_color', [''])[0]
            
            with open(CONFIG_FILE, 'w') as f:
                json.dump(cfg, f)
                
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()
            
    def log_message(self, format, *args):
        pass # Suppress HTTP logs to keep terminal clean

def run_local_server():
    try:
        server = HTTPServer(('127.0.0.1', 9090), ConfigHandler)
        logger.info("Local Configuration UI running at http://localhost:9090")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start local config server: {e}")


def main():
    print("=======================================")
    print(" PRINT BRIDGE - HEADLESS AGENT ")
    print("=======================================")
    
    email = os.environ.get('SHOP_EMAIL')
    password = os.environ.get('SHOP_PASSWORD')
    
    # Check local credential store
    cred_dir = os.path.expanduser('~/.printhub')
    cred_file = os.path.join(cred_dir, 'credentials.json')
    
    if not email or not password:
        if os.path.exists(cred_file):
            try:
                import json, base64
                with open(cred_file, 'r') as f:
                    creds = json.load(f)
                    email = creds.get('e')
                    password = base64.b64decode(creds.get('p').encode()).decode()
            except Exception as e:
                logger.error(f"Failed to read saved credentials: {e}")

    if not email or not password:
        if not sys.stdin.isatty():
            logger.error("Missing credentials in headless mode. Exiting.")
            sys.exit(1)
        if not email:
            email = input("Shop Email: ")
        if not password:
            import getpass
            password = getpass.getpass("Shop Password: ")

    try:
        auth_res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        user_id = auth_res.user.id
        logger.info("Authenticated successfully.")
        
        # Save credentials for next boot
        if not os.path.exists(cred_file):
            os.makedirs(cred_dir, exist_ok=True)
            import json, base64
            with open(cred_file, 'w') as f:
                json.dump({'e': email, 'p': base64.b64encode(password.encode()).decode()}, f)
            
            # Setup Windows Auto-Start if on Windows
            if platform.system() == "Windows":
                startup_dir = os.path.join(os.environ.get('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
                vbs_path = os.path.join(startup_dir, 'PrintHubBridge.vbs')
                exe_path = sys.executable
                if exe_path.endswith('.exe'):
                    vbs_content = f'Set WshShell = CreateObject("WScript.Shell")\nWshShell.Run chr(34) & "{exe_path}" & Chr(34), 0\nSet WshShell = Nothing'
                    with open(vbs_path, 'w') as f:
                        f.write(vbs_content)
                        
                    # Add to Windows Registry for ultimate reliability
                    try:
                        import winreg
                        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_SET_VALUE)
                        winreg.SetValueEx(key, 'PrintHubBridge', 0, winreg.REG_SZ, f'wscript.exe "{vbs_path}"')
                        winreg.CloseKey(key)
                    except Exception as reg_e:
                        logger.warning(f"Failed to set Registry key (non-fatal): {reg_e}")
                        
                    print("\n[SUCCESS] Auto-start heavily secured! PrintBridge is injected into the Startup folder AND the Windows Registry.\n")
                    
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise ConnectionError(f"Auth failed: {e}")

    shop_res = supabase.table('printhub_shops').select('id, is_active').eq('owner_uid', user_id).execute()
    if not shop_res.data:
        logger.error("No PrintHub shop linked to this account.")
        sys.exit(1)
        
    shop = shop_res.data[0]
    if not shop.get('is_active'):
        logger.error("Shop is suspended by Superadmin.")
        sys.exit(1)
    
    shop_id = shop['id']
    
    # Strict HWID Locking
    try:
        # Check existing HWID
        shop_info = supabase.table('printhub_shops').select('active_device_id').eq('id', shop_id).execute()
        current_hwid = shop_info.data[0].get('active_device_id')
        
        base_hwid = current_hwid.split('|')[0] if current_hwid else None
        
        if not base_hwid:
            # First time login on this shop - lock it to this device
            supabase.table('printhub_shops').update({'active_device_id': f"{HWID}|{int(time.time())}"}).eq('id', shop_id).execute()
            logger.info(f"Shop locked to this Hardware ID: {HWID}")
        elif base_hwid != HWID:
            # Device mismatch! Reject login.
            logger.error(f"SECURITY ALERT: This account is already locked to another computer.")
            logger.error(f"Please contact support to reset your Hardware ID if you changed devices.")
            return
        else:
            logger.info(f"Hardware ID matched. Access granted.")
            
    except Exception as e:
        logger.error(f"Failed to verify HWID: {e}")
        return
        
    logger.info(f"Bridge Active for Shop ID: {shop_id}")
    
    # Spin up local config UI
    threading.Thread(target=run_local_server, daemon=True).start()
    
    logger.info("Polling for approved print jobs...")
    
    last_heartbeat_time = 0
    while True:
        try:
            current_time = int(time.time())
            
            # Send Heartbeat every 15 seconds to keep the Dashboard "Online" meter green
            if current_time - last_heartbeat_time >= 15:
                supabase.table('printhub_shops').update({'active_device_id': f"{HWID}|{current_time}"}).eq('id', shop_id).execute()
                last_heartbeat_time = current_time

            # 1. Hardware Heartbeat & Killswitch Check
            heartbeat_res = supabase.table('printhub_shops').select('active_device_id, is_active').eq('id', shop_id).execute()
            if heartbeat_res.data:
                shop_status = heartbeat_res.data[0]
                if not shop_status.get('is_active'):
                    logger.error("Account suspended by platform administrator. Pausing operations.")
                    time.sleep(30)
                    continue
                
                fetched_hwid = str(shop_status.get('active_device_id', '')).split('|')[0]
                if fetched_hwid != HWID:
                    logger.error("Account logged in from another computer. Device access revoked. Exiting.")
                    break
                    
            # Poll for orders that are Paid and otp_verified == True
            res = supabase.table('printhub_orders')\
                .select('*')\
                .eq('shop_id', shop_id)\
                .eq('status', 'Paid')\
                .eq('otp_verified', True)\
                .execute()
                
            orders = res.data
            for order in orders:
                process_order(order)
                
        except Exception as e:
            logger.error(f"Error during polling: {e}")
            
        time.sleep(5)

if __name__ == '__main__':
    retry_count = 0
    while True:
        try:
            main()
        except SystemExit:
            # Explicit exit requested (e.g. suspended shop or missing credentials)
            break
        except Exception as e:
            retry_count += 1
            import traceback
            error_log = os.path.expanduser('~/.printhub/crash_report.txt')
            with open(error_log, 'a') as f:
                f.write(f"\n--- CRASH {time.ctime()} ---\n")
                f.write(traceback.format_exc())
            
            print(f"[{time.ctime()}] Network or System error. Retrying in 10 seconds... (Attempt {retry_count})")
            time.sleep(10)

# Trigger build
