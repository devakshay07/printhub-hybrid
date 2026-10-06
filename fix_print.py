with open('print_bridge.py', 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if 'print("\\n' in line:
        new_lines.append('                    print("\\n[SUCCESS] Auto-start configured! PrintBridge will now run silently in the background every time you turn on this computer.\\n")\n')
        skip = True
    elif skip and '[SUCCESS]' in line:
        pass
    elif skip and line.strip() == '':
        skip = False
    else:
        new_lines.append(line)

with open('print_bridge.py', 'w') as f:
    f.writelines(new_lines)
