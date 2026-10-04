with open("shop_agent.py", "r") as f:
    code = f.read()

import re

old_verify = """@app.route('/verify_otp/<order_id>', methods=['POST'])
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
        return "INCORRECT PIN - Nice try ghost.", 403"""

new_verify = """@app.route('/verify_otp/<order_id>', methods=['POST'])
def verify_otp(order_id):
    submitted_otp = request.form.get('otp', '').strip()
    try:
        # Fetch real OTP from DB
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
        return f"Network Error: Unable to reach Supabase. Check your internet connection. (Error: {str(e)})", 503"""

if old_verify in code:
    code = code.replace(old_verify, new_verify)
    with open("shop_agent.py", "w") as f:
        f.write(code)
    print("Patched verify_otp")
else:
    print("old_verify block not found!")
