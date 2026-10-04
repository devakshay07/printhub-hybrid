with open("shop_agent.py", "r") as f:
    code = f.read()

import_patch = "import json\nfrom dotenv import load_dotenv\nload_dotenv()"
code = code.replace("import json", import_patch)

with open("shop_agent.py", "w") as f:
    f.write(code)
print("Added python-dotenv")
