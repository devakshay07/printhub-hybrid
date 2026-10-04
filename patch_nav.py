import glob

for filename in ['templates/admin.html', 'templates/settings.html']:
    with open(filename, 'r') as f:
        code = f.read()
    
    if "logout" not in code:
        code = code.replace(
            '<div style="max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center;">',
            '<div style="max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center;">\n            <div style="flex:1;">'
        )
        code = code.replace(
            '</div>\n        </div>\n    </nav>',
            '</div>\n            <a href="/logout" style="color: #ef4444; text-decoration: none; font-weight: bold; font-family: monospace;">[ LOGOUT / DISCONNECT ]</a>\n        </div>\n    </nav>'
        )
        with open(filename, 'w') as f:
            f.write(code)

print("Logout buttons added to UI.")
