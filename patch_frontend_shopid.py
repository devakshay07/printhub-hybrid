with open("index.html", "r") as f:
    code = f.read()

# Update create-order call
code = code.replace(
    "body: JSON.stringify({ amount: totalAmount })",
    "body: JSON.stringify({ amount: totalAmount, shop_id: currentShopId })"
)

# Update verify-payment call
old_verify = """body: JSON.stringify({
                            razorpay_order_id: response.razorpay_order_id,
                            razorpay_payment_id: response.razorpay_payment_id,
                            razorpay_signature: response.razorpay_signature,
                            supabase_order_id: supabaseOrderId
                        })"""

new_verify = """body: JSON.stringify({
                            razorpay_order_id: response.razorpay_order_id,
                            razorpay_payment_id: response.razorpay_payment_id,
                            razorpay_signature: response.razorpay_signature,
                            supabase_order_id: supabaseOrderId,
                            shop_id: currentShopId
                        })"""

code = code.replace(old_verify, new_verify)

with open("index.html", "w") as f:
    f.write(code)
print("Frontend updated to pass shop_id to backend APIs")
