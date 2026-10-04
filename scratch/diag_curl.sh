URL="https://yfnjzhftofbihvwtcsyq.supabase.co"
KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlmbmp6aGZ0b2ZiaWh2d3Rjc3lxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTAyNzI4NzksImV4cCI6MjEwNTg0ODg3OX0.hw5XMsjmgHkUvHYs03vdRSZdhHqznjdkQHp_vwKO-Lg"

echo "1. Checking Buckets..."
curl -s -H "apikey: $KEY" -H "Authorization: Bearer $KEY" "$URL/storage/v1/bucket" | python3 -m json.tool

echo -e "\n2. Testing Order Insert..."
curl -s -X POST -H "apikey: $KEY" -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" -H "Prefer: return=representation" -d '{"customer_name":"Diag","customer_email":"a@b.com","total_amount":0,"otp":"1234"}' "$URL/rest/v1/printhub_orders" | python3 -m json.tool

echo -e "\n3. Testing Storage Upload..."
# create a dummy file
echo "dummy file" > scratch/dummy.txt
curl -s -X POST -H "apikey: $KEY" -H "Authorization: Bearer $KEY" -H "Content-Type: text/plain" --data-binary "@scratch/dummy.txt" "$URL/storage/v1/object/print-files/diag_test/dummy.txt" | python3 -m json.tool
