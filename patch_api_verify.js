const fs = require('fs');

const code = `const crypto = require('crypto');
const { createClient } = require('@supabase/supabase-js');

export default async function handler(req, res) {
    if (req.method !== 'POST') return res.status(405).send('Method Not Allowed');

    const { razorpay_order_id, razorpay_payment_id, razorpay_signature, supabase_order_id, shop_id } = req.body;

    if (!shop_id || !supabase_order_id) return res.status(400).json({ error: "Missing required fields" });

    try {
        const supabase = createClient(
            process.env.SUPABASE_URL || 'https://yfnjzhftofbihvwtcsyq.supabase.co',
            process.env.SUPABASE_SERVICE_ROLE_KEY
        );

        // Fetch the specific shop's Razorpay secret
        const { data: shopData, error: shopErr } = await supabase
            .from('printhub_shops')
            .select('rzp_key_secret')
            .eq('id', shop_id)
            .single();

        if (shopErr || !shopData || !shopData.rzp_key_secret) {
            return res.status(500).json({ success: false, error: "Shop payment configuration missing." });
        }

        const secret = shopData.rzp_key_secret;

        // 1. Verify Cryptographic Signature
        const shasum = crypto.createHmac('sha256', secret);
        shasum.update(razorpay_order_id + "|" + razorpay_payment_id);
        const digest = shasum.digest('hex');

        if (digest !== razorpay_signature) {
            return res.status(400).json({ success: false, error: "Invalid signature. Payment rejected." });
        }

        // 2. Signature is valid. Upgrade the order status in Supabase securely.
        const { error } = await supabase
            .from('printhub_orders')
            .update({ status: 'Paid', notes: \`[PAID ONLINE: \${razorpay_payment_id}]\` })
            .eq('id', supabase_order_id);
            
        if (error) {
            console.error("Supabase Update Error:", error);
            return res.status(500).json({ success: false, error: "Failed to update database, but payment was verified." });
        }
        
        return res.status(200).json({ success: true });
    } catch (e) {
        console.error("Verification Error:", e);
        return res.status(500).json({ success: false, error: "Internal server error during verification" });
    }
}
`;

fs.writeFileSync('api/verify-payment.js', code);
console.log("api/verify-payment.js updated for BYOK multi-tenancy");
