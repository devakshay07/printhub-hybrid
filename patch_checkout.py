import re

with open("index.html", "r") as f:
    code = f.read()

# Replace the handleCheckout logic
old_logic = """if (isOnline) {
        // MOCK RAZORPAY INTEGRATION FOR MVP
        var options = {
            "key": "YOUR_KEY_ID", 
            "amount": totalAmount * 100, 
            "currency": "INR",
            "name": "PRINTHub Fast-Pass",
            "description": "Print Order",
            "handler": function (response) {
                // If payment succeeds, submit order with the payment ID
                submitOrder(response.razorpay_payment_id);
            },
            "theme": { "color": "#FF9B51" }
        };
        var rzp1 = new Razorpay(options);
        rzp1.open();
    } else {
        submitOrder(null);
    }"""

new_logic = """if (isOnline) {
        try {
            overlay.style.display = 'flex';
            overlayTitle.textContent = 'Connecting to Bank...';
            overlayDesc.textContent = 'Generating secure payment gateway...';

            // 1. Get Razorpay Order ID from Backend
            const rzpRes = await fetch('/api/create-order', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount: totalAmount })
            });
            const rzpOrder = await rzpRes.json();
            
            if (rzpOrder.error) {
                throw new Error(rzpOrder.error);
            }

            overlay.style.display = 'none';

            // 2. Open Razorpay UI
            var options = {
                "key": rzpOrder.key_id, 
                "amount": rzpOrder.amount, 
                "currency": "INR",
                "name": currentShopName,
                "description": "Print Order",
                "order_id": rzpOrder.id,
                "handler": async function (response) {
                    overlay.style.display = 'flex';
                    overlayTitle.textContent = 'Verifying Payment...';
                    overlayDesc.textContent = 'Cryptographically checking signature...';

                    // 3. Submit Order to Supabase first (as Pending)
                    const otpCode = Math.floor(10 + Math.random() * 90).toString() + (phone.length >= 2 ? phone.slice(-2) : "00");
                    const { data: orderData, error: orderErr } = await supabaseClient
                        .from('printhub_orders')
                        .insert([{ 
                            shop_id: currentShopId,
                            customer_name: name, 
                            customer_email: email, 
                            customer_phone: phone, 
                            notes: notes, 
                            total_amount: totalAmount, 
                            otp: otpCode,
                            status: 'Pending' // Always pending until verified
                        }])
                        .select();
                        
                    if (orderErr) {
                        alert("Error saving order. Contact shop.");
                        overlay.style.display = 'none';
                        return;
                    }
                    
                    const supabaseOrderId = orderData[0].id;

                    // 4. Verify Payment with Backend
                    const verifyRes = await fetch('/api/verify-payment', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            razorpay_order_id: response.razorpay_order_id,
                            razorpay_payment_id: response.razorpay_payment_id,
                            razorpay_signature: response.razorpay_signature,
                            supabase_order_id: supabaseOrderId
                        })
                    });
                    
                    const verifyData = await verifyRes.json();
                    
                    if (verifyData.success) {
                        // 5. Upload files now that payment is locked in
                        overlayTitle.textContent = 'Payment Verified!';
                        overlayDesc.textContent = 'Uploading files to cloud...';
                        await processAndUploadFiles(supabaseOrderId, otpCode);
                    } else {
                        alert("Payment verification failed! " + (verifyData.error || ""));
                        overlay.style.display = 'none';
                    }
                },
                "theme": { "color": "#111" }
            };
            var rzp1 = new Razorpay(options);
            rzp1.open();
        } catch (e) {
            console.error(e);
            alert("Payment gateway error: " + e.message);
            overlay.style.display = 'none';
        }
    } else {
        // Pay at shop route (same as before)
        const otpCode = Math.floor(10 + Math.random() * 90).toString() + (phone.length >= 2 ? phone.slice(-2) : "00");
        const { data: orderData, error: orderErr } = await supabaseClient
            .from('printhub_orders')
            .insert([{ 
                shop_id: currentShopId,
                customer_name: name, 
                customer_email: email, 
                customer_phone: phone, 
                notes: notes, 
                total_amount: totalAmount, 
                otp: otpCode,
                status: 'Pending'
            }])
            .select();
            
        if (orderErr) {
            alert("Error saving order: " + orderErr.message);
            return;
        }
        await processAndUploadFiles(orderData[0].id, otpCode);
    }"""

# Now we need to modify submitOrder to be processAndUploadFiles
old_submitOrder = """async function submitOrder(paymentId) {
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const phone = document.getElementById('phone').value;
    const notes = document.getElementById('notes').value;

    const overlay = document.getElementById('loadingOverlay');
    const overlayTitle = document.getElementById('overlayTitle');
    const overlayDesc = document.getElementById('overlayDesc');

    overlay.style.display = 'flex';

    try {
        overlayTitle.textContent = 'Preparing Files...';
        overlayDesc.textContent = 'Generating secure PIN...';
        
        // Prevent OTP collision by combining random digits with phone number
        const randomPart = Math.floor(10 + Math.random() * 90).toString();
        const phoneSuffix = phone.length >= 2 ? phone.slice(-2) : "00";
        const otpCode = randomPart + phoneSuffix;
        
        // Determine status based on payment
        const initialStatus = paymentId ? 'Paid' : 'Pending';

        // 1. Create Order
        const { data: orderData, error: orderErr } = await supabaseClient
            .from('printhub_orders')
            .insert([{ 
                shop_id: currentShopId,
                customer_name: name, 
                customer_email: email, 
                customer_phone: phone, 
                notes: paymentId ? `[PAID ONLINE: ${paymentId}] ${notes}` : notes, 
                total_amount: totalAmount, 
                otp: otpCode,
                status: initialStatus
            }])
            .select();

        if (orderErr) throw orderErr;
        const orderId = orderData[0].id;"""

new_submitOrder = """async function processAndUploadFiles(orderId, otpCode) {
    const overlay = document.getElementById('loadingOverlay');
    const overlayTitle = document.getElementById('overlayTitle');
    const overlayDesc = document.getElementById('overlayDesc');

    try {
        overlayTitle.textContent = 'Uploading...';"""

code = code.replace(old_logic, new_logic)
code = code.replace(old_submitOrder, new_submitOrder)

with open("index.html", "w") as f:
    f.write(code)
print("Checkout logic updated!")
