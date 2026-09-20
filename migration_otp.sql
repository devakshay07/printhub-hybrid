-- Run this in your Supabase SQL Editor to apply the Anti-Ghosting Protocol

ALTER TABLE public.orders 
ADD COLUMN otp TEXT;

ALTER TABLE public.orders 
ADD COLUMN otp_verified BOOLEAN DEFAULT FALSE;
