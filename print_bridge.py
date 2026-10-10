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


# Enable ANSI colors on Windows
if platform.system() == "Windows":
    os.system("color")

class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


import urllib.request
import zipfile

def ensure_sumatra():
    sumatra_dir = os.path.join(_base_dir, "sumatra")
    sumatra_exe = os.path.join(sumatra_dir, "SumatraPDF.exe")
    if os.path.exists(sumatra_exe):
        return sumatra_exe
        
    logger.info("Downloading SumatraPDF Auto-Print Engine...")
    os.makedirs(sumatra_dir, exist_ok=True)
    zip_path = os.path.join(sumatra_dir, "sumatra.zip")
    
    # We use a reliable mirror for the portable 64-bit build
    url = "https://www.sumatrapdfreader.org/dl/rel/3.5.2/SumatraPDF-3.5.2-64.zip"
    try:
        import requests
        r = requests.get(url, verify=False)
        with open(zip_path, 'wb') as f:
            f.write(r.content)
    except Exception as e:
        logger.error(f"Failed to download SumatraPDF: {e}")
        return None
        
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(sumatra_dir)
        
    # Sumatra portable puts 'SumatraPDF-something.exe' inside. Rename it to SumatraPDF.exe
    for file in os.listdir(sumatra_dir):
        if file.lower().endswith('.exe') and file != "SumatraPDF.exe":
            os.rename(os.path.join(sumatra_dir, file), sumatra_exe)
            break
            
    try:
        os.remove(zip_path)
    except: pass
    
    return sumatra_exe


def get_printers():
    if platform.system() != "Windows":
        return ["Default Printer"]
    try:
        # Get all printers using WMI to ensure we only get valid queues
        # Strict hardware filter: Only grab printers where WorkOffline is False
        ps_cmd = 'Get-WmiObject -Class Win32_Printer | Where-Object { $_.WorkOffline -eq $false } | Select-Object -ExpandProperty Name'
        result = subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)
        printers = [p.strip() for p in result.stdout.split('\n') if p.strip()]
        return printers if printers else ["Default Printer"]
    except Exception as e:
        logger.error(f"Failed to fetch live printers: {e}")
        return ["Default Printer"]

def get_hwid():
    system = platform.system()
    hw_string = ""
    try:
        if system == "Darwin":
            result = subprocess.run(['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if "IOPlatformUUID" in line:
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

if platform.system() == "Windows":
    _base_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'PrintHub')
else:
    _base_dir = os.path.expanduser('~/.printhub')

TEMP_DIR = os.path.join(_base_dir, "temp_print_spool")
CONFIG_FILE = os.path.join(_base_dir, "shop_config.json")
os.makedirs(TEMP_DIR, exist_ok=True)

def get_local_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading config: {e}")
    return {"printer_bw": "", "printer_color": ""}

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
        if self.path.startswith('/order/'):
            order_id = self.path.split('/')[-1]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Fetch files for this order from Supabase
            files_res = supabase.table('printhub_files').select('*').eq('order_id', order_id).execute()
            files_html = ""
            if files_res.data:
                for f_rec in files_res.data:
                    local_filename = os.path.join(TEMP_DIR, os.path.basename(f_rec['storage_path']))
                    file_exists = os.path.exists(local_filename)
                    status_badge = '<span class="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs">Ready</span>' if file_exists else '<span class="px-2 py-1 bg-slate-100 text-slate-500 rounded-full text-xs">Deleted</span>'
                    
                    files_html += f"""
                    <div style="border: 1px solid #e2e8f0; padding: 15px; margin-bottom: 15px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: bold; margin-bottom: 5px;">{f_rec['filename']} {status_badge}</div>
                            <div style="font-size: 14px; color: #64748b;">Type: <strong style="color: {'#3b82f6' if f_rec.get('color_mode') == 'color' else '#475569'}">{str(f_rec.get('color_mode', 'bw')).upper()}</strong> | Copies: <strong>{f_rec.get('copies', 1)}</strong></div>
                        </div>
                        <div style="display: flex; gap: 10px;">
                            <a href="/file/{os.path.basename(f_rec['storage_path'])}" target="_blank" style="background: #3b82f6; color: white; padding: 8px 16px; text-decoration: none; border-radius: 6px; font-weight: bold;">Print / View</a>
                        </div>
                    </div>
                    """
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Order #{order_id[:8]} - PrintHub</title>
                <style>
                    body {{ font-family: -apple-system, system-ui, sans-serif; background: #f8fafc; color: #0f172a; max-width: 800px; margin: 40px auto; padding: 20px; }}
                    .card {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }}
                    button {{ background: #ef4444; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; width: 100%; margin-top: 20px; }}
                    button:hover {{ background: #dc2626; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h1 style="margin-top: 0;">Incoming Print Order</h1>
                    <p style="color: #64748b;">Order ID: {order_id}</p>
                    <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;">
                    
                    {files_html or "<p>No files found.</p>"}
                    
                    <form method="POST" action="/cleanup/{order_id}">
                        <button type="submit" onclick="return confirm('Are you sure? This will delete the files from your computer.')">Finish Order & Delete Files</button>
                    </form>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
            return
            
        if self.path.startswith('/file/'):
            filename = self.path.split('/')[-1]
            local_filename = os.path.join(TEMP_DIR, filename)
            if os.path.exists(local_filename):
                self.send_response(200)
                ext = filename.lower().split('.')[-1]
                content_type = 'application/pdf' if ext == 'pdf' else f'image/{ext}'
                self.send_header('Content-type', content_type)
                self.end_headers()
                with open(local_filename, 'rb') as file:
                    self.wfile.write(file.read())
            else:
                self.send_error(404, "File deleted or not found")
            return

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
        if self.path.startswith('/cleanup/'):
            order_id = self.path.split('/')[-1]
            # Delete local files for this order
            files_res = supabase.table('printhub_files').select('storage_path').eq('order_id', order_id).execute()
            if files_res.data:
                for f_rec in files_res.data:
                    local_filename = os.path.join(TEMP_DIR, os.path.basename(f_rec['storage_path']))
                    if os.path.exists(local_filename):
                        try:
                            os.remove(local_filename)
                            logger.info(f"Deleted {local_filename}")
                        except: pass
            
            # Update status
            supabase.table('printhub_orders').update({'status': 'Printed'}).eq('id', order_id).execute()
            
            self.send_response(303)
            self.send_header('Location', f'/order/{order_id}')
            self.end_headers()
            return
            
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

def garbage_collector():
    """Background thread to delete manual-preview PDFs older than 15 minutes"""
    import time
    while True:
        try:
            now = time.time()
            for filename in os.listdir(TEMP_DIR):
                file_path = os.path.join(TEMP_DIR, filename)
                if os.path.isfile(file_path):
                    if os.stat(file_path).st_mtime < now - 900:
                        try:
                            os.remove(file_path)
                            logger.info(f"Garbage collected old file: {filename}")
                        except: pass
        except Exception:
            pass
        time.sleep(300)

def run_local_server():
    try:
        server = HTTPServer(('127.0.0.1', 9090), ConfigHandler)
        logger.info("Local Configuration UI running at http://localhost:9090")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start local config server: {e}")


def process_order(order):
    order_id = order['id']
    logger.info(f"Processing Order #{order_id[:8]}")
    
    # 1. Fetch files
    files_res = supabase.table('printhub_files').select('*').eq('order_id', order_id).execute()
    if not files_res.data:
        logger.warning(f"No files found for order {order_id}")
        supabase.table('printhub_orders').update({'status': 'Printed'}).eq('id', order_id).execute()
        return
        
    # 2. Download files
    for f_rec in files_res.data:
        try:
            storage_path = f_rec['storage_path']
            filename = os.path.basename(storage_path)
            local_filename = os.path.join(TEMP_DIR, filename)
            
            logger.info(f"Downloading {storage_path}...")
            # Using authenticated GET
            import requests
            session = supabase.auth.get_session()
            headers = {"Authorization": f"Bearer {session.access_token}"} if session else {}
            
            file_url = f"{supabase.supabase_url}/storage/v1/object/authenticated/print-files/{storage_path}"
            r = requests.get(file_url, headers=headers)
            if r.status_code == 200:
                with open(local_filename, 'wb') as lf:
                    lf.write(r.content)
            else:
                # Try public bucket if authenticated fails
                public_url = supabase.storage.from_("print-files").get_public_url(storage_path)
                pr = requests.get(public_url)
                if pr.status_code == 200:
                    with open(local_filename, 'wb') as lf:
                        lf.write(pr.content)
                else:
                    logger.error(f"Failed to download {storage_path}")
        except Exception as e:
            logger.error(f"Download failed for {storage_path}: {e}")
            
    # 3. Print or Preview based on mode (Parse JSON Routing Payload)
    print_mode = 'manual'
    bw_target = None
    color_target = None
    
    notes_raw = order.get('notes') or ''
    if notes_raw.startswith('{'):
        import json
        try:
            route_data = json.loads(notes_raw)
            print_mode = route_data.get('mode', 'manual')
            bw_target = route_data.get('bw_printer')
            color_target = route_data.get('color_printer')
        except:
            print_mode = 'manual'
    else:
        print_mode = notes_raw if notes_raw else 'manual'
    
    sumatra_exe = None
    if print_mode == 'auto' and platform.system() == "Windows":
        sumatra_exe = ensure_sumatra()
        if not sumatra_exe:
            logger.warning("Failed to setup Auto-Print. Falling back to manual mode.")
            print_mode = 'manual'
            
    for f_rec in files_res.data:
        fname = os.path.basename(f_rec['storage_path'])
        local_path = os.path.join(TEMP_DIR, fname)
        if not os.path.exists(local_path):
            continue
            
        is_color = f_rec.get('color_mode') == 'color'
        color_str = f"{Colors.BLUE}[COLOR]{Colors.RESET}" if is_color else f"{Colors.BOLD}[B&W]{Colors.RESET}"
        copies = f_rec.get('copies', 1)
        
        print("")
        print(f"{Colors.CYAN}========================================={Colors.RESET}")
        print(f"{Colors.YELLOW}🖨️  PROCESSING FILE ({print_mode.upper()}){Colors.RESET}")
        print(f"File: {Colors.BOLD}{fname}{Colors.RESET}")
        print(f"Settings: {color_str} | {copies} Copies")
        print(f"{Colors.CYAN}========================================={Colors.RESET}")
        print("")
        
        try:
            abs_path = os.path.abspath(local_path)
            if print_mode == 'auto' and sumatra_exe:
                # Silently auto-print via Sumatra PDF using Dynamic Split-Routing
                color_flag = "color" if is_color else "monochrome"
                target_printer = color_target if is_color else bw_target
                
                cmd_args = [sumatra_exe]
                if target_printer and target_printer != "Default Printer":
                    cmd_args.extend(["-print-to", target_printer])
                    logger.info(f"{Colors.GREEN}Routing to hardware: {target_printer}{Colors.RESET}")
                else:
                    cmd_args.extend(["-print-to-default"])
                    logger.info(f"{Colors.GREEN}Routing to Default Windows Printer{Colors.RESET}")
                
                cmd_args.extend(["-print-settings", f"{copies}x,{color_flag}", abs_path])
                
                # Execute using a list to completely bypass cmd.exe quote-stripping corruption
                subprocess.run(cmd_args, shell=False)
                logger.info(f"{Colors.GREEN}Successfully spooled {fname}.{Colors.RESET}")
            else:
                # Manual Preview in Edge
                if platform.system() == "Windows":
                    try:
                        file_uri = f"file:///{abs_path.replace(chr(92), '/')}"
                        subprocess.run(f'start "" msedge "{file_uri}"', shell=True)
                    except Exception as ex1:
                        subprocess.run(['explorer.exe', abs_path])
                else:
                    subprocess.run(['open', abs_path])
        except Exception as e:
            logger.error(f"Failed to process {fname}: {e}")
            
    # 4. Zero-Trace Privacy Cleanup
    # Clear from Supabase Storage
    try:
        storage_paths = [f['storage_path'] for f in files_res.data]
        if storage_paths:
            supabase.storage.from_('print-files').remove(storage_paths)
            logger.info("Cleared files from Supabase cloud storage.")
    except Exception as e:
        logger.error(f"Failed to clear cloud storage: {e}")
        
    # Clear from local disk (if auto mode). Manual mode relies on the garbage collector.
    if print_mode == 'auto':
        for f_rec in files_res.data:
            local_path = os.path.join(TEMP_DIR, os.path.basename(f_rec['storage_path']))
            if os.path.exists(local_path):
                try:
                    os.remove(local_path)
                except: pass

    supabase.table('printhub_orders').update({'status': 'Printed'}).eq('id', order_id).execute()
    logger.info(f"Order #{order_id[:8]} marked as printed. Awaiting next order...")

def main():
    print("=======================================")
    print(" PRINT BRIDGE - HEADLESS AGENT ")
    print("=======================================")
    
    email = os.environ.get('SHOP_EMAIL')
    password = os.environ.get('SHOP_PASSWORD')
    
    # Check local credential store
    if platform.system() == "Windows":
        cred_dir = os.path.join(os.environ.get('APPDATA'), 'PrintHub')
    else:
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
            logger.error("Missing credentials in headless mode. Waiting 60 seconds and retrying...")
            time.sleep(60)
            raise ConnectionError("Missing credentials (headless)")
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
                    # Create a visible batch file instead of hidden VBS
                    bat_path = os.path.join(startup_dir, 'PrintHubBridge.bat')
                    bat_content = f'@echo off\nstart "" "{exe_path}"'
                    with open(bat_path, 'w') as f:
                        f.write(bat_content)
                        
                    # Add to Windows Registry directly to launch the visible .exe
                    try:
                        import winreg
                        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_SET_VALUE)
                        winreg.SetValueEx(key, 'PrintHubBridge', 0, winreg.REG_SZ, f'"{exe_path}"')
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
        
        base_hwid = None
        if current_hwid:
            if current_hwid.startswith('{'):
                import json
                try:
                    base_hwid = json.loads(current_hwid).get('hwid')
                except:
                    pass
            else:
                base_hwid = current_hwid.split('|')[0]
        
        if not base_hwid:
            # First time login on this shop - lock it to this device
            import json
            initial_payload = {"hwid": HWID, "ts": int(time.time()), "printers": get_printers(), "selected_printer": None}
            supabase.table('printhub_shops').update({'active_device_id': json.dumps(initial_payload)}).eq('id', shop_id).execute()
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
    
    # Spin up local config UI and Garbage Collector
    threading.Thread(target=run_local_server, daemon=True).start()
    threading.Thread(target=garbage_collector, daemon=True).start()
    
    logger.info("Polling for approved print jobs...")
    
    last_heartbeat_time = 0
    while True:
        try:
            current_time = int(time.time())
            
            # 1. Hardware Heartbeat & Killswitch Check (Fetch First)
            heartbeat_res = supabase.table('printhub_shops').select('active_device_id, is_active').eq('id', shop_id).execute()
            
            selected_printer = None
            if heartbeat_res.data:
                shop_status = heartbeat_res.data[0]
                if not shop_status.get('is_active'):
                    logger.error("Account suspended by platform administrator. Pausing operations.")
                    time.sleep(30)
                    continue
                
                device_data_str = str(shop_status.get('active_device_id', ''))
                # Handle legacy pipe format or new JSON format
                if device_data_str.startswith('{'):
                    import json
                    try:
                        device_data = json.loads(device_data_str)
                        fetched_hwid = device_data.get('hwid')
                        selected_printer = device_data.get('selected_printer')
                    except:
                        fetched_hwid = device_data_str.split('|')[0]
                else:
                    fetched_hwid = device_data_str.split('|')[0]
                
                if fetched_hwid != HWID:
                    logger.error("Account logged in from another computer. Device access revoked. Exiting.")
                    break
                    
            # Send Advanced Telemetry Heartbeat every 15 seconds
            if current_time - last_heartbeat_time >= 15:
                import json
                printers = get_printers()
                payload = {
                    "hwid": HWID,
                    "ts": current_time,
                    "printers": printers,
                    "selected_printer": selected_printer if selected_printer in printers else (printers[0] if printers else None)
                }
                supabase.table('printhub_shops').update({'active_device_id': json.dumps(payload)}).eq('id', shop_id).execute()
                last_heartbeat_time = current_time
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
            if platform.system() == "Windows":
                error_log = os.path.join(os.environ.get('APPDATA'), 'PrintHub', 'crash_report.txt')
            else:
                error_log = os.path.expanduser('~/.printhub/crash_report.txt')
            with open(error_log, 'a') as f:
                f.write(f"\n--- CRASH {time.ctime()} ---\n")
                f.write(traceback.format_exc())
            
            print(f"[{time.ctime()}] Network or System error. Retrying in 10 seconds... (Attempt {retry_count})")
            time.sleep(10)

# Trigger build
