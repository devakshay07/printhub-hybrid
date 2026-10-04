import re

with open("index.html", "r") as f:
    code = f.read()

# 1. Add Responsive CSS
responsive_css = """
/* Responsive Mobile Adjustments */
@media (max-width: 768px) {
    .container { padding: 1rem; }
    .config-grid { grid-template-columns: 1fr !important; gap: 1rem; }
    .payment-options { flex-direction: column; }
    .pay-option { width: 100%; box-sizing: border-box; }
    .slicer-header { flex-direction: column; gap: 1rem; text-align: center; }
    .slicer-footer { flex-direction: column; gap: 1rem; }
    .slicer-footer input { width: 100%; box-sizing: border-box; }
    .slicer-footer button { width: 100%; }
    .slicer-body { grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); padding: 1rem; }
    .checkout-footer .container { flex-direction: column; gap: 1rem; align-items: stretch !important; text-align: center; }
    .file-header { flex-direction: column; align-items: flex-start !important; gap: 1rem; }
    .btn-remove { width: 100%; }
}
</style>
"""
code = code.replace("</style>", responsive_css)

# 2. Fix the Slicer Button UI (Make it highly recognizable and mobile-friendly)
# We will place the input and the button side-by-side (or stacked on mobile)
old_input_group = """                ${f.type === 'application/pdf' ? `
                <div class="input-group" style="flex: 2;">
                    <label style="display: flex; justify-content: space-between; align-items: center;">
                        <span>Specific Pages</span>
                        <button onclick="openVisualSlicer('${f.id}')" style="background: none; border: none; color: #2563eb; font-size: 0.85rem; font-weight: 600; cursor: pointer; padding: 0;">👁️ Open Visual Slicer</button>
                    </label>
                    <input type="text" placeholder="e.g. 1-3, 5 (Leave blank for all)" value="${f.config.pageRange}" onchange="updateConfig('${f.id}', 'pageRange', this.value)" id="range-input-${f.id}">
                </div>
                ` : ''}"""

new_input_group = """                ${f.type === 'application/pdf' ? `
                <div class="input-group" style="flex: 2; min-width: 100%;">
                    <label>Specific Pages</label>
                    <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                        <input type="text" style="flex: 1; min-width: 150px;" placeholder="e.g. 1-3, 5 (Leave blank for all)" value="${f.config.pageRange}" onchange="updateConfig('${f.id}', 'pageRange', this.value)">
                        <button class="btn-primary" style="padding: 0.75rem 1rem; white-space: nowrap; display: flex; align-items: center; gap: 0.5rem; background: #3b82f6;" onclick="openVisualSlicer('${f.id}')">
                            👁️ Visual Select
                        </button>
                    </div>
                </div>
                ` : ''}"""

if old_input_group in code:
    code = code.replace(old_input_group, new_input_group)
else:
    print("WARNING: Could not find old input group to replace.")

# 3. Fix saveSlicerSelection() to use updateConfig to trigger strict recalculation
old_save_func = """function saveSlicerSelection() {
    const f = filesData[currentSlicerFileIndex];
    f.config.pageRange = document.getElementById('slicer-range-input').value;
    document.getElementById('slicer-modal').style.display = 'none';
    renderFileList();
    calculateTotal();
}"""

new_save_func = """function saveSlicerSelection() {
    const f = filesData[currentSlicerFileIndex];
    const newValue = document.getElementById('slicer-range-input').value;
    document.getElementById('slicer-modal').style.display = 'none';
    // This triggers renderFileList AND calculateTotal cleanly:
    updateConfig(f.id, 'pageRange', newValue);
}"""

if old_save_func in code:
    code = code.replace(old_save_func, new_save_func)
else:
    print("WARNING: Could not find old saveSlicerSelection function.")


with open("index.html", "w") as f:
    f.write(code)
print("Mobile responsiveness and Slicer fixes applied.")
