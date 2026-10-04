import re

with open("index.html", "r") as f:
    code = f.read()

# The exact block to replace
old_block = """                ${f.type === 'application/pdf' ? `
                <div class="input-group">
                    <label>Specific Pages</label>
                    <input type="text" placeholder="e.g. 1-3, 5 (Leave blank for all)" value="${f.config.pageRange}" onchange="updateConfig('${f.id}', 'pageRange', this.value)">
                </div>
                ` : ''}"""

new_block = """                ${f.type === 'application/pdf' ? `
                <div class="input-group" style="flex: 2;">
                    <label style="display: flex; justify-content: space-between; align-items: center;">
                        <span>Specific Pages</span>
                        <button onclick="openVisualSlicer('${f.id}')" style="background: none; border: none; color: #2563eb; font-size: 0.85rem; font-weight: 600; cursor: pointer; padding: 0;">👁️ Open Visual Slicer</button>
                    </label>
                    <input type="text" placeholder="e.g. 1-3, 5 (Leave blank for all)" value="${f.config.pageRange}" onchange="updateConfig('${f.id}', 'pageRange', this.value)" id="range-input-${f.id}">
                </div>
                ` : ''}"""

if old_block in code:
    code = code.replace(old_block, new_block)
else:
    print("WARNING: Could not find the block to replace!")

# I also need to fix openVisualSlicer to take f.id instead of index
old_js_start = """async function openVisualSlicer(fileIndex) {
    currentSlicerFileIndex = fileIndex;
    const f = filesData[fileIndex];"""

new_js_start = """async function openVisualSlicer(fileId) {
    const fileIndex = filesData.findIndex(file => file.id === fileId);
    if (fileIndex === -1) return;
    currentSlicerFileIndex = fileIndex;
    const f = filesData[fileIndex];"""

if old_js_start in code:
    code = code.replace(old_js_start, new_js_start)

# Add some modern styling to the modal to ensure it doesn't look "old"
code = code.replace("background: #111;", "background: #f8fafc; color: #0f172a;")
code = code.replace("background: #222;", "background: #ffffff; color: #0f172a;")
code = code.replace("border-bottom: 1px solid #333;", "border-bottom: 1px solid #e2e8f0;")
code = code.replace("border-top: 1px solid #333;", "border-top: 1px solid #e2e8f0;")
code = code.replace("color: #fff;", "color: #0f172a;")
code = code.replace("rgba(0,0,0,0.95)", "rgba(15, 23, 42, 0.7)")
code = code.replace(".slicer-modal", "backdrop-filter: blur(10px);")

with open("index.html", "w") as f:
    f.write(code)
print("Slicer button and modern UI injected.")
