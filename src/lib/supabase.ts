import { createClient } from '@supabase/supabase-js';

// Support both Vite (import.meta.env) and Next.js / Node (process.env)
const envUrl =
  (typeof import.meta !== 'undefined' && (import.meta as any).env?.VITE_SUPABASE_URL) ||
  (typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_SUPABASE_URL) ||
  '';

const envKey =
  (typeof import.meta !== 'undefined' && (import.meta as any).env?.VITE_SUPABASE_ANON_KEY) ||
  (typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_SUPABASE_ANON_KEY) ||
  '';

// Check if valid credentials are provided
export const isSupabaseConfigured = Boolean(
  envUrl &&
  envKey &&
  !envUrl.includes('placeholder') &&
  !envUrl.includes('your-project-id')
);

// Safe fallback URL & key to prevent module crash if Vercel env vars are not yet set
const safeUrl = isSupabaseConfigured ? envUrl : 'https://demo-roommet.supabase.co';
const safeKey = isSupabaseConfigured
  ? envKey
  : 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummy_anon_key_for_preview_mode';

export const supabase = createClient(safeUrl, safeKey, {
  auth: {
    persistSession: false,
    autoRefreshToken: false,
  },
});

export interface Hostel {
  id: string;
  name: string;
  slug: string;
  created_at: string;
}

export interface Profile {
  id: string;
  hostel_id: string;
  full_name: string;
  role: 'superadmin' | 'hostel_owner' | 'branch_manager' | 'resident';
  phone?: string;
  created_at: string;
}

export interface Property {
  id: string;
  hostel_id: string;
  name: string;
  code: string;
  total_floors: number;
  created_at: string;
}

export interface Room {
  id: string;
  hostel_id: string;
  property_id: string;
  room_number: string;
  floor_number: number;
  wing: string;
  capacity: number;
  monthly_rent: number;
  status: 'available' | 'occupied' | 'maintenance' | 'reserved';
  created_at: string;
}

export interface Resident {
  id: string;
  hostel_id: string;
  property_id: string;
  room_id?: string;
  full_name: string;
  email: string;
  phone: string;
  occupation: string;
  check_in_date: string;
  status: string;
  created_at: string;
}

export interface Payment {
  id: string;
  hostel_id: string;
  property_id: string;
  resident_id: string;
  room_id?: string;
  payment_code: string;
  amount: number;
  currency: string;
  status: 'verified' | 'pending' | 'overdue' | 'rejected';
  billing_month: string;
  receipt_url?: string;
  created_at: string;
}
