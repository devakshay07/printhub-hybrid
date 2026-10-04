with open("index.html", "r") as f:
    code = f.read()

old_logic = """if (!shopData) {
            document.body.innerHTML = `<div style="padding: 3rem; text-align: center; font-family: sans-serif;"><h1>404 - Shop Not Found</h1><p>The print shop at subdomain '${subdomain}' does not exist on our platform.</p></div>`;
            return;
        }
        
        currentShopId = shopData.id;"""

new_logic = """if (!shopData) {
            document.body.innerHTML = `<div style="padding: 3rem; text-align: center; font-family: sans-serif;"><h1>404 - Shop Not Found</h1><p>The print shop at subdomain '${subdomain}' does not exist on our platform.</p></div>`;
            return;
        }
        
        if (shopData.is_active === false) {
            document.body.innerHTML = `<div style="padding: 3rem; text-align: center; font-family: sans-serif;"><h1 style="color: #ef4444;">Shop Suspended</h1><p>This shop's subscription to PrintHub has expired. Please contact the shop owner.</p></div>`;
            return;
        }
        
        currentShopId = shopData.id;"""

code = code.replace(old_logic, new_logic)

with open("index.html", "w") as f:
    f.write(code)
print("Killswitch patched into frontend!")
