with open("shop_agent.py", "r") as f:
    code = f.read()

code = code.replace("if request.endpoint in ['login', 'static']:", "if request.endpoint in ['login', 'logout', 'static']:")

with open("shop_agent.py", "w") as f:
    f.write(code)

print("Auth middleware patched.")
