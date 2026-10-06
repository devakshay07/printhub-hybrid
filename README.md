# PrintHub (Hybrid Architecture)

PrintHub is a zero-trace, fully-decoupled SaaS platform for print shops.

## Architecture

1. **Customer Storefront (`index.html`)**: A lightweight, CDN-powered web app that allows customers to upload PDFs, calculates pricing, generates secure PINs, and pushes jobs to the cloud. Hosted on Vercel.
2. **Shop Dashboard (`dashboard.html`)**: A secure, real-time agent dashboard where shop owners can view incoming orders, verify PINs, and manage their shop. Hosted on Vercel.
3. **Print Bridge (`print_bridge.py` / `PrintBridge.exe`)**: A headless local agent that runs on the physical print shop computer. It authenticates with the cloud, downloads paid/verified print jobs, streams them directly to the local OS printer spooler, and securely wipes the files from the disk.

## Setup Instructions

1. **Database**: Run `printhub_schema.sql` in your Supabase SQL Editor.
2. **Frontend**: Deploy the repository to Vercel. (No build step required).
3. **Local Print Agent**: Download the `PrintBridge.exe` from GitHub Actions, or run `python print_bridge.py`. Enter your Shop Email and Password to authenticate the node.

## Zero-Trace Privacy Guarantee
All files are streamed directly from Supabase to the local print spooler and are securely deleted from the local disk the moment the print job is successfully queued.
