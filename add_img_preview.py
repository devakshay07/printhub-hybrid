with open("index.html", "r") as f:
    code = f.read()

# Add a thumbnail image to the file card
old_card_header = """<div class="file-info">
                <strong>${f.name}</strong>
                <span class="badge">${f.type === 'application/pdf' ? f.totalPages + ' Pages' : 'Image'}</span>
            </div>"""

new_card_header = """<div class="file-info" style="display: flex; align-items: center; gap: 1rem;">
                ${f.type.startsWith('image/') ? `<img src="${URL.createObjectURL(f.originalFile)}" style="width: 40px; height: 40px; object-fit: cover; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">` : '<div style="width: 40px; height: 40px; background: #e2e8f0; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem;">📄</div>'}
                <div style="display: flex; flex-direction: column;">
                    <strong>${f.name}</strong>
                    <span class="badge" style="width: fit-content; margin-top: 4px;">${f.type === 'application/pdf' ? f.totalPages + ' Pages' : 'Image'}</span>
                </div>
            </div>"""

if old_card_header in code:
    code = code.replace(old_card_header, new_card_header)
else:
    print("Could not find file info header.")

with open("index.html", "w") as f:
    f.write(code)
print("Image previews added.")
