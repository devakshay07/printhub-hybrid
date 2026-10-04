with open("superadmin.html", "r") as f:
    code = f.read()

# Make super admin fetch both shops and settings
old_fetch = """async function fetchShops() {
            const { data, error } = await supabase.from('printhub_shops').select('*').order('created_at', { ascending: false });"""

new_fetch = """async function fetchShops() {
            const { data, error } = await supabase.from('printhub_shops').select('*, printhub_settings(*)').order('created_at', { ascending: false });"""
code = code.replace(old_fetch, new_fetch)

# Update the edit modal UI in superadmin
old_modal_html = """            document.getElementById('editShopId').value = shop.id;
            document.getElementById('editShopName').value = shop.shop_name;
            document.getElementById('editSubdomain').value = shop.subdomain;
            document.getElementById('editModal').style.display = 'flex';"""

new_modal_html = """            document.getElementById('editShopId').value = shop.id;
            document.getElementById('editShopName').value = shop.shop_name;
            document.getElementById('editSubdomain').value = shop.subdomain;
            document.getElementById('editLocation').value = shop.location || '';
            document.getElementById('editLogo').value = shop.logo_url || '';
            
            const settings = shop.printhub_settings && shop.printhub_settings[0] ? shop.printhub_settings[0] : {};
            document.getElementById('editBanner').value = settings.offer_banner || '';
            document.getElementById('editPriceBw').value = settings.price_bw || '2';
            document.getElementById('editPriceColor').value = settings.price_color || '10';
            
            document.getElementById('editModal').style.display = 'flex';"""
code = code.replace(old_modal_html, new_modal_html)

old_modal_form = """        <div class="form-group">
            <label>Shop Name</label>
            <input type="text" id="editShopName" style="width:100%; padding: 8px; margin-top:5px; border-radius: 4px; border:1px solid #334155; background: #1e293b; color: white;">
        </div>"""

new_modal_form = """        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
            <div class="form-group">
                <label>Shop Name</label>
                <input type="text" id="editShopName" style="width:100%; padding: 8px; margin-top:5px; border-radius: 4px; border:1px solid #334155; background: #1e293b; color: white;">
            </div>
            <div class="form-group">
                <label>Subdomain</label>
                <input type="text" id="editSubdomain" style="width:100%; padding: 8px; margin-top:5px; border-radius: 4px; border:1px solid #334155; background: #1e293b; color: white;">
            </div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 10px;">
            <div class="form-group">
                <label>Logo URL</label>
                <input type="text" id="editLogo" style="width:100%; padding: 8px; margin-top:5px; border-radius: 4px; border:1px solid #334155; background: #1e293b; color: white;">
            </div>
            <div class="form-group">
                <label>Location</label>
                <input type="text" id="editLocation" style="width:100%; padding: 8px; margin-top:5px; border-radius: 4px; border:1px solid #334155; background: #1e293b; color: white;">
            </div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 10px;">
            <div class="form-group">
                <label>Price B&W</label>
                <input type="number" step="0.5" id="editPriceBw" style="width:100%; padding: 8px; margin-top:5px; border-radius: 4px; border:1px solid #334155; background: #1e293b; color: white;">
            </div>
            <div class="form-group">
                <label>Price Color</label>
                <input type="number" step="1" id="editPriceColor" style="width:100%; padding: 8px; margin-top:5px; border-radius: 4px; border:1px solid #334155; background: #1e293b; color: white;">
            </div>
        </div>
        <div class="form-group" style="margin-top: 10px;">
            <label>Offer Banner</label>
            <input type="text" id="editBanner" style="width:100%; padding: 8px; margin-top:5px; border-radius: 4px; border:1px solid #334155; background: #1e293b; color: white;">
        </div>"""

code = code.replace(old_modal_form, new_modal_form)

# Remove the old subdomain field since we moved it into the grid
code = code.replace("""        <div class="form-group" style="margin-top: 15px;">
            <label>Subdomain (URL Slug)</label>
            <input type="text" id="editSubdomain" style="width:100%; padding: 8px; margin-top:5px; border-radius: 4px; border:1px solid #334155; background: #1e293b; color: white;">
        </div>""", "")


old_save = """        async function saveShopEdit() {
            const id = document.getElementById('editShopId').value;
            const name = document.getElementById('editShopName').value;
            const sub = document.getElementById('editSubdomain').value;
            
            const { error } = await supabase.from('printhub_shops').update({ shop_name: name, subdomain: sub }).eq('id', id);"""

new_save = """        async function saveShopEdit() {
            const id = document.getElementById('editShopId').value;
            const name = document.getElementById('editShopName').value;
            const sub = document.getElementById('editSubdomain').value;
            const loc = document.getElementById('editLocation').value;
            const logo = document.getElementById('editLogo').value;
            
            const pbw = document.getElementById('editPriceBw').value;
            const pcol = document.getElementById('editPriceColor').value;
            const banner = document.getElementById('editBanner').value;
            
            const { error } = await supabase.from('printhub_shops').update({ 
                shop_name: name, subdomain: sub, location: loc, logo_url: logo 
            }).eq('id', id);
            
            await supabase.from('printhub_settings').update({
                price_bw: pbw, price_color: pcol, offer_banner: banner
            }).eq('shop_id', id);"""
code = code.replace(old_save, new_save)

with open("superadmin.html", "w") as f:
    f.write(code)

print("Superadmin HTML patched.")
