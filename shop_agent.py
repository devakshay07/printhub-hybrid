import os
import subprocess
from flask import Flask, render_template, redirect, url_for, request, Response
from supabase import create_client, Client
import requests

app = Flask(__name__)

# ==========================================
# UPDATE THESE WITH YOUR REAL SUPABASE KEYS
# ==========================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "YOUR_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY", "YOUR_SUPABASE_ANON_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
TEMP_DIR = "temp_print_spool"
os.makedirs(TEMP_DIR, exist_ok=True)

@app.route('/')
def dashboard():
    # Fetch orders
    response = supabase.table('orders').select('*').order('created_at', desc=True).execute()
    orders = response.data
    
    # Fetch files for all these orders
    files_res = supabase.table('order_files').select('*').execute()
    files_data = files_res.data
    
    # Group files by order_id
    for order in orders:
        order['files'] = [f for f in files_data if f['order_id'] == order['id']]
        
    return render_template('admin.html', orders=orders)

@app.route('/status/<order_id>', methods=['POST'])
def update_status(order_id):
    status = request.form.get('status')
    supabase.table('orders').update({'status': status}).eq('id', order_id).execute()
    return redirect(url_for('dashboard'))

@app.route('/print/<file_id>', methods=['POST'])
def print_file(file_id):
    try:
        # 1. Get file details from Supabase
        file_res = supabase.table('order_files').select('*').eq('id', file_id).execute()
        if not file_res.data:
            return "File not found in DB", 404
        file_record = file_res.data[0]
        
        # 2. Download file from Supabase Storage
        storage_path = file_record['storage_path']
        download_url = supabase.storage.from_('print-files').get_public_url(storage_path)
        
        local_filename = os.path.join(TEMP_DIR, os.path.basename(storage_path))
        
        # Download it
        r = requests.get(download_url, stream=True)
        if r.status_code == 200:
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
        else:
            return f"Failed to download file from Supabase: {r.status_code}", 500
            
        # 3. Construct Dynamic `lp` Command
        # Default options
        cmd = ["lp", "-n", str(file_record['copies'])]
        
        # Color mode
        if file_record['color_mode'] == 'bw':
            # CUPS generic grayscale flag
            cmd.extend(["-o", "ColorModel=Gray"])
            
        # Sides (Duplex)
        if file_record['sides'] == 'double':
            cmd.extend(["-o", "sides=two-sided-long-edge"])
        else:
            cmd.extend(["-o", "sides=one-sided"])
            
        # Add the file path
        cmd.append(local_filename)
        
        print(f"Executing print command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return f"Print failed: {result.stderr}", 500
            
    except Exception as e:
        return f"Exception occurred: {str(e)}", 500
        
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    print("Starting Local Shop Agent...")
    print(f"Make sure to set your Supabase keys in the file or env vars!")
    app.run(host='127.0.0.1', port=5000)
