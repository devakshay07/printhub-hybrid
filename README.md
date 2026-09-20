# PRINTHub - Cloud-to-Ground Print Service

A hybrid architecture for a modern printing shop. Accepts orders and files globally via a Vercel-hosted frontend, stores them securely in Supabase, and uses a local Python agent to route print jobs directly to physical printers.

## Architecture

1. **Frontend (`index.html`)**: Deployed on Vercel or any static host. Users upload PDFs and images, configure print settings (Copies, Color, Duplex, Page Ranges), and submit. Local PDF slicing is handled via `pdf-lib` to minimize upload bandwidth.
2. **Database (Supabase)**: Stores the `orders`, `order_files`, and actual file payloads in a secure `print-files` bucket.
3. **Shop Agent (`shop_agent.py`)**: Runs locally at the print shop on a Linux/macOS machine. Polls Supabase for new orders, provides a local dashboard to manage jobs, and uses the `lp` command to dynamically send configured files to the local printer.

## Setup Instructions

### 1. Supabase Setup
- Create a new Supabase project.
- Open the SQL Editor and paste the contents of `schema.sql` to generate your tables, policies, and storage buckets.

### 2. Frontend Setup
- Open `index.html`.
- Replace `YOUR_SUPABASE_URL` and `YOUR_SUPABASE_ANON_KEY` with your project's keys.
- Deploy the folder to Vercel/Netlify/GitHub Pages.

### 3. Local Shop Agent
- Install dependencies: `pip install -r requirements.txt`
- Export your Supabase keys to your environment:
  ```bash
  export SUPABASE_URL="your-url"
  export SUPABASE_ANON_KEY="your-key"
  ```
- Run the agent: `python3 shop_agent.py`
- Open `http://localhost:5000` to access the shopkeeper dashboard.
