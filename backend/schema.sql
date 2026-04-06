-- ==========================================
-- CancerCare AI — Supabase SQL Schema
-- Run this in the Supabase SQL Editor
-- ==========================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  cancer_type TEXT,
  role TEXT DEFAULT 'patient',
  caregiver_for UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Diet plans
CREATE TABLE IF NOT EXISTS diet_plans (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  plan_data JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Meal logs
CREATE TABLE IF NOT EXISTS meal_logs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  meal_type TEXT,
  food_items JSONB,
  calories INTEGER,
  adhered_to_plan BOOLEAN DEFAULT true,
  logged_at TIMESTAMPTZ DEFAULT NOW()
);

-- Medications
CREATE TABLE IF NOT EXISTS medications (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  dosage TEXT,
  frequency TEXT,
  times TEXT[],
  start_date DATE,
  notes TEXT,
  active BOOLEAN DEFAULT true
);

-- Row Level Security (patients see only their own data)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE diet_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE meal_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE medications ENABLE ROW LEVEL SECURITY;

-- RLS Policies (allow all operations via service role / anon key for now)
CREATE POLICY "Allow all" ON users FOR ALL USING (true);
CREATE POLICY "Allow all" ON diet_plans FOR ALL USING (true);
CREATE POLICY "Allow all" ON meal_logs FOR ALL USING (true);
CREATE POLICY "Allow all" ON medications FOR ALL USING (true);
