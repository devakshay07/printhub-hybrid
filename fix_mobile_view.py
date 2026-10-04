with open("index.html", "r") as f:
    code = f.read()

# 1. Fix Slicer Modal CSS (Solid Background instead of Transparent Blur)
old_slicer_css = "#slicer-modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(10px); z-index: 2000; flex-direction: column; color: #0f172a; font-family: sans-serif; }"
new_slicer_css = "#slicer-modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #f8fafc; z-index: 2000; flex-direction: column; color: #0f172a; font-family: sans-serif; }"
code = code.replace(old_slicer_css, new_slicer_css)

# 2. Fix the Mobile Media Query that was causing the massive header/footer
old_media = """    .slicer-header { flex-direction: column; gap: 1rem; text-align: center; }
    .slicer-footer { flex-direction: column; gap: 1rem; }"""

new_media = """    .slicer-header { flex-direction: row; padding: 1rem; }
    .slicer-header h2 { font-size: 1.2rem; margin: 0; }
    .slicer-footer { flex-direction: column; gap: 0.5rem; padding: 1rem; }
    .slicer-footer input { padding: 0.5rem; }"""
code = code.replace(old_media, new_media)

# 3. Fix the Header Logo Layout (Flexbox to handle wrapping text gracefully)
old_header_js = """        let headerHtml = currentShopName;
        if (shopData.logo_url) {
            headerHtml = `<img src="${shopData.logo_url}" style="height: 48px; width: 48px; object-fit: cover; border-radius: 50%; vertical-align: middle; margin-right: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">` + currentShopName;
        }
        document.querySelector('header h1').innerHTML = headerHtml;"""

new_header_js = """        let headerHtml = currentShopName;
        if (shopData.logo_url) {
            headerHtml = `<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px;">
                            <img src="${shopData.logo_url}" style="height: 64px; width: 64px; object-fit: cover; border-radius: 50%; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                            <span>${currentShopName}</span>
                          </div>`;
        }
        document.querySelector('header h1').innerHTML = headerHtml;"""
code = code.replace(old_header_js, new_header_js)

# 4. Improve Thumbnail aspect ratio and spacing on mobile
old_thumbnail_css = ".slicer-body { flex: 1; overflow-y: auto; padding: 2rem; display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 1.5rem; align-content: start; }"
new_thumbnail_css = ".slicer-body { flex: 1; overflow-y: auto; padding: 1rem; display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 1rem; align-content: start; }"
code = code.replace(old_thumbnail_css, new_thumbnail_css)

with open("index.html", "w") as f:
    f.write(code)

print("Mobile view CSS and Slicer layout patched.")
