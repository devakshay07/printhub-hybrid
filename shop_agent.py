import os
import subprocess
import re
import threading
import time
from flask import Flask, render_template, redirect, url_for, request
from supabase import create_client, Client
import requests

app = Flask(__name__)

# ==========================================
# UPDATE THESE WITH YOUR REAL SUPABASE KEYS
# ==========================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://yfnjzhftofbihvwtcsyq.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlmbmp6aGZ0b2ZiaWh2d3Rjc3lxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTAyNzI4NzksImV4cCI6MjEwNTg0ODg3OX0.hw5XMsjmgHkUvHYs03vdRSZdhHqznjdkQHp_vwKO-Lg")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
TEMP_DIR = "temp_print_spool"
os.makedirs(TEMP_DIR, exist_ok=True)

# In-memory tracker for active CUPS print jobs
# Format: { 'job_id': {'order_id': '...', 'file_path': '...'} }
active_print_jobs = {}

def purge_cloud_storage():
    """Sweeps Supabase for Printed orders older than 24h and nukes their files."""
    try:
        from datetime import datetime, timezone, timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Fetch printed orders
        res = supabase.table('printhub_orders').select('id, created_at, status').eq('status', 'Printed').execute()
        for order in res.data:
            created = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
            if created < cutoff:
                # Time to purge
                print(f"[Cost Control] Purging cloud files for order {order['id']}")
                f_res = supabase.table('printhub_files').select('storage_path').eq('order_id', order['id']).execute()
                paths = [f['storage_path'] for f in f_res.data if f['storage_path'] != 'PURGED']
                
                if paths:
                    supabase.storage.from_('print-files').remove(paths)
                    supabase.table('printhub_files').update({'storage_path': 'PURGED'}).eq('order_id', order['id']).execute()
                
                # Mark as archived so we don't sweep it again
                supabase.table('printhub_orders').update({'status': 'Archived (Purged)'}).eq('id', order['id']).execute()
    except Exception as e:
        print(f"[Cost Control Error] {str(e)}")

def monitor_printer():
    """Background thread that polls CUPS lpstat to see if jobs are done."""
    last_sweep = 0
    while True:
        # Run cloud purge sweep every hour
        if time.time() - last_sweep > 3600:
            purge_cloud_storage()
            last_sweep = time.time()

        if active_print_jobs:
            try:
                # Get all currently pending/processing jobs in CUPS
                result = subprocess.run(['lpstat', '-o'], capture_output=True, text=True)
                active_cups_jobs = result.stdout

                # Check our tracked jobs against the active CUPS queue
                jobs_to_remove = []
                for job_id, job_data in active_print_jobs.items():
                    if job_id not in active_cups_jobs:
                        order_id = job_data['order_id']
                        file_path = job_data['file_path']
                        
                        # Job finished. Nuke the local file immediately.
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            print(f"[Cost Control] Local spool file {file_path} shredded.")
                            
                        print(f"[Telemetry] Job {job_id} finished printing. Updating Supabase...")
                        supabase.table('printhub_orders').update({'status': 'Printed'}).eq('id', order_id).execute()
                        jobs_to_remove.append(job_id)
                
                for j in jobs_to_remove:
                    del active_print_jobs[j]

            except Exception as e:
                print(f"[Telemetry Error] {str(e)}")
        
        time.sleep(3) # Poll every 3 seconds

# Start the hardware telemetry thread
telemetry_thread = threading.Thread(target=monitor_printer, daemon=True)
telemetry_thread.start()

@app.route('/')
def dashboard():
    # Fetch orders
    response = supabase.table('printhub_orders').select('*').order('created_at', desc=True).execute()
    orders = response.data
    
    # Fetch files for all these orders
    files_res = supabase.table('printhub_files').select('*').execute()
    files_data = files_res.data
    
    # Group files by order_id
    for order in orders:
        order['files'] = [f for f in files_data if f['order_id'] == order['id']]
        # If it's currently tracked in hardware telemetry, mark it as Printing
        if order['id'] in active_print_jobs.values() and order['status'] != 'Printed':
            order['status'] = 'Printing (Hardware)'
            
    return render_template('admin.html', orders=orders)

@app.route('/status/<order_id>', methods=['POST'])
def update_status(order_id):
    status = request.form.get('status')
    supabase.table('printhub_orders').update({'status': status}).eq('id', order_id).execute()
    return redirect(url_for('dashboard'))

@app.route('/verify_otp/<order_id>', methods=['POST'])
def verify_otp(order_id):
    submitted_otp = request.form.get('otp', '').strip()
    # Fetch real OTP from DB
    res = supabase.table('printhub_orders').select('otp').eq('id', order_id).execute()
    if not res.data:
        return "Order not found", 404
        
    real_otp = res.data[0].get('otp')
    if submitted_otp == real_otp:
        supabase.table('printhub_orders').update({'otp_verified': True}).eq('id', order_id).execute()
        return redirect(url_for('dashboard'))
    else:
        # In a real app we'd flash an error, but simple text return for hacking speed
        return "INCORRECT PIN - Nice try ghost.", 403

@app.route('/print/<file_id>', methods=['POST'])
def print_file(file_id):
    try:
        # 1. Get file details
        file_res = supabase.table('printhub_files').select('*').eq('id', file_id).execute()
        if not file_res.data:
            return "File not found in DB", 404
        file_record = file_res.data[0]
        order_id = file_record['order_id']
        
        # 2. Download file
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
            
        # 3. Construct Dynamic `lp` Command
        cmd = ["lp", "-n", str(file_record['copies'])]
        if file_record['color_mode'] == 'bw':
            cmd.extend(["-o", "ColorModel=Gray"])
        if file_record['sides'] == 'double':
            cmd.extend(["-o", "sides=two-sided-long-edge"])
        else:
            cmd.extend(["-o", "sides=one-sided"])
            
        cmd.append(local_filename)
        
        print(f"Executing: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return f"Print failed: {result.stderr}", 500
            
        # 4. Hardware Telemetry Hook
        # Parse the CUPS job ID from output: "request id is printer_name-123 (1 file(s))"
        match = re.search(r'request id is (\S+)', result.stdout)
        if match:
            job_id = match.group(1)
            print(f"[Telemetry] Tracked new hardware job: {job_id}")
            active_print_jobs[job_id] = {'order_id': order_id, 'file_path': local_filename}
            # Set status to Printing in Supabase so frontend knows it started
            supabase.table('printhub_orders').update({'status': 'Printing...'}).eq('id', order_id).execute()
            
    except Exception as e:
        return f"Exception occurred: {str(e)}", 500
        
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    print("Starting Local Shop Agent with Hardware Telemetry...")
    app.run(host='127.0.0.1', port=5000)
