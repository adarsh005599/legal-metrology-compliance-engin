-- ==============================================================================
-- Legal Metrology Compliance-Assist Engine
-- Supabase SQL Table Setup Script
-- ==============================================================================

-- 1. Create the 'scans' table
CREATE TABLE IF NOT EXISTS public.scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_ref_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    filename TEXT,
    status TEXT NOT NULL CHECK (status IN ('compliant', 'non-compliant', 'exempt', 'uncertain')),
    fields_passed INTEGER DEFAULT 0,
    fields_total INTEGER DEFAULT 5,
    field_results JSONB DEFAULT '[]'::jsonb
);

-- 2. Create indices for performance on dashboard lookups
CREATE INDEX IF NOT EXISTS idx_scans_timestamp ON public.scans (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_scans_status ON public.scans (status);
CREATE INDEX IF NOT EXISTS idx_scans_ref_id ON public.scans (scan_ref_id);

-- 3. Enable Row Level Security (RLS)
ALTER TABLE public.scans ENABLE ROW LEVEL SECURITY;

-- 4. Create policies allowing public/anon read & insert for hackathon MVP
CREATE POLICY "Allow public read access on scans" 
ON public.scans FOR SELECT 
TO anon, authenticated, service_role
USING (true);

CREATE POLICY "Allow public insert access on scans" 
ON public.scans FOR INSERT 
TO anon, authenticated, service_role
WITH CHECK (true);

COMMENT ON TABLE public.scans IS 'Records of pre-inspection packaged commodity label screenings for Legal Metrology compliance.';
