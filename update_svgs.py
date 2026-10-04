def replace_in_file(filepath, replacements):
    with open(filepath, "r") as f:
        content = f.read()
    for old, new in replacements.items():
        content = content.replace(old, new)
    with open(filepath, "w") as f:
        f.write(content)

replace_in_file("templates/admin.html", {
    'data-lucide="activity"': 'data-lucide="list-ordered"',
    'data-lucide="radio"': 'data-lucide="inbox"'
})

replace_in_file("templates/settings.html", {
    'data-lucide="cpu"': 'data-lucide="printer"',
    'data-lucide="cloud"': 'data-lucide="globe"',
    'data-lucide="sliders"': 'data-lucide="settings"'
})

replace_in_file("templates/login.html", {
    'data-lucide="shield-check"': 'data-lucide="lock-keyhole"',
    'data-lucide="cpu"': 'data-lucide="hard-drive"'
})

replace_in_file("templates/locked.html", {
    'data-lucide="cpu"': 'data-lucide="hard-drive"'
})

replace_in_file("superadmin.html", {
    'data-lucide="database"': 'data-lucide="layout-dashboard"'
})

print("SVGs updated to relevant business context.")
