with open("superadmin.html", "r") as f:
    code = f.read()

# Add -30 days button and Edit button
old_buttons = """<button class="action-btn green" onclick="addTime('${shop.id}', 30)">+30 Days</button>
                        ${shop.is_active """

new_buttons = """<button class="action-btn green" onclick="addTime('${shop.id}', 30)">+30D</button>
                        <button class="action-btn red" style="background:#dc3545;" onclick="addTime('${shop.id}', -30)">-30D</button>
                        <button class="action-btn" style="background:#007bff;" onclick="editShop('${shop.id}', '${shop.shop_name}')">EDIT</button>
                        ${shop.is_active """
code = code.replace(old_buttons, new_buttons)

# Add editShop JS function
edit_js = """async function editShop(id, currentName) {
            const newName = prompt("Enter new Shop Name:", currentName);
            if(!newName || newName === currentName) return;
            
            await supabase.from('printhub_shops').update({ shop_name: newName }).eq('id', id);
            loadShops();
        }

        async function addTime(id, days) {"""
code = code.replace("async function addTime(id, days) {", edit_js)

with open("superadmin.html", "w") as f:
    f.write(code)
print("superadmin.html upgraded with enterprise features!")
