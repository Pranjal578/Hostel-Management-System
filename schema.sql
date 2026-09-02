-- =========================================================================
-- ROOMMET — Multi-Tenant PostgreSQL Schema & RLS Policies (Supabase)
-- Run this directly in the Supabase SQL Editor.
-- =========================================================================

-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- 1. HOSTEL TENANTS (Multi-Tenant Root Accounts)
create table if not exists hostels (
    id uuid primary key default uuid_generate_v4(),
    name text not null,
    slug text unique not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 2. USER PROFILES & ROLES
do $$ begin
    create type user_role as enum ('superadmin', 'hostel_owner', 'branch_manager', 'resident');
exception
    when duplicate_object then null;
end $$;

create table if not exists profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    hostel_id uuid references hostels(id) on delete cascade not null,
    full_name text not null,
    role user_role default 'resident'::user_role not null,
    phone text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 3. PROPERTY BRANCHES (Wings / Buildings)
create table if not exists properties (
    id uuid primary key default uuid_generate_v4(),
    hostel_id uuid references hostels(id) on delete cascade not null,
    name text not null, -- e.g., "Downtown Executive Wing"
    code text not null,
    total_floors int default 1 not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 4. SPATIAL ROOM NODES
do $$ begin
    create type room_status as enum ('available', 'occupied', 'maintenance', 'reserved');
exception
    when duplicate_object then null;
end $$;

create table if not exists rooms (
    id uuid primary key default uuid_generate_v4(),
    hostel_id uuid references hostels(id) on delete cascade not null,
    property_id uuid references properties(id) on delete cascade not null,
    room_number text not null, -- e.g., "302"
    floor_number int not null,
    wing text not null,
    capacity int default 2 not null,
    monthly_rent numeric(10, 2) not null,
    status room_status default 'available'::room_status not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 5. RESIDENTS / TENANTS
create table if not exists residents (
    id uuid primary key default uuid_generate_v4(),
    hostel_id uuid references hostels(id) on delete cascade not null,
    property_id uuid references properties(id) on delete cascade not null,
    room_id uuid references rooms(id) on delete set null,
    full_name text not null,
    email text not null,
    phone text not null,
    occupation text default 'Student',
    check_in_date date default current_date not null,
    status text default 'active' not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 6. RENT PAYMENTS & LEDGER
do $$ begin
    create type payment_status as enum ('verified', 'pending', 'overdue', 'rejected');
exception
    when duplicate_object then null;
end $$;

create table if not exists payments (
    id uuid primary key default uuid_generate_v4(),
    hostel_id uuid references hostels(id) on delete cascade not null,
    property_id uuid references properties(id) on delete cascade not null,
    resident_id uuid references residents(id) on delete cascade not null,
    room_id uuid references rooms(id) on delete set null,
    payment_code text not null, -- e.g., "RM-2026-11-01"
    amount numeric(10, 2) not null,
    currency text default 'USD' not null,
    status payment_status default 'pending'::payment_status not null,
    billing_month text not null, -- "2026-11"
    receipt_url text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- =========================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =========================================================================

alter table hostels enable row level security;
alter table profiles enable row level security;
alter table properties enable row level security;
alter table rooms enable row level security;
alter table residents enable row level security;
alter table payments enable row level security;

-- Helper function to fetch requesting user's hostel_id
create or replace function get_auth_hostel_id()
returns uuid language sql stable as $$
  select hostel_id from profiles where id = auth.uid();
$$;

-- Enforce Multi-Tenant Data Isolation
drop policy if exists "Hostel Data Isolation - Properties" on properties;
create policy "Hostel Data Isolation - Properties" on properties
    for all using (hostel_id = get_auth_hostel_id());

drop policy if exists "Hostel Data Isolation - Rooms" on rooms;
create policy "Hostel Data Isolation - Rooms" on rooms
    for all using (hostel_id = get_auth_hostel_id());

drop policy if exists "Hostel Data Isolation - Residents" on residents;
create policy "Hostel Data Isolation - Residents" on residents
    for all using (hostel_id = get_auth_hostel_id());

drop policy if exists "Hostel Data Isolation - Payments" on payments;
create policy "Hostel Data Isolation - Payments" on payments
    for all using (hostel_id = get_auth_hostel_id());
