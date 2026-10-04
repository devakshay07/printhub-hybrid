with open("templates/settings.html", "r") as f:
    code = f.read()

# Add Shop Profile Section
new_profile_section = """
        <div class="card">
            <h3>Shop Profile (Cloud)</h3>
            <p style="color: #64748b; font-size: 0.9rem; margin-top: -10px; margin-bottom: 20px;">This updates your public branding on your unique Vercel link.</p>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div class="form-group">
                    <label>Shop Name</label>
                    <input type="text" name="shop_name" value="{{ shop_data.get('shop_name', '') }}" required>
                </div>
                <div class="form-group">
                    <label>Logo URL (Optional)</label>
                    <input type="text" name="logo_url" value="{{ shop_data.get('logo_url', '') }}" placeholder="https://example.com/logo.png">
                </div>
            </div>
            <div class="form-group">
                <label>Physical Location / Address</label>
                <input type="text" name="location" value="{{ shop_data.get('location', '') }}" placeholder="e.g., Near Main Gate, MIT Campus">
            </div>
            <div class="form-group">
                <label>Offer Banner / Announcement (Optional)</label>
                <input type="text" name="offer_banner" value="{{ cloud_config.get('offer_banner', '') }}" placeholder="e.g., 50% Off Color Prints Today!">
            </div>
        </div>

        <div class="card">
"""

if "Shop Profile (Cloud)" not in code:
    code = code.replace('<div class="card">', new_profile_section, 1)

with open("templates/settings.html", "w") as f:
    f.write(code)

print("settings.html UI updated.")
