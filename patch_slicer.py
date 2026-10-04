with open("index.html", "r") as f:
    code = f.read()

# 1. Add PDF.js to HEAD
pdfjs_script = '<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js"></script>'
if pdfjs_script not in code:
    code = code.replace("</head>", f"    {pdfjs_script}\n</head>")

# 2. Add Slicer CSS
css = """
#slicer-modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95); z-index: 2000; flex-direction: column; color: white; font-family: sans-serif; }
.slicer-header { padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; background: #111; border-bottom: 1px solid #333; }
.slicer-body { flex: 1; overflow-y: auto; padding: 2rem; display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 1.5rem; align-content: start; }
.page-thumbnail { position: relative; cursor: pointer; border: 4px solid transparent; border-radius: 6px; overflow: hidden; background: #fff; transition: transform 0.1s; }
.page-thumbnail:hover { transform: scale(1.02); }
.page-thumbnail.selected { border-color: #3b82f6; box-shadow: 0 0 15px rgba(59, 130, 246, 0.5); }
.page-thumbnail canvas { width: 100%; height: auto; display: block; }
.page-thumbnail .page-number { position: absolute; bottom: 0; right: 0; background: rgba(0,0,0,0.8); color: white; padding: 4px 10px; font-weight: bold; font-size: 0.9rem; border-top-left-radius: 4px; }
.page-thumbnail .check-icon { position: absolute; top: 8px; right: 8px; background: #3b82f6; color: white; width: 28px; height: 28px; border-radius: 50%; display: none; align-items: center; justify-content: center; font-size: 1rem; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.3); }
.page-thumbnail.selected .check-icon { display: flex; }
.slicer-footer { padding: 1.5rem 2rem; background: #111; display: flex; gap: 1rem; align-items: center; border-top: 1px solid #333; }
.slicer-footer input { flex: 1; background: #222; color: white; border: 1px solid #444; padding: 0.8rem; border-radius: 6px; font-size: 1rem; }
</style>"""
code = code.replace("</style>", css)

# 3. Add Slicer HTML
html = """
<!-- Visual Slicer Modal -->
<div id="slicer-modal">
    <div class="slicer-header">
        <h2 style="margin: 0; color: #fff;">Visual Smart Slicer</h2>
        <button class="btn-primary" style="background: #444;" onclick="closeSlicer()">Cancel</button>
    </div>
    <div class="slicer-body" id="slicer-grid"></div>
    <div class="slicer-footer">
        <label style="font-weight: bold;">Selected Pages:</label>
        <input type="text" id="slicer-range-input" onkeyup="syncSlicerGridFromInput()" placeholder="e.g. 1-3, 5, 7">
        <button class="btn-primary" onclick="saveSlicerSelection()">Confirm Selection</button>
    </div>
</div>
</body>"""
code = code.replace("</body>", html)

# 4. Add Slicer JS Logic
js = """
let currentSlicerFileIndex = -1;
let currentSlicerPdf = null;
let slicerSelectedPages = new Set();

async function openVisualSlicer(fileIndex) {
    currentSlicerFileIndex = fileIndex;
    const f = filesData[fileIndex];
    if (f.type !== 'application/pdf') return alert("Preview only available for PDFs.");
    
    document.getElementById('slicer-modal').style.display = 'flex';
    const grid = document.getElementById('slicer-grid');
    grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 2rem; font-size: 1.2rem;">Loading High-Res PDF Previews...<br><span style="font-size:0.9rem; color:#aaa;">This may take a few seconds for large textbooks.</span></div>';
    
    // Parse current range or default to all
    let initialPages = [];
    if (f.config.pageRange && f.config.pageRange.toLowerCase() !== 'all') {
        initialPages = parsePageRange(f.config.pageRange, f.totalPages);
    } else {
        for(let i = 1; i <= f.totalPages; i++) initialPages.push(i-1);
    }
    slicerSelectedPages = new Set(initialPages);
    
    updateSlicerInput();

    // Load PDF via PDF.js
    const arrayBuffer = await f.originalFile.arrayBuffer();
    const pdfjsLib = window['pdfjs-dist/build/pdf'];
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';
    
    try {
        currentSlicerPdf = await pdfjsLib.getDocument({data: arrayBuffer}).promise;
        grid.innerHTML = ''; // clear loading
        
        // Render pages
        for(let i = 1; i <= currentSlicerPdf.numPages; i++) {
            const thumb = document.createElement('div');
            thumb.className = 'page-thumbnail ' + (slicerSelectedPages.has(i-1) ? 'selected' : '');
            thumb.onclick = () => toggleSlicerPage(i-1, thumb);
            
            const canvas = document.createElement('canvas');
            const pageNumStr = document.createElement('div');
            pageNumStr.className = 'page-number';
            pageNumStr.innerText = i;
            
            const check = document.createElement('div');
            check.className = 'check-icon';
            check.innerHTML = '✓';
            
            thumb.appendChild(canvas);
            thumb.appendChild(pageNumStr);
            thumb.appendChild(check);
            grid.appendChild(thumb);
            
            // Async render canvas
            currentSlicerPdf.getPage(i).then(page => {
                const viewport = page.getViewport({scale: 0.6});
                canvas.height = viewport.height;
                canvas.width = viewport.width;
                page.render({canvasContext: canvas.getContext('2d'), viewport: viewport});
            });
        }
    } catch (e) {
        grid.innerHTML = '<div style="color: #ef4444; padding: 2rem;">Failed to render PDF preview.</div>';
        console.error(e);
    }
}

function toggleSlicerPage(pageIndex, element) {
    if (slicerSelectedPages.has(pageIndex)) {
        slicerSelectedPages.delete(pageIndex);
        element.classList.remove('selected');
    } else {
        slicerSelectedPages.add(pageIndex);
        element.classList.add('selected');
    }
    updateSlicerInput();
}

function updateSlicerInput() {
    const input = document.getElementById('slicer-range-input');
    let sorted = Array.from(slicerSelectedPages).sort((a,b)=>a-b);
    let ranges = [];
    let i = 0;
    while(i < sorted.length) {
        let start = sorted[i];
        let end = start;
        while(i+1 < sorted.length && sorted[i+1] == end + 1) {
            end = sorted[i+1];
            i++;
        }
        if(start === end) ranges.push(start+1);
        else ranges.push((start+1) + '-' + (end+1));
        i++;
    }
    input.value = ranges.join(', ');
}

function syncSlicerGridFromInput() {
    const inputStr = document.getElementById('slicer-range-input').value;
    const total = currentSlicerPdf ? currentSlicerPdf.numPages : 100;
    const parsed = parsePageRange(inputStr, total);
    slicerSelectedPages = new Set(parsed);
    
    const grid = document.getElementById('slicer-grid');
    for(let i=0; i<grid.children.length; i++) {
        if(slicerSelectedPages.has(i)) grid.children[i].classList.add('selected');
        else grid.children[i].classList.remove('selected');
    }
}

function saveSlicerSelection() {
    const f = filesData[currentSlicerFileIndex];
    f.config.pageRange = document.getElementById('slicer-range-input').value;
    document.getElementById('slicer-modal').style.display = 'none';
    renderFileList();
    calculateTotal();
}
function closeSlicer() {
    document.getElementById('slicer-modal').style.display = 'none';
}
</script>"""
code = code.replace("</script>", js)

# 5. Update renderFileList to add the Visual Select button
old_page_row = """            ${f.type === 'application/pdf' ? `
            <div class="config-row">
                <span class="config-label">Pages</span>
                <input type="text" class="config-input" placeholder="e.g. 1-3, 5" value="${f.config.pageRange}" onchange="updateConfig(${index}, 'pageRange', this.value)">
            </div>` : ''}"""

new_page_row = """            ${f.type === 'application/pdf' ? `
            <div class="config-row">
                <span class="config-label">Pages</span>
                <div style="display:flex; gap:0.5rem; flex:1;">
                    <input type="text" style="flex:1;" class="config-input" placeholder="e.g. 1-3, 5" value="${f.config.pageRange}" onchange="updateConfig(${index}, 'pageRange', this.value)">
                    <button class="btn-primary" style="padding: 0.2rem 0.8rem; font-size: 0.85rem;" onclick="openVisualSlicer(${index})">👁️ Visual Preview</button>
                </div>
            </div>` : ''}"""

code = code.replace(old_page_row, new_page_row)

with open("index.html", "w") as f:
    f.write(code)
print("Visual Slicer successfully injected into index.html")
