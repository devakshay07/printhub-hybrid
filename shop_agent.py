import os
import time
import threading
import subprocess
import re
import json
import uuid
import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from supabase import create_client, Client
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "printhub_enterprise_hardware_secret_key_change_me"

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://yfnjzhftofbihvwtcsyq.supabase.co")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlmbmp6aGZ0b2ZiaWh2d3Rjc3lxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTAyNzI4NzksImV4cCI6MjEwNTg0ODg3OX0.hw5XMsjmgHkUvHYs03vdRSZdhHqznjdkQHp_vwKO-Lg")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

TEMP_DIR = "temp_print_spool"
os.makedirs(TEMP_DIR, exist_ok=True)
CONFIG_FILE = "shop_config.json"

# Cryptographic Hardware ID (Motherboard/MAC hash)
def get_hwid():
    return str(uuid.getnode())

HWID = get_hwid()

AGENT_STATE = {
    'shop_id': None,
    'is_locked': True,
    'lock_reason': 'Device not authenticated. Please log in.'
}

active_print_jobs = {}

def get_local_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"printer_bw": "", "printer_color": ""}

def save_local_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f)

def get_system_printers():
    try:
        result = subprocess.run(['lpstat', '-a'], capture_output=True, text=True)
        printers = []
        for line in result.stdout.split('\n'):
            if line.strip():
                printers.append(line.split()[0])
        return printers
    except:
        return []

def hardware_heartbeat():
    while True:
        if AGENT_STATE['shop_id'] and not AGENT_STATE['is_locked']:
            try:
                res = supabase.table('printhub_shops').select('active_device_id, is_active').eq('id', AGENT_STATE['shop_id']).execute()
                if res.data:
                    shop = res.data[0]
                    # 1. Check Killswitch
                    if not shop.get('is_active'):
                        AGENT_STATE['is_locked'] = True
                        AGENT_STATE['lock_reason'] = "Shop suspended by Superadmin."
                    
                    # 2. Check Hardware Concurrency (Single Device Lock)
                    elif str(shop.get('active_device_id')) != HWID:
                        AGENT_STATE['is_locked'] = True
                        AGENT_STATE['lock_reason'] = "Account logged in from another computer. Hardware lock engaged."
                        try:
                            supabase.auth.sign_out()
                        except:
                            pass
            except Exception as e:
                pass
        time.sleep(5)

threading.Thread(target=hardware_heartbeat, daemon=True).start()

def monitor_printer():
    last_sweep = 0
    while True:
        if active_print_jobs and not AGENT_STATE['is_locked']:
            try:
                result = subprocess.run(['lpstat', '-o'], capture_output=True, text=True)
                active_cups_jobs = result.stdout
                jobs_to_remove = []
                for job_id, job_data in active_print_jobs.items():
                    if job_id not in active_cups_jobs:
                        order_id = job_data['order_id']
                        file_path = job_data['file_path']
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        supabase.table('printhub_orders').update({'status': 'Printed'}).eq('id', order_id).execute()
                        jobs_to_remove.append(job_id)
                for j in jobs_to_remove:
                    del active_print_jobs[j]
            except Exception as e:
                pass
        time.sleep(3)

threading.Thread(target=monitor_printer, daemon=True).start()

@app.before_request
def check_auth():
    if request.endpoint in ['login', 'static']:
        return
        
    if AGENT_STATE['is_locked']:
        return render_template('locked.html', reason=AGENT_STATE['lock_reason'], hwid=HWID)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            auth_res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            user_id = auth_res.user.id
            
            shop_res = supabase.table('printhub_shops').select('id, is_active').eq('owner_uid', user_id).execute()
            if not shop_res.data:
                return render_template('login.html', error="No PrintHub shop linked to this account.", hwid=HWID)
                
            shop = shop_res.data[0]
            if not shop.get('is_active'):
                return render_template('login.html', error="Shop is suspended by Superadmin.", hwid=HWID)
            
            shop_id = shop['id']
            # Authenticate HWID
            supabase.table('printhub_shops').update({'active_device_id': HWID}).eq('id', shop_id).execute()
            
            AGENT_STATE['shop_id'] = shop_id
            AGENT_STATE['is_locked'] = False
            AGENT_STATE['lock_reason'] = ""
            
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            return render_template('login.html', error="Invalid credentials or network error.", hwid=HWID)
            
    return render_template('login.html', hwid=HWID)

@app.route('/logout')
def logout():
    AGENT_STATE['is_locked'] = True
    AGENT_STATE['lock_reason'] = "Device disconnected securely."
    try:
        supabase.auth.sign_out()
    except:
        pass
    return redirect(url_for('login'))

@app.route('/')
def dashboard():
    shop_res = supabase.table('printhub_shops').select('subscription_expiry, is_active').eq('id', AGENT_STATE['shop_id']).execute()
    shop_data = shop_res.data[0] if shop_res.data else {}
    
    expiry_str = shop_data.get('subscription_expiry')
    is_active = shop_data.get('is_active', True)
    
    days_left = 999
    in_grace_period = False
    is_locked_ui = False
    
    if not is_active:
        is_locked_ui = True
    elif expiry_str:
        try:
            expiry_date = datetime.datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
            now = datetime.datetime.now(datetime.timezone.utc)
            delta = expiry_date - now
            days_left = delta.days
            
            if days_left < 0:
                in_grace_period = True
                if days_left < -3:
                    is_locked_ui = True
        except:
            pass

    response = supabase.table('printhub_orders').select('*').eq('shop_id', AGENT_STATE['shop_id']).order('created_at', desc=True).execute()
    orders = response.data
    files_res = supabase.table('printhub_files').select('*').execute()
    files_data = files_res.data
    for order in orders:
        order['files'] = [f for f in files_data if f['order_id'] == order['id']]
        if any(order['id'] == v.get('order_id') for v in active_print_jobs.values()) and order['status'] != 'Printed':
            order['status'] = 'Printing (Hardware)'
            
    return render_template('admin.html', orders=orders, days_left=days_left, in_grace_period=in_grace_period, is_locked=is_locked_ui)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    success = False
    try:
        res = supabase.table('printhub_settings').select('*').eq('shop_id', AGENT_STATE['shop_id']).execute()
        if not res.data:
            supabase.table('printhub_settings').insert([{'shop_id': AGENT_STATE['shop_id']}]).execute()
            res = supabase.table('printhub_settings').select('*').eq('shop_id', AGENT_STATE['shop_id']).execute()
        cloud_config = res.data[0]
    except Exception as e:
        return f"Error reaching Supabase settings table. {e}", 500

    if request.method == 'POST':
        local_cfg = {
            "printer_bw": request.form.get('printer_bw', ''),
            "printer_color": request.form.get('printer_color', '')
        }
        save_local_config(local_cfg)
        
        is_accepting = request.form.get('is_accepting_orders') == 'true'
        price_bw = float(request.form.get('price_bw', 2.0))
        price_color = float(request.form.get('price_color', 10.0))
        
        supabase.table('printhub_settings').update({
            'is_accepting_orders': is_accepting,
            'price_bw': price_bw,
            'price_color': price_color
        }).eq('shop_id', AGENT_STATE['shop_id']).execute()
        
        cloud_config['is_accepting_orders'] = is_accepting
        cloud_config['price_bw'] = price_bw
        cloud_config['price_color'] = price_color
        success = True

    local_config = get_local_config()
    system_printers = get_system_printers()
    
    return render_template('settings.html', 
                           cloud_config=cloud_config, 
                           local_config=local_config, 
                           system_printers=system_printers,
                           success=success)

@app.route('/status/<order_id>', methods=['POST'])
def update_status(order_id):
    status = request.form.get('status')
    supabase.table('printhub_orders').update({'status': status}).eq('id', order_id).execute()
    return redirect(url_for('dashboard'))

@app.route('/verify_otp/<order_id>', methods=['POST'])
def verify_otp(order_id):
    submitted_otp = request.form.get('otp', '').strip()
    try:
        res = supabase.table('printhub_orders').select('otp').eq('id', order_id).execute()
        if not res.data:
            return "Order not found", 404
        real_otp = res.data[0].get('otp')
        if submitted_otp == real_otp:
            supabase.table('printhub_orders').update({'otp_verified': True}).eq('id', order_id).execute()
            return redirect(url_for('dashboard'))
        else:
            return "INCORRECT PIN - Nice try ghost.", 403
    except Exception as e:
        return f"Network Error. (Error: {str(e)})", 503

@app.route('/print/<file_id>', methods=['POST'])
def print_file(file_id):
    try:
        file_res = supabase.table('printhub_files').select('*').eq('id', file_id).execute()
        if not file_res.data:
            return "File not found in DB", 404
        file_record = file_res.data[0]
        order_id = file_record['order_id']
        
        storage_path = file_record['storage_path']
        download_url = supabase.storage.from_('print-files').get_public_url(storage_path)
        
        local_filename = os.path.join(TEMP_DIR, os.path.basename(storage_path))
        r = requests.get(download_url, stream=True)
        if r.status_code == 200:
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
        else:
            return f"Failed to download: {r.status_code}", 500
            
        cmd = ["lp", "-n", str(file_record['copies'])]
        
        local_cfg = get_local_config()
        if file_record['color_mode'] == 'bw':
            cmd.extend(["-o", "ColorModel=Gray"])
            if local_cfg.get("printer_bw"):
                cmd.extend(["-d", local_cfg["printer_bw"]])
        else:
            if local_cfg.get("printer_color"):
                cmd.extend(["-d", local_cfg["printer_color"]])
            
        if file_record['sides'] == 'double':
            cmd.extend(["-o", "sides=two-sided-long-edge"])
        else:
            cmd.extend(["-o", "sides=one-sided"])
            
        cmd.append(local_filename)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return f"Print failed: {result.stderr}", 500
            
        match = re.search(r'request id is (\S+)', result.stdout)
        if match:
            job_id = match.group(1)
            active_print_jobs[job_id] = {'order_id': order_id, 'file_path': local_filename}
            supabase.table('printhub_orders').update({'status': 'Printing...'}).eq('id', order_id).execute()
            
    except Exception as e:
        return f"Exception occurred: {str(e)}", 500
        
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    print(f"Starting Local Shop Agent with HWID: {HWID}")
    from waitress import serve
    serve(app, host='127.0.0.1', port=5002)
