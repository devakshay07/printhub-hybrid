-- Run this in your Supabase SQL Editor

-- 1. Create the orders table
CREATE TABLE IF NOT EXISTS public.orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_name TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    customer_phone TEXT,
    notes TEXT,
    total_amount NUMERIC NOT NULL,
    status TEXT DEFAULT 'Pending', -- Pending, Paid, Printed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create the order_files table (to track config per file)
CREATE TABLE IF NOT EXISTS public.order_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES public.orders(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    pages INTEGER NOT NULL,
    copies INTEGER DEFAULT 1,
    paper_type TEXT DEFAULT 'Plain 75gsm',
    color_mode TEXT DEFAULT 'bw', -- bw or color
    sides TEXT DEFAULT 'single', -- single or double
    page_range TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Set up Storage Bucket for print-files
INSERT INTO storage.buckets (id, name, public) 
VALUES ('print-files', 'print-files', true)
ON CONFLICT (id) DO NOTHING;

-- 4. Set up permissive Row Level Security (RLS) for hacking speed
-- WARNING: In a production app, lock this down so users can only read their own files.
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.order_files ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public inserts on orders" 
ON public.orders FOR INSERT TO public WITH CHECK (true);

CREATE POLICY "Allow public read on orders" 
ON public.orders FOR SELECT TO public USING (true);

CREATE POLICY "Allow public update on orders" 
ON public.orders FOR UPDATE TO public USING (true);

CREATE POLICY "Allow public inserts on order_files" 
ON public.order_files FOR INSERT TO public WITH CHECK (true);

CREATE POLICY "Allow public read on order_files" 
ON public.order_files FOR SELECT TO public USING (true);

-- Storage Policies
CREATE POLICY "Allow public uploads to print-files"
ON storage.objects FOR INSERT TO public WITH CHECK (bucket_id = 'print-files');

CREATE POLICY "Allow public read on print-files"
ON storage.objects FOR SELECT TO public USING (bucket_id = 'print-files');
