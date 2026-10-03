const Razorpay = require('razorpay');
const { createClient } = require('@supabase/supabase-js');

export default async function handler(req, res) {
    if (req.method !== 'POST') return res.status(405).send('Method Not Allowed');
    
    const { amount, shop_id } = req.body;

    if (!shop_id) return res.status(400).json({ error: "Missing shop_id" });

    try {
        const supabase = createClient(
            process.env.SUPABASE_URL || 'https://yfnjzhftofbihvwtcsyq.supabase.co',
            process.env.SUPABASE_SERVICE_ROLE_KEY
        );

        // Fetch the specific shop's Razorpay keys
        const { data: shopData, error: shopErr } = await supabase
            .from('printhub_shops')
            .select('rzp_key_id, rzp_key_secret')
            .eq('id', shop_id)
            .single();

        if (shopErr || !shopData || !shopData.rzp_key_id || !shopData.rzp_key_secret) {
            console.error("Shop Key Error:", shopErr);
            return res.status(500).json({ error: "This shop has not configured their Razorpay keys yet." });
        }

        const instance = new Razorpay({
            key_id: shopData.rzp_key_id,
            key_secret: shopData.rzp_key_secret,
        });

        const options = {
            amount: Math.round(amount * 100), // convert INR to paise
            currency: "INR",
            receipt: "order_rcptid_" + Date.now(),
        };

        const order = await instance.orders.create(options);
        
        // Return the specific shop's key_id so the frontend can load their checkout
        res.status(200).json({
            id: order.id,
            amount: order.amount,
            key_id: shopData.rzp_key_id 
        });
    } catch (error) {
        console.error("Razorpay Order Error:", error);
        res.status(500).json({ error: "Failed to create Razorpay order" });
    }
}
