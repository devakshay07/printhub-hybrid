with open("shop_agent.py", "r") as f:
    code = f.read()

# Replace the create_client part
old_supabase_init = """SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlmbmp6aGZ0b2ZiaWh2d3Rjc3lxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTAyNzI4NzksImV4cCI6MjEwNTg0ODg3OX0.hw5XMsjmgHkUvHYs03vdRSZdhHqznjdkQHp_vwKO-Lg")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)"""

new_supabase_init = """# Security Upgrade: Use SERVICE_ROLE_KEY if available for backend ops
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlmbmp6aGZ0b2ZiaWh2d3Rjc3lxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTAyNzI4NzksImV4cCI6MjEwNTg0ODg3OX0.hw5XMsjmgHkUvHYs03vdRSZdhHqznjdkQHp_vwKO-Lg"
SUPABASE_KEY = SERVICE_KEY if SERVICE_KEY else ANON_KEY

if not SERVICE_KEY:
    print("⚠️ WARNING: Running with public ANON_KEY. Database RLS might block operations. Set SUPABASE_SERVICE_ROLE_KEY environment variable!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)"""

code = code.replace(old_supabase_init, new_supabase_init)

# Replace the run block with Waitress
old_run = """if __name__ == '__main__':
    print("Starting Local Shop Agent with Hardware Telemetry...")
    app.run(host='127.0.0.1', port=5001)"""

new_run = """if __name__ == '__main__':
    print("Starting Local Shop Agent with Hardware Telemetry (Production Mode)...")
    from waitress import serve
    serve(app, host='127.0.0.1', port=5002)"""

# Also fix the port 5002 if it was still 5001 in the source (I used sed earlier but let's be safe)
code = code.replace("app.run(host='127.0.0.1', port=5001)", "from waitress import serve\n    serve(app, host='127.0.0.1', port=5002)")
code = code.replace("app.run(host='127.0.0.1', port=5002)", "from waitress import serve\n    serve(app, host='127.0.0.1', port=5002)")

with open("shop_agent.py", "w") as f:
    f.write(code)
print("shop_agent.py patched!")
