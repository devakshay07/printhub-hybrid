import os
import time
import threading
import subprocess
import re
import json
from flask import Flask, render_template, request, redirect, url_for
from supabase import create_client, Client
import requests

app = Flask(__name__)

SUPABASE_URL = "https://yfnjzhftofbihvwtcsyq.supabase.co"
# Security Upgrade: Use SERVICE_ROLE_KEY if available for backend ops
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlmbmp6aGZ0b2ZiaWh2d3Rjc3lxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTAyNzI4NzksImV4cCI6MjEwNTg0ODg3OX0.hw5XMsjmgHkUvHYs03vdRSZdhHqznjdkQHp_vwKO-Lg"
SUPABASE_KEY = SERVICE_KEY if SERVICE_KEY else ANON_KEY

if not SERVICE_KEY:
    print("⚠️ WARNING: Running with public ANON_KEY. Database RLS might block operations. Set SUPABASE_SERVICE_ROLE_KEY environment variable!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
TEMP_DIR = "temp_print_spool"
os.makedirs(TEMP_DIR, exist_ok=True)

CONFIG_FILE = "shop_config.json"

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

# In-memory tracker for active CUPS print jobs
active_print_jobs = {}

def purge_cloud_storage():
    try:
        from datetime import datetime, timezone, timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        res = supabase.table('printhub_orders').select('id, created_at, status').eq('status', 'Printed').execute()
        for order in res.data:
            created = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
            if created < cutoff:
                f_res = supabase.table('printhub_files').select('storage_path').eq('order_id', order['id']).execute()
                paths = [f['storage_path'] for f in f_res.data if f['storage_path'] != 'PURGED']
                if paths:
                    supabase.storage.from_('print-files').remove(paths)
                    supabase.table('printhub_files').update({'storage_path': 'PURGED'}).eq('order_id', order['id']).execute()
                supabase.table('printhub_orders').update({'status': 'Archived (Purged)'}).eq('id', order['id']).execute()
    except Exception as e:
        print(f"[Cost Control Error] {str(e)}")

def monitor_printer():
    last_sweep = 0
    while True:
        if time.time() - last_sweep > 3600:
            purge_cloud_storage()
            last_sweep = time.time()

        if active_print_jobs:
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
                print(f"[Telemetry Error] {str(e)}")
        time.sleep(3)

telemetry_thread = threading.Thread(target=monitor_printer, daemon=True)
telemetry_thread.start()

@app.route('/')
def dashboard():
    response = supabase.table('printhub_orders').select('*').order('created_at', desc=True).execute()
    orders = response.data
    files_res = supabase.table('printhub_files').select('*').execute()
    files_data = files_res.data
    for order in orders:
        order['files'] = [f for f in files_data if f['order_id'] == order['id']]
        if any(order['id'] == v.get('order_id') for v in active_print_jobs.values()) and order['status'] != 'Printed':
            order['status'] = 'Printing (Hardware)'
    return render_template('admin.html', orders=orders)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    success = False
    
    # Check if table exists by trying to select, if fails we assume we need to instruct user
    try:
        res = supabase.table('printhub_settings').select('*').eq('id', 1).execute()
        if not res.data:
            supabase.table('printhub_settings').insert([{'id': 1}]).execute()
            res = supabase.table('printhub_settings').select('*').eq('id', 1).execute()
        cloud_config = res.data[0]
    except Exception as e:
        return f"Error reaching Supabase settings table. Please run the setup SQL snippet in your Supabase SQL editor. Details: {e}", 500

    if request.method == 'POST':
        # Save local config
        local_cfg = {
            "printer_bw": request.form.get('printer_bw', ''),
            "printer_color": request.form.get('printer_color', '')
        }
        save_local_config(local_cfg)
        
        # Save cloud config
        is_accepting = request.form.get('is_accepting_orders') == 'true'
        price_bw = float(request.form.get('price_bw', 2.0))
        price_color = float(request.form.get('price_color', 10.0))
        
        supabase.table('printhub_settings').update({
            'is_accepting_orders': is_accepting,
            'price_bw': price_bw,
            'price_color': price_color
        }).eq('id', 1).execute()
        
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
        return f"Network Error: Unable to reach Supabase. Check your internet connection. (Error: {str(e)})", 503

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
        
        # Apply Hardware Routing based on Local Settings
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
        
        print(f"Executing: {' '.join(cmd)}")
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
    print("Starting Local Shop Agent with Hardware Telemetry...")
    from waitress import serve
    serve(app, host='127.0.0.1', port=5002)
