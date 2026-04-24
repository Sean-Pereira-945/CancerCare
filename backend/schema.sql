-- ==========================================
-- CancerCare AI — PostgreSQL Schema
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

-- Medication logs
CREATE TABLE IF NOT EXISTS medication_logs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  medication_id UUID REFERENCES medications(id) ON DELETE CASCADE,
  taken_at TIMESTAMPTZ DEFAULT NOW(),
  status TEXT DEFAULT 'taken'
);

