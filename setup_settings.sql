-- 1. Create the settings table
CREATE TABLE IF NOT EXISTS public.printhub_settings (
    id INTEGER PRIMARY KEY DEFAULT 1,
    is_accepting_orders BOOLEAN DEFAULT TRUE,
    price_bw NUMERIC DEFAULT 2.0,
    price_color NUMERIC DEFAULT 10.0
);

-- 2. Insert the default row
INSERT INTO public.printhub_settings (id, is_accepting_orders, price_bw, price_color) 
VALUES (1, true, 2.0, 10.0) 
ON CONFLICT (id) DO NOTHING;

-- 3. Enable RLS and allow public read/update (since it's an MVP)
ALTER TABLE public.printhub_settings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow public read on printhub_settings" ON public.printhub_settings FOR SELECT TO public USING (true);
CREATE POLICY "Allow public update on printhub_settings" ON public.printhub_settings FOR UPDATE TO public USING (true);
