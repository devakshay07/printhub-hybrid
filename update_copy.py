import os

def replace_in_file(filepath, replacements):
    with open(filepath, "r") as f:
        content = f.read()
    for old, new in replacements.items():
        content = content.replace(old, new)
    with open(filepath, "w") as f:
        f.write(content)

# 1. Update superadmin.html
replace_in_file("superadmin.html", {
    "God Mode": "Superadmin Access",
    "SaaS Throne": "Administration Panel",
    "The Throne": "Platform Administration",
    "SaaS Global Overview": "Tenant Management Overview",
    "Killswitch": "Suspend",
    "Restore": "Activate"
})

# 2. Update base.html
replace_in_file("templates/base.html", {
    "PrintHub Enclave": "PrintHub Agent",
    ">Feed<": ">Orders<",
    ">Config<": ">Settings<"
})

# 3. Update login.html
replace_in_file("templates/login.html", {
    "Enclave Authentication": "Terminal Authentication",
    "Connect this machine to your PrintHub network": "Log in to connect this device to your cloud workspace.",
    "Establish Uplink": "Secure Login"
})

# 4. Update locked.html
replace_in_file("templates/locked.html", {
    "Hardware Lock Engaged": "Device Access Restricted",
    "This computer has been disconnected from the PrintHub network": "This device's hardware signature is no longer authorized",
    "Re-Authenticate Device": "Re-Authenticate"
})

# 5. Update settings.html
replace_in_file("templates/settings.html", {
    "Hardware & Cloud Config": "Agent Configuration",
    "Manage physical relays and Vercel synchronizations.": "Manage physical printers and cloud preferences.",
    "Configuration synced successfully across all edge nodes.": "Configuration saved and synced successfully.",
    "SaaS Profile (Vercel Edge)": "Cloud Profile",
    "These settings sync directly to your live Vercel storefront in real-time.": "These settings sync directly to your public web link in real-time.",
    "Local Hardware Relays": "Local Printer Routing",
    "Map incoming payload color modes to specific physical hardware printers on this machine.": "Map incoming print jobs to specific physical printers connected to this computer.",
    "Relay Destination": "Printer Destination",
    "Compile & Sync Settings": "Save Settings"
})

# 6. Update admin.html
replace_in_file("templates/admin.html", {
    "Fatal System Lock": "Subscription Expired",
    "All hardware relays and print jobs are frozen.": "All print jobs are currently paused.",
    "Hardware Uplink Secure": "System Online",
    "Live Terminal Feed": "Live Order Feed",
    "Awaiting Transmissions": "Awaiting Orders",
    "Listening to the cloud...": "Waiting for incoming customer orders...",
    "Cash Received": "Mark as Paid",
    "Archive Job": "Mark as Complete",
    "Encrypted Payload": "Secure Document",
    "Ask the customer for their 4-digit PIN to decrypt files.": "Enter the customer's 4-digit PIN to unlock their files.",
    "Decrypt": "Unlock",
    "Payload Decrypted": "Files Unlocked",
    "Dispatch": "Print Document"
})

# 7. Update index.html
replace_in_file("index.html", {
    "Initializing Secure Terminal...": "Connecting to print station...",
    "Initializing secure terminal.": "Connecting to print station...",
    "Preparing Secure Transfer...": "Preparing files...",
    "Generating end-to-end PIN...": "Generating secure PIN...",
    "Authenticating Request...": "Processing request...",
    "Encrypting and transferring...": "Transferring securely...",
    "Secure Transfer": "File Upload",
    "Encrypted Payload": "Secure Document"
})

print("Copywriting enterprise sweep complete.")
