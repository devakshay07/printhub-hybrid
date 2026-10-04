import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("SUPABASE_URL", "https://yfnjzhftofbihvwtcsyq.supabase.co")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(url, key)

# 1. Get the demo shop ID
shop_res = supabase.table('printhub_shops').select('id').eq('subdomain', 'demo').execute()
if not shop_res.data:
    print("Demo shop not found.")
    exit()
shop_id = shop_res.data[0]['id']

# 2. Insert Order
order_res = supabase.table('printhub_orders').insert([{
    'shop_id': shop_id,
    'customer_name': 'ERA Automated Test',
    'customer_email': 'era@printhub.com',
    'customer_phone': '9999999999',
    'total_amount': 25.0,
    'otp': '9999',
    'status': 'Pending',
    'notes': 'Automated system diagnostic test'
}]).execute()

order_id = order_res.data[0]['id']

# 3. Insert File record
file_res = supabase.table('printhub_files').insert([{
    'order_id': order_id,
    'file_name': 'diagnostic_test.pdf',
    'storage_path': 'test/diagnostic_test.pdf',
    'copies': 1,
    'color_mode': 'bw',
    'sides': 'one-sided',
    'page_ranges': '1'
}]).execute()

print(f"✅ Order {order_id} successfully injected into the cloud network.")
