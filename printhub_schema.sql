-- ==============================================================================
-- PRINTHUB SAAS - COMPLETE MASTER SCHEMA & PROVISIONING SUITE (OCT 2026)
-- Run this entire script in the Supabase SQL Editor.
-- Sets up: Extensions, Core Tables, Storage, RLS, and Stored Procedures.
-- ==============================================================================

-- 0. Required Extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================================================================
-- 1. Create Core Tables
-- ==============================================================================

CREATE TABLE IF NOT EXISTS public.printhub_shops (
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

CREATE TABLE IF NOT EXISTS public.printhub_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id UUID NOT NULL REFERENCES public.printhub_shops(id) ON DELETE CASCADE,
    price_bw NUMERIC DEFAULT 2.0,
    price_color NUMERIC DEFAULT 10.0,
    offer_banner TEXT
);

CREATE TABLE IF NOT EXISTS public.printhub_orders (
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

CREATE TABLE IF NOT EXISTS public.printhub_files (
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
-- 4. Strict Security Policies (Idempotent)
-- ==============================================================================

-- Shops
DO $$ BEGIN
    DROP POLICY IF EXISTS "Public Shop Select" ON public.printhub_shops;
    DROP POLICY IF EXISTS "Owner Shop Update" ON public.printhub_shops;
    DROP POLICY IF EXISTS "Service Role All Shops" ON public.printhub_shops;
END $$;
CREATE POLICY "Public Shop Select" ON public.printhub_shops FOR SELECT USING (true);
CREATE POLICY "Owner Shop Update" ON public.printhub_shops FOR UPDATE USING (auth.uid() = owner_uid);

-- Settings
DO $$ BEGIN
    DROP POLICY IF EXISTS "Public Settings Select" ON public.printhub_settings;
    DROP POLICY IF EXISTS "Owner Settings Update" ON public.printhub_settings;
    DROP POLICY IF EXISTS "Owner Settings Insert" ON public.printhub_settings;
END $$;
CREATE POLICY "Public Settings Select" ON public.printhub_settings FOR SELECT USING (true);
CREATE POLICY "Owner Settings Update" ON public.printhub_settings FOR UPDATE USING (
    auth.uid() IN (SELECT owner_uid FROM public.printhub_shops WHERE id = shop_id)
);
CREATE POLICY "Owner Settings Insert" ON public.printhub_settings FOR INSERT WITH CHECK (
    auth.uid() IN (SELECT owner_uid FROM public.printhub_shops WHERE id = shop_id)
);

-- Orders
DO $$ BEGIN
    DROP POLICY IF EXISTS "Public Order Insert" ON public.printhub_orders;
    DROP POLICY IF EXISTS "Agent Order Select" ON public.printhub_orders;
    DROP POLICY IF EXISTS "Agent Order Update" ON public.printhub_orders;
END $$;
CREATE POLICY "Public Order Insert" ON public.printhub_orders FOR INSERT WITH CHECK (true);
CREATE POLICY "Agent Order Select" ON public.printhub_orders FOR SELECT USING (
    auth.uid() IN (SELECT owner_uid FROM public.printhub_shops WHERE id = shop_id)
);
CREATE POLICY "Agent Order Update" ON public.printhub_orders FOR UPDATE USING (
    auth.uid() IN (SELECT owner_uid FROM public.printhub_shops WHERE id = shop_id)
);

-- Files
DO $$ BEGIN
    DROP POLICY IF EXISTS "Public File Insert" ON public.printhub_files;
    DROP POLICY IF EXISTS "Agent File Select" ON public.printhub_files;
END $$;
CREATE POLICY "Public File Insert" ON public.printhub_files FOR INSERT WITH CHECK (true);
CREATE POLICY "Agent File Select" ON public.printhub_files FOR SELECT USING (
    auth.uid() IN (
        SELECT s.owner_uid 
        FROM public.printhub_shops s 
        JOIN public.printhub_orders o ON s.id = o.shop_id 
        WHERE o.id = order_id
    )
);

-- Storage Policies
DO $$ BEGIN
    DROP POLICY IF EXISTS "Public Uploads" ON storage.objects;
    DROP POLICY IF EXISTS "Agent Reads" ON storage.objects;
END $$;
CREATE POLICY "Public Uploads" ON storage.objects FOR INSERT WITH CHECK (
    bucket_id = 'print-files'
);
CREATE POLICY "Agent Reads" ON storage.objects FOR SELECT USING (
    bucket_id = 'print-files' AND auth.role() = 'authenticated'
);

-- ==============================================================================
-- 5. Stored Procedure: Atomic Tenant Provisioning
-- ==============================================================================
-- Creates Auth User, Shop Registry, and Pricing Matrix in a single SQL transaction.
-- Can be called via Supabase SQL Editor OR via the Superadmin Dashboard (RPC).

CREATE OR REPLACE FUNCTION public.printhub_add_shop(
    p_owner_email TEXT,
    p_owner_password TEXT,
    p_shop_name TEXT,
    p_subdomain TEXT,
    p_location TEXT DEFAULT 'HQ',
    p_days INTEGER DEFAULT 30,
    p_price_bw NUMERIC DEFAULT 2.0,
    p_price_color NUMERIC DEFAULT 10.0
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, auth, extensions
AS $$
DECLARE
    v_user_id UUID;
    v_shop_id UUID;
    v_encrypted_pw TEXT;
    v_clean_subdomain TEXT;
BEGIN
    v_clean_subdomain := lower(trim(p_subdomain));

    -- Validate Subdomain
    IF v_clean_subdomain = '' THEN
        RAISE EXCEPTION 'Subdomain slug cannot be empty.';
    END IF;

    IF EXISTS (SELECT 1 FROM public.printhub_shops WHERE subdomain = v_clean_subdomain) THEN
        RAISE EXCEPTION 'Subdomain "%" is already registered.', v_clean_subdomain;
    END IF;

    -- 1. Create or resolve User in auth.users
    SELECT id INTO v_user_id FROM auth.users WHERE email = lower(trim(p_owner_email));

    IF v_user_id IS NULL THEN
        v_user_id := gen_random_uuid();
        v_encrypted_pw := crypt(p_owner_password, gen_salt('bf'));

        INSERT INTO auth.users (
            instance_id,
            id,
            aud,
            role,
            email,
            encrypted_password,
            email_confirmed_at,
            raw_app_meta_data,
            raw_user_meta_data,
            created_at,
            updated_at
        ) VALUES (
            '00000000-0000-0000-0000-000000000000',
            v_user_id,
            'authenticated',
            'authenticated',
            lower(trim(p_owner_email)),
            v_encrypted_pw,
            NOW(),
            '{"provider":"email","providers":["email"]}',
            '{}',
            NOW(),
            NOW()
        );

        INSERT INTO auth.identities (
            id,
            user_id,
            identity_data,
            provider,
            last_sign_in_at,
            created_at,
            updated_at
        ) VALUES (
            gen_random_uuid(),
            v_user_id,
            format('{"sub":"%s","email":"%s"}', v_user_id, lower(trim(p_owner_email)))::jsonb,
            'email',
            NOW(),
            NOW(),
            NOW()
        );
    END IF;

    -- 2. Insert into printhub_shops
    INSERT INTO public.printhub_shops (
        owner_uid,
        shop_name,
        subdomain,
        location,
        is_active,
        subscription_expiry
    ) VALUES (
        v_user_id,
        p_shop_name,
        v_clean_subdomain,
        p_location,
        true,
        NOW() + (p_days || ' days')::INTERVAL
    )
    RETURNING id INTO v_shop_id;

    -- 3. Seed default pricing in printhub_settings
    INSERT INTO public.printhub_settings (
        shop_id,
        price_bw,
        price_color,
        offer_banner
    ) VALUES (
        v_shop_id,
        p_price_bw,
        p_price_color,
        ''
    );

    RETURN jsonb_build_object(
        'success', true,
        'user_id', v_user_id,
        'shop_id', v_shop_id,
        'subdomain', v_clean_subdomain,
        'email', lower(trim(p_owner_email)),
        'message', 'Shop provisioned successfully'
    );
END;
$$;

-- Permissions
GRANT EXECUTE ON FUNCTION public.printhub_add_shop TO service_role;
GRANT EXECUTE ON FUNCTION public.printhub_add_shop TO postgres;
GRANT EXECUTE ON FUNCTION public.printhub_add_shop TO authenticated;
