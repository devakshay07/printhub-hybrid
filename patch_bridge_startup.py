import re

with open('print_bridge.py', 'r') as f:
    code = f.read()

# Make sure sys is imported
if 'import sys' not in code:
    code = code.replace('import os', 'import os\nimport sys\nimport base64')

new_auth_logic = """    email = os.environ.get('SHOP_EMAIL')
    password = os.environ.get('SHOP_PASSWORD')
    
    # Check local credential store
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
                    # Create a silent VBS wrapper so it runs in background without a console window on boot
                    vbs_content = f'Set WshShell = CreateObject("WScript.Shell")\\nWshShell.Run chr(34) & "{exe_path}" & Chr(34), 0\\nSet WshShell = Nothing'
                    with open(vbs_path, 'w') as f:
                        f.write(vbs_content)
                    print("\n[SUCCESS] Auto-start configured! PrintBridge will now run silently in the background every time you turn on this computer.\n")
                    
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        return"""

old_auth_logic = """    email = os.environ.get('SHOP_EMAIL')
    password = os.environ.get('SHOP_PASSWORD')
    
    if not email:
        email = input("Shop Email: ")
    if not password:
        password = getpass("Shop Password: ")

    try:
        auth_res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        user_id = auth_res.user.id
        logger.info("Authenticated successfully.")
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        return"""

code = code.replace(old_auth_logic, new_auth_logic)

with open('print_bridge.py', 'w') as f:
    f.write(code)
