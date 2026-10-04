with open("index.html", "r") as f:
    code = f.read()

# Fix the shop data query to prevent leaking the agent_api_key
old_query = ".select('*').eq('subdomain', subdomain)"
new_query = ".select('id, shop_name, is_active').eq('subdomain', subdomain)"
code = code.replace(old_query, new_query)

# Also ensure printhub_settings query is safe
old_settings_query = ".from('printhub_settings').select('*').eq('shop_id', currentShopId)"
new_settings_query = ".from('printhub_settings').select('price_bw, price_color, is_accepting_orders').eq('shop_id', currentShopId)"
code = code.replace(old_settings_query, new_settings_query)

with open("index.html", "w") as f:
    f.write(code)
print("Frontend patched to avoid requesting sensitive columns!")
