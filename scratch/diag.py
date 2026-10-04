import os
from supabase import create_client, Client

url = "https://yfnjzhftofbihvwtcsyq.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlmbmp6aGZ0b2ZiaWh2d3Rjc3lxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTAyNzI4NzksImV4cCI6MjEwNTg0ODg3OX0.hw5XMsjmgHkUvHYs03vdRSZdhHqznjdkQHp_vwKO-Lg"
supabase: Client = create_client(url, key)

print("1. Testing Order Insert...")
try:
    res = supabase.table("printhub_orders").insert({
        "customer_name": "Diagnostic", 
        "customer_email": "test@test.com", 
        "total_amount": 0, 
        "otp": "1234"
    }).execute()
    print("Order inserted:", res.data[0]['id'])
    order_id = res.data[0]['id']
except Exception as e:
    print("Order Insert Failed:", str(e))
    exit(1)

print("\n2. Testing File Upload...")
try:
    file_path = f"{order_id}/test.txt"
    res = supabase.storage.from_("print-files").upload(file_path, b"dummy data")
    print("Upload succeeded!")
except Exception as e:
    print("File Upload Failed:", str(e))
    
print("\n3. Testing Bucket Existence...")
try:
    buckets = supabase.storage.list_buckets()
    print("Buckets found:", [b.name for b in buckets])
except Exception as e:
    print("Bucket List Failed:", str(e))
