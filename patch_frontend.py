with open("index.html", "r") as f:
    code = f.read()

# Replace fetchShopSettings with multi-tenant version
old_fetch = """async function fetchShopSettings() {
    try {
        const { data, error } = await supabaseClient.from('printhub_settings').select('*').eq('id', 1).single();
        if (data) {
            RATES.bw = parseFloat(data.price_bw) || 2.0;
            RATES.color = parseFloat(data.price_color) || 10.0;
            SHOP_ONLINE = data.is_accepting_orders;
            
            if (!SHOP_ONLINE) {
                document.getElementById('dropzone').style.display = 'none';
                document.getElementById('dropzone').insertAdjacentHTML('afterend', '<div style="background:#fef2f2; color:#ef4444; padding:2rem; border-radius:16px; text-align:center; font-weight:bold; font-size:1.2rem; border:2px dashed #ef4444;">Shop is currently offline. We are not accepting orders right now.</div>');
            }
        }
    } catch (e) {
        console.error("Could not fetch shop settings", e);
    }
}
fetchShopSettings();"""

new_fetch = """let currentShopId = null;
let currentShopName = "PrintHub";

async function initializeTenant() {
    try {
        let hostname = window.location.hostname;
        let subdomain = 'demo'; // Default for local testing
        
        if (hostname !== 'localhost' && hostname !== '127.0.0.1' && hostname.includes('.')) {
            // Extract subdomain (e.g. 'akshay' from 'akshay.printhub.com')
            // For vercel apps like printhub-hybrid.vercel.app, we might need a specific check, but for MVP:
            subdomain = hostname.split('.')[0]; 
            // Fallback for vercel default domains during testing
            if (hostname.includes('vercel.app')) subdomain = 'demo';
        }

        // 1. Fetch Shop Details
        const { data: shopData, error: shopErr } = await supabaseClient.from('printhub_shops').select('*').eq('subdomain', subdomain).single();
        
        if (!shopData) {
            document.body.innerHTML = `<div style="padding: 3rem; text-align: center; font-family: sans-serif;"><h1>404 - Shop Not Found</h1><p>The print shop at subdomain '${subdomain}' does not exist on our platform.</p></div>`;
            return;
        }
        
        currentShopId = shopData.id;
        currentShopName = shopData.shop_name;
        document.querySelector('header h1').textContent = currentShopName;
        document.title = currentShopName + " - PrintHub SaaS";

        // 2. Fetch Shop Settings
        const { data: settingsData } = await supabaseClient.from('printhub_settings').select('*').eq('shop_id', currentShopId).single();
        
        if (settingsData) {
            RATES.bw = parseFloat(settingsData.price_bw) || 2.0;
            RATES.color = parseFloat(settingsData.price_color) || 10.0;
            SHOP_ONLINE = settingsData.is_accepting_orders;
            
            if (!SHOP_ONLINE) {
                document.getElementById('dropzone').style.display = 'none';
                document.getElementById('dropzone').insertAdjacentHTML('afterend', '<div style="background:#fef2f2; color:#ef4444; padding:2rem; border-radius:16px; text-align:center; font-weight:bold; font-size:1.2rem; border:2px dashed #ef4444;">Shop is currently offline. We are not accepting orders right now.</div>');
            }
        }
    } catch (e) {
        console.error("Could not initialize tenant", e);
    }
}
initializeTenant();"""

code = code.replace(old_fetch, new_fetch)

# Inject shop_id into the order insert
old_insert = """const { data: orderData, error: orderErr } = await supabaseClient
            .from('printhub_orders')
            .insert([{ 
                customer_name: name, 
                customer_email: email, 
                customer_phone: phone, 
                notes: paymentId ? `[PAID ONLINE: ${paymentId}] ${notes}` : notes, 
                total_amount: totalAmount, 
                otp: otpCode,
                status: initialStatus
            }])
            .select();"""

new_insert = """const { data: orderData, error: orderErr } = await supabaseClient
            .from('printhub_orders')
            .insert([{ 
                shop_id: currentShopId,
                customer_name: name, 
                customer_email: email, 
                customer_phone: phone, 
                notes: paymentId ? `[PAID ONLINE: ${paymentId}] ${notes}` : notes, 
                total_amount: totalAmount, 
                otp: otpCode,
                status: initialStatus
            }])
            .select();"""

code = code.replace(old_insert, new_insert)

with open("index.html", "w") as f:
    f.write(code)
print("index.html patched for SaaS multi-tenancy!")
