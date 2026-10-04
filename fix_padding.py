with open("index.html", "r") as f:
    code = f.read()

# Add bottom padding to body to clear the fixed footer
old_body_css = "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: var(--background); color: var(--text); padding-bottom: 5rem; }"
if old_body_css in code:
    code = code.replace(old_body_css, "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: var(--background); color: var(--text); padding-bottom: 140px; }")
else:
    # If padding-bottom wasn't there
    code = code.replace("body {", "body { padding-bottom: 140px; ")

# Make absolutely sure the slicer modal has a solid white background
code = code.replace("background: rgba(0,0,0,0.95);", "background: #f8fafc;")

with open("index.html", "w") as f:
    f.write(code)

print("Footer overlap padding fixed.")
