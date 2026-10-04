with open("index.html", "r") as f:
    code = f.read()

# Render logo and location in the header
old_init_header = """        currentShopId = shopData.id;
        currentShopName = shopData.shop_name;
        document.querySelector('header h1').textContent = currentShopName;
        document.title = currentShopName + " - PrintHub SaaS";"""

new_init_header = """        currentShopId = shopData.id;
        currentShopName = shopData.shop_name;
        
        // Render Branding
        let headerHtml = currentShopName;
        if (shopData.logo_url) {
            headerHtml = `<img src="${shopData.logo_url}" style="height: 48px; width: 48px; object-fit: cover; border-radius: 50%; vertical-align: middle; margin-right: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">` + currentShopName;
        }
        document.querySelector('header h1').innerHTML = headerHtml;
        document.title = currentShopName + " - PrintHub SaaS";
        
        // Render Location
        if (shopData.location) {
            const locEl = document.createElement('div');
            locEl.innerHTML = `📍 ${shopData.location}`;
            locEl.style.cssText = "color: #64748b; font-size: 0.95rem; margin-top: 0.5rem; font-weight: 500;";
            document.querySelector('.subtitle').insertAdjacentElement('afterend', locEl);
        }"""
code = code.replace(old_init_header, new_init_header)

# Render Offer Banner if available
old_settings_fetch = """        const { data: settingsData } = await supabaseClient.from('printhub_settings').select('price_bw, price_color, is_accepting_orders').eq('shop_id', currentShopId).single();
        
        if (settingsData) {
            RATES.bw = parseFloat(settingsData.price_bw) || 2.0;
            RATES.color = parseFloat(settingsData.price_color) || 10.0;
            SHOP_ONLINE = settingsData.is_accepting_orders;"""

new_settings_fetch = """        const { data: settingsData } = await supabaseClient.from('printhub_settings').select('price_bw, price_color, is_accepting_orders, offer_banner').eq('shop_id', currentShopId).single();
        
        if (settingsData) {
            RATES.bw = parseFloat(settingsData.price_bw) || 2.0;
            RATES.color = parseFloat(settingsData.price_color) || 10.0;
            SHOP_ONLINE = settingsData.is_accepting_orders;
            
            // Render Offer Banner
            if (settingsData.offer_banner) {
                const banner = document.createElement('div');
                banner.innerHTML = `🎉 <strong>Special Offer:</strong> ${settingsData.offer_banner}`;
                banner.style.cssText = "background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; padding: 12px; text-align: center; border-radius: 8px; margin-bottom: 2rem; font-size: 0.95rem; box-shadow: 0 4px 6px -1px rgba(37,99,235,0.2);";
                document.querySelector('.upload-zone').insertAdjacentElement('beforebegin', banner);
            }"""
code = code.replace(old_settings_fetch, new_settings_fetch)

with open("index.html", "w") as f:
    f.write(code)

print("Index HTML patched to render branding and banners.")
