with open("index.html", "r") as f:
    code = f.read()

old_header = """            <div class="file-header">
                <div class="file-name">${f.name} <span class="file-badge">${f.totalPages} Pages</span></div>
                <button class="btn-remove" onclick="removeFile('${f.id}')">Remove</button>
            </div>"""

new_header = """            <div class="file-header" style="display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    ${f.type.startsWith('image/') ? `<img src="${URL.createObjectURL(f.originalFile)}" style="width: 40px; height: 40px; object-fit: cover; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">` : '<div style="width: 40px; height: 40px; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem;">📄</div>'}
                    <div class="file-name" style="margin: 0;">${f.name} <span class="file-badge">${f.type === 'application/pdf' ? f.totalPages + ' Pages' : 'Image'}</span></div>
                </div>
                <button class="btn-remove" onclick="removeFile('${f.id}')">Remove</button>
            </div>"""

code = code.replace(old_header, new_header)

with open("index.html", "w") as f:
    f.write(code)
print("File header updated with thumbnails.")
