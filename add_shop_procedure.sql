-- ==============================================================================
-- PRINTHUB SAAS - ADD NEW SHOP SQL STORED PROCEDURE (OCT 2026)
-- Run this in your Supabase SQL Editor once.
-- Allows single-call tenant creation from the SQL Editor or Superadmin Console.
-- ==============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

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
AS $$
DECLARE
    v_user_id UUID;
    v_shop_id UUID;
    v_encrypted_pw TEXT;
    v_clean_subdomain TEXT;
BEGIN
    v_clean_subdomain := lower(trim(p_subdomain));

    -- Check for duplicate subdomain
    IF EXISTS (SELECT 1 FROM public.printhub_shops WHERE subdomain = v_clean_subdomain) THEN
        RAISE EXCEPTION 'Subdomain "%" is already taken by another shop.', v_clean_subdomain;
    END IF;

    -- Check if auth user already exists in auth.users
    SELECT id INTO v_user_id FROM auth.users WHERE email = lower(trim(p_owner_email));

    IF v_user_id IS NULL THEN
        -- Generate new user in auth.users
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

    -- Insert new tenant shop
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

    -- Seed default rates
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
        'email', p_owner_email,
        'message', 'Shop provisioned successfully'
    );
END;
$$;

-- Grant execution to service_role and postgres
GRANT EXECUTE ON FUNCTION public.printhub_add_shop TO service_role;
GRANT EXECUTE ON FUNCTION public.printhub_add_shop TO postgres;

-- Example of direct SQL usage:
-- SELECT public.printhub_add_shop('shop2@printhub.local', 'Password123!', 'Campus Xerox Hub', 'campus', 'Block B', 30, 2.0, 10.0);
