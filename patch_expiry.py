with open("index.html", "r") as f:
    code = f.read()

# Update query to include subscription_expiry
old_query = ".select('id, shop_name, is_active').eq('subdomain', subdomain)"
new_query = ".select('id, shop_name, is_active, subscription_expiry').eq('subdomain', subdomain)"
code = code.replace(old_query, new_query)

# Update the killswitch logic
old_logic = """if (shopData.is_active === false) {
            document.body.innerHTML = `<div style="padding: 3rem; text-align: center; font-family: sans-serif;"><h1 style="color: #ef4444;">Shop Suspended</h1><p>This shop's subscription to PrintHub has expired. Please contact the shop owner.</p></div>`;
            return;
        }"""

new_logic = """if (shopData.is_active === false) {
            document.body.innerHTML = `<div style="padding: 3rem; text-align: center; font-family: sans-serif;"><h1 style="color: #ef4444;">Shop Suspended</h1><p>This shop has been manually suspended.</p></div>`;
            return;
        }
        
        // Automated 3-Day Grace Period Killswitch
        if (shopData.subscription_expiry) {
            const expiryDate = new Date(shopData.subscription_expiry);
            const currentDate = new Date();
            const gracePeriodEnd = new Date(expiryDate.getTime() + (3 * 24 * 60 * 60 * 1000));
            
            if (currentDate > gracePeriodEnd) {
                document.body.innerHTML = `<div style="padding: 3rem; text-align: center; font-family: sans-serif;"><h1 style="color: #ef4444;">Service Unavailable</h1><p>This shop's SaaS subscription expired 3 days ago. The system has automatically locked the terminal.</p></div>`;
                return;
            } else if (currentDate > expiryDate) {
                // Shop is in grace period. We can silently log it or show a tiny warning for the owner.
                console.warn(`[SYSTEM] Shop is in 72-hour grace period. Expires entirely on ${gracePeriodEnd}`);
            }
        }"""

code = code.replace(old_logic, new_logic)

with open("index.html", "w") as f:
    f.write(code)
print("Automated Killswitch patched into frontend!")
