-- ==============================================================================
-- PRINTHUB SAAS - MASTER SCHEMA (OCT 2026)
-- Run this entire script in the Supabase SQL Editor of your NEW project.
-- ==============================================================================

-- 1. Create Core Tables
CREATE TABLE public.printhub_shops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    owner_uid UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    shop_name TEXT NOT NULL,
    subdomain TEXT UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    active_device_id TEXT,
    subscription_expiry TIMESTAMP WITH TIME ZONE,
    location TEXT,
    logo_url TEXT
);

CREATE TABLE public.printhub_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id UUID NOT NULL REFERENCES public.printhub_shops(id) ON DELETE CASCADE,
    price_bw NUMERIC DEFAULT 2.0,
    price_color NUMERIC DEFAULT 10.0,
    offer_banner TEXT
);

CREATE TABLE public.printhub_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    shop_id UUID NOT NULL REFERENCES public.printhub_shops(id) ON DELETE CASCADE,
    customer_name TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    total_amount NUMERIC NOT NULL,
    status TEXT DEFAULT 'Pending',
    otp TEXT NOT NULL,
    otp_verified BOOLEAN DEFAULT FALSE,
    notes TEXT
);

CREATE TABLE public.printhub_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    order_id UUID NOT NULL REFERENCES public.printhub_orders(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    pages INTEGER NOT NULL,
    copies INTEGER DEFAULT 1,
    color_mode TEXT DEFAULT 'bw',
    page_range TEXT
);

-- ==============================================================================
-- 2. Storage Bucket
-- ==============================================================================
INSERT INTO storage.buckets (id, name, public) 
VALUES ('print-files', 'print-files', false)
ON CONFLICT (id) DO NOTHING;

-- ==============================================================================
-- 3. Enable Row Level Security (RLS)
-- ==============================================================================
ALTER TABLE public.printhub_shops ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.printhub_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.printhub_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.printhub_files ENABLE ROW LEVEL SECURITY;

-- ==============================================================================
-- 4. Strict Security Policies
-- ==============================================================================

-- Shops: Anyone can view (for storefronts), only owner can edit
CREATE POLICY "Public Shop Select" ON public.printhub_shops FOR SELECT USING (true);
CREATE POLICY "Owner Shop Update" ON public.printhub_shops FOR UPDATE USING (auth.uid() = owner_uid);

-- Settings: Anyone can view (for frontend calculations), only owner can edit
CREATE POLICY "Public Settings Select" ON public.printhub_settings FOR SELECT USING (true);
CREATE POLICY "Owner Settings Update" ON public.printhub_settings FOR UPDATE USING (
    auth.uid() IN (SELECT owner_uid FROM public.printhub_shops WHERE id = shop_id)
);
CREATE POLICY "Owner Settings Insert" ON public.printhub_settings FOR INSERT WITH CHECK (
    auth.uid() IN (SELECT owner_uid FROM public.printhub_shops WHERE id = shop_id)
);

-- Orders: Public can insert (place orders), ONLY shop agent/owner can select/update
CREATE POLICY "Public Order Insert" ON public.printhub_orders FOR INSERT WITH CHECK (true);
CREATE POLICY "Agent Order Select" ON public.printhub_orders FOR SELECT USING (
    auth.uid() IN (SELECT owner_uid FROM public.printhub_shops WHERE id = shop_id)
);
CREATE POLICY "Agent Order Update" ON public.printhub_orders FOR UPDATE USING (
    auth.uid() IN (SELECT owner_uid FROM public.printhub_shops WHERE id = shop_id)
);

-- Files: Public can insert, ONLY shop agent/owner can select
CREATE POLICY "Public File Insert" ON public.printhub_files FOR INSERT WITH CHECK (true);
CREATE POLICY "Agent File Select" ON public.printhub_files FOR SELECT USING (
    auth.uid() IN (
        SELECT s.owner_uid 
        FROM public.printhub_shops s 
        JOIN public.printhub_orders o ON s.id = o.shop_id 
        WHERE o.id = order_id
    )
);

-- Storage Policies: Public can upload files, ONLY authenticated agents can read them
CREATE POLICY "Public Uploads" ON storage.objects FOR INSERT WITH CHECK (
    bucket_id = 'print-files'
);
CREATE POLICY "Agent Reads" ON storage.objects FOR SELECT USING (
    bucket_id = 'print-files' AND auth.role() = 'authenticated'
);
