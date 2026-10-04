import re

with open("shop_agent.py", "r") as f:
    code = f.read()

# 1. Fetch SHOP_SUBDOMAIN from .env or config
env_patch = """import json
from dotenv import load_dotenv
load_dotenv()

SHOP_SUBDOMAIN = os.environ.get("SHOP_SUBDOMAIN", "demo")
"""
code = code.replace("import json\nfrom dotenv import load_dotenv\nload_dotenv()", env_patch)

# 2. Get shop_id globally on boot
boot_patch = """supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print(f"Fetching tenant ID for subdomain: {SHOP_SUBDOMAIN}...")
try:
    shop_res = supabase.table('printhub_shops').select('id').eq('subdomain', SHOP_SUBDOMAIN).execute()
    if not shop_res.data:
        print("CRITICAL ERROR: Shop subdomain not found in database! Halting.")
        exit(1)
    SHOP_ID = shop_res.data[0]['id']
    print(f"Tenant Authenticated! Shop ID: {SHOP_ID}")
except Exception as e:
    print(f"Failed to connect to Supabase: {e}")
    exit(1)
"""
code = code.replace("supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)", boot_patch)

# 3. Filter queries by SHOP_ID
# In purge_cloud_storage
code = code.replace(".eq('status', 'Printed').execute()", ".eq('status', 'Printed').eq('shop_id', SHOP_ID).execute()")
# In dashboard
code = code.replace(".order('created_at', desc=True).execute()", ".eq('shop_id', SHOP_ID).order('created_at', desc=True).execute()")
# In settings GET
code = code.replace("eq('id', 1).execute()", "eq('shop_id', SHOP_ID).execute()")
code = code.replace("insert([{'id': 1}]).execute()", "insert([{'shop_id': SHOP_ID}]).execute()")
# In settings POST
code = code.replace("eq('id', 1).execute()", "eq('shop_id', SHOP_ID).execute()")

with open("shop_agent.py", "w") as f:
    f.write(code)
print("shop_agent.py patched for SaaS multi-tenancy!")
