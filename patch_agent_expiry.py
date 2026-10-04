with open("shop_agent.py", "r") as f:
    code = f.read()

# Modify the dashboard route to fetch shop expiry
old_dashboard = """@app.route('/')
def dashboard():
    response = supabase.table('printhub_orders').select('*').eq('shop_id', SHOP_ID).order('created_at', desc=True).execute()
    orders = response.data
    files_res = supabase.table('printhub_files').select('*').execute()
    files_data = files_res.data
    for order in orders:
        order['files'] = [f for f in files_data if f['order_id'] == order['id']]
        if any(order['id'] == v.get('order_id') for v in active_print_jobs.values()) and order['status'] != 'Printed':
            order['status'] = 'Printing (Hardware)'
    return render_template('admin.html', orders=orders)"""

new_dashboard = """from datetime import datetime, timezone

@app.route('/')
def dashboard():
    # Fetch shop data for expiry alerts
    shop_res = supabase.table('printhub_shops').select('subscription_expiry, is_active').eq('id', SHOP_ID).execute()
    shop_data = shop_res.data[0] if shop_res.data else {}
    
    expiry_str = shop_data.get('subscription_expiry')
    is_active = shop_data.get('is_active', True)
    
    days_left = 999
    in_grace_period = False
    is_locked = False
    
    if not is_active:
        is_locked = True
    elif expiry_str:
        try:
            # Parse ISO 8601 timestamp from Supabase
            expiry_date = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            delta = expiry_date - now
            days_left = delta.days
            
            if days_left < 0:
                in_grace_period = True
                if days_left < -3:
                    is_locked = True
        except Exception as e:
            print("Date parse error:", e)

    response = supabase.table('printhub_orders').select('*').eq('shop_id', SHOP_ID).order('created_at', desc=True).execute()
    orders = response.data
    files_res = supabase.table('printhub_files').select('*').execute()
    files_data = files_res.data
    for order in orders:
        order['files'] = [f for f in files_data if f['order_id'] == order['id']]
        if any(order['id'] == v.get('order_id') for v in active_print_jobs.values()) and order['status'] != 'Printed':
            order['status'] = 'Printing (Hardware)'
            
    return render_template('admin.html', orders=orders, days_left=days_left, in_grace_period=in_grace_period, is_locked=is_locked)"""

code = code.replace(old_dashboard, new_dashboard)

with open("shop_agent.py", "w") as f:
    f.write(code)
print("shop_agent.py updated for expiry alerts!")
