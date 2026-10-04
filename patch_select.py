with open("index.html", "r") as f:
    code = f.read()

code = code.replace(".select('id, shop_name, is_active, subscription_expiry')", ".select('id, shop_name, is_active, subscription_expiry, location, logo_url')")

with open("index.html", "w") as f:
    f.write(code)

print("Select clause patched.")
