with open("shop_agent.py", "r") as f:
    code = f.read()

old_settings_get = """    try:
        res = supabase.table('printhub_settings').select('*').eq('shop_id', AGENT_STATE['shop_id']).execute()"""

new_settings_get = """    try:
        shop_res = supabase.table('printhub_shops').select('*').eq('id', AGENT_STATE['shop_id']).execute()
        shop_data = shop_res.data[0] if shop_res.data else {}

        res = supabase.table('printhub_settings').select('*').eq('shop_id', AGENT_STATE['shop_id']).execute()"""

code = code.replace(old_settings_get, new_settings_get)

old_settings_post = """        is_accepting = request.form.get('is_accepting_orders') == 'true'
        price_bw = float(request.form.get('price_bw', 2.0))
        price_color = float(request.form.get('price_color', 10.0))
        
        supabase.table('printhub_settings').update({
            'is_accepting_orders': is_accepting,
            'price_bw': price_bw,
            'price_color': price_color
        }).eq('shop_id', AGENT_STATE['shop_id']).execute()
        
        cloud_config['is_accepting_orders'] = is_accepting
        cloud_config['price_bw'] = price_bw
        cloud_config['price_color'] = price_color
        success = True"""

new_settings_post = """        is_accepting = request.form.get('is_accepting_orders') == 'true'
        price_bw = float(request.form.get('price_bw', 2.0))
        price_color = float(request.form.get('price_color', 10.0))
        offer_banner = request.form.get('offer_banner', '')
        
        # 1. Update Profile in printhub_shops
        supabase.table('printhub_shops').update({
            'shop_name': request.form.get('shop_name', shop_data.get('shop_name')),
            'location': request.form.get('location', ''),
            'logo_url': request.form.get('logo_url', '')
        }).eq('id', AGENT_STATE['shop_id']).execute()
        
        # 2. Update Settings in printhub_settings
        supabase.table('printhub_settings').update({
            'is_accepting_orders': is_accepting,
            'price_bw': price_bw,
            'price_color': price_color,
            'offer_banner': offer_banner
        }).eq('shop_id', AGENT_STATE['shop_id']).execute()
        
        # Refresh state for UI render
        shop_data['shop_name'] = request.form.get('shop_name')
        shop_data['location'] = request.form.get('location')
        shop_data['logo_url'] = request.form.get('logo_url')
        
        cloud_config['is_accepting_orders'] = is_accepting
        cloud_config['price_bw'] = price_bw
        cloud_config['price_color'] = price_color
        cloud_config['offer_banner'] = offer_banner
        success = True"""

code = code.replace(old_settings_post, new_settings_post)

old_return = """return render_template('settings.html', 
                           cloud_config=cloud_config, 
                           local_config=local_config, 
                           system_printers=system_printers,
                           success=success)"""

new_return = """return render_template('settings.html', 
                           shop_data=shop_data,
                           cloud_config=cloud_config, 
                           local_config=local_config, 
                           system_printers=system_printers,
                           success=success)"""

code = code.replace(old_return, new_return)

with open("shop_agent.py", "w") as f:
    f.write(code)

print("Agent settings patched to support profile and banners.")
