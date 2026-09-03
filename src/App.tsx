import React, { useState, useEffect } from 'react';
import { 
  supabase, 
  isSupabaseConfigured,
  Hostel, 
  Property, 
  Room, 
  Resident, 
  Payment 
} from './lib/supabase';
import { 
  Building2, 
  Home, 
  Users, 
  CreditCard, 
  CheckCircle2, 
  AlertCircle, 
  Plus, 
  Filter, 
  Database,
  ExternalLink,
  ShieldCheck,
  ChevronRight
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState<'rooms' | 'residents' | 'payments' | 'schema'>('rooms');
  const [selectedWing, setSelectedWing] = useState<string>('All');
  const [selectedStatus, setSelectedStatus] = useState<string>('All');
  const [supabaseConnected, setSupabaseConnected] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  // Mock initial demo data matching schema.sql
  const [rooms, setRooms] = useState<Room[]>([
    {
      id: 'rm-101',
      hostel_id: 'hos-01',
      property_id: 'prop-01',
      room_number: '101',
      floor_number: 1,
      wing: 'North Wing',
      capacity: 2,
      monthly_rent: 320,
      status: 'occupied',
      created_at: new Date().toISOString()
    },
    {
      id: 'rm-102',
      hostel_id: 'hos-01',
      property_id: 'prop-01',
      room_number: '102',
      floor_number: 1,
      wing: 'North Wing',
      capacity: 2,
      monthly_rent: 320,
      status: 'available',
      created_at: new Date().toISOString()
    },
    {
      id: 'rm-201',
      hostel_id: 'hos-01',
      property_id: 'prop-01',
      room_number: '201',
      floor_number: 2,
      wing: 'Downtown Executive',
      capacity: 1,
      monthly_rent: 550,
      status: 'available',
      created_at: new Date().toISOString()
    },
    {
      id: 'rm-202',
      hostel_id: 'hos-01',
      property_id: 'prop-01',
      room_number: '202',
      floor_number: 2,
      wing: 'Downtown Executive',
      capacity: 1,
      monthly_rent: 550,
      status: 'reserved',
      created_at: new Date().toISOString()
    },
    {
      id: 'rm-301',
      hostel_id: 'hos-01',
      property_id: 'prop-01',
      room_number: '301',
      floor_number: 3,
      wing: 'Penthouse Loft',
      capacity: 3,
      monthly_rent: 280,
      status: 'occupied',
      created_at: new Date().toISOString()
    },
    {
      id: 'rm-302',
      hostel_id: 'hos-01',
      property_id: 'prop-01',
      room_number: '302',
      floor_number: 3,
      wing: 'Penthouse Loft',
      capacity: 2,
      monthly_rent: 350,
      status: 'available',
      created_at: new Date().toISOString()
    }
  ]);

  const [residents, setResidents] = useState<Resident[]>([
    {
      id: 'res-01',
      hostel_id: 'hos-01',
      property_id: 'prop-01',
      room_id: 'rm-101',
      full_name: 'Pranjal Shukla',
      email: 'pranjalshukla2222@gmail.com',
      phone: '+91 9876543210',
      occupation: 'Software Engineer',
      check_in_date: '2026-01-15',
      status: 'active',
      created_at: new Date().toISOString()
    },
    {
      id: 'res-02',
      hostel_id: 'hos-01',
      property_id: 'prop-01',
      room_id: 'rm-301',
      full_name: 'Sarah J. Parker',
      email: 'sarah.parker@example.com',
      phone: '+1 (555) 234-5678',
      occupation: 'Medical Student',
      check_in_date: '2026-02-01',
      status: 'active',
      created_at: new Date().toISOString()
    }
  ]);

  const [payments, setPayments] = useState<Payment[]>([
    {
      id: 'pay-01',
      hostel_id: 'hos-01',
      property_id: 'prop-01',
      resident_id: 'res-01',
      room_id: 'rm-101',
      payment_code: 'RM-2026-09-01',
      amount: 320,
      currency: 'USD',
      status: 'verified',
      billing_month: '2026-09',
      created_at: new Date().toISOString()
    },
    {
      id: 'pay-02',
      hostel_id: 'hos-01',
      property_id: 'prop-01',
      resident_id: 'res-02',
      room_id: 'rm-301',
      payment_code: 'RM-2026-09-02',
      amount: 280,
      currency: 'USD',
      status: 'pending',
      billing_month: '2026-09',
      created_at: new Date().toISOString()
    }
  ]);

  useEffect(() => {
    async function checkSupabase() {
      if (!isSupabaseConfigured) {
        setSupabaseConnected(false);
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        // Attempt a ping to Supabase rooms table
        const { data, error } = await supabase.from('rooms').select('*').limit(10);
        if (!error && data && data.length > 0) {
          setRooms(data as Room[]);
          setSupabaseConnected(true);
        } else {
          setSupabaseConnected(false);
        }
      } catch (err) {
        console.warn('Supabase fetch notice, using fallback state:', err);
        setSupabaseConnected(false);
      } finally {
        setLoading(false);
      }
    }
    checkSupabase();
  }, []);

  const filteredRooms = rooms.filter(room => {
    const matchesWing = selectedWing === 'All' || room.wing === selectedWing;
    const matchesStatus = selectedStatus === 'All' || room.status === selectedStatus;
    return matchesWing && matchesStatus;
  });

  const availableCount = rooms.filter(r => r.status === 'available').length;
  const occupiedCount = rooms.filter(r => r.status === 'occupied').length;
  const totalOccupancyRate = Math.round((occupiedCount / rooms.length) * 100);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* ── Top Navigation Bar ── */}
      <header style={{ 
        background: 'rgba(9, 13, 22, 0.85)', 
        backdropFilter: 'blur(16px)', 
        borderBottom: '1px solid rgba(56, 189, 248, 0.15)',
        position: 'sticky',
        top: 0,
        zIndex: 50
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '1rem 1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <img 
              src="/APP_LOGO.jpg" 
              alt="ROOMMET Logo" 
              style={{ width: '40px', height: '40px', borderRadius: '10px', objectFit: 'cover', border: '1px solid var(--primary)' }}
              onError={(e) => {
                // Fallback to text icon if image not found
                e.currentTarget.style.display = 'none';
              }}
            />
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.02em', background: 'linear-gradient(135deg, #fff 30%, var(--primary) 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                  ROOMMET
                </span>
                <span style={{ fontSize: '0.7rem', padding: '0.15rem 0.5rem', background: 'rgba(56, 189, 248, 0.1)', color: 'var(--primary)', borderRadius: '6px', border: '1px solid rgba(56, 189, 248, 0.3)', fontWeight: 600 }}>
                  SPATIAL V2
                </span>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Multi-Tenant Accommodation OS</p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '0.5rem', 
              padding: '0.4rem 0.85rem', 
              background: supabaseConnected ? 'rgba(16, 185, 129, 0.1)' : 'rgba(56, 189, 248, 0.1)', 
              borderRadius: '999px',
              border: `1px solid ${supabaseConnected ? 'rgba(16, 185, 129, 0.3)' : 'rgba(56, 189, 248, 0.3)'}`,
              fontSize: '0.8rem',
              fontWeight: 500
            }}>
              <Database size={14} color={supabaseConnected ? '#10b981' : '#38bdf8'} />
              <span>{supabaseConnected ? 'Supabase Live' : 'Demo Mode (schema.sql ready)'}</span>
            </div>

            <a 
              href="https://github.com/Pranjal578/Hostel-Management-System" 
              target="_blank" 
              rel="noreferrer"
              className="btn-secondary"
              style={{ padding: '0.45rem 0.9rem', fontSize: '0.85rem', textDecoration: 'none' }}
            >
              GitHub <ExternalLink size={14} />
            </a>
          </div>
        </div>
      </header>

      {/* ── Main Dashboard Content ── */}
      <main style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem 1.5rem', flex: 1, width: '100%' }}>
        {!isSupabaseConfigured && (
          <div style={{
            background: 'linear-gradient(90deg, rgba(56, 189, 248, 0.12), rgba(168, 85, 247, 0.12))',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            borderRadius: '12px',
            padding: '1rem 1.25rem',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '1rem',
            flexWrap: 'wrap'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <AlertCircle size={20} color="#38bdf8" />
              <span style={{ fontSize: '0.9rem', color: '#e2e8f0' }}>
                <strong>Vercel Preview Mode:</strong> Running with spatial mock nodes. To stream live database records, add <code>VITE_SUPABASE_URL</code> and <code>VITE_SUPABASE_ANON_KEY</code> in your Vercel Project Settings.
              </span>
            </div>
            <button 
              onClick={() => setActiveTab('schema')}
              className="btn-secondary"
              style={{ padding: '0.4rem 0.85rem', fontSize: '0.8rem', whiteSpace: 'nowrap' }}
            >
              View Schema SQL
            </button>
          </div>
        )}

        {/* Metric Cards Banner */}
        <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase' }}>Available Nodes</span>
              <span style={{ padding: '0.35rem', background: 'rgba(16, 185, 129, 0.15)', borderRadius: '8px', color: '#10b981' }}><CheckCircle2 size={18} /></span>
            </div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: '#34d399' }}>{availableCount} <span style={{ fontSize: '0.9rem', fontWeight: 500, color: 'var(--text-secondary)' }}>/ {rooms.length} rooms</span></div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Ready for immediate resident onboarding</p>
          </div>

          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase' }}>Occupancy Rate</span>
              <span style={{ padding: '0.35rem', background: 'rgba(56, 189, 248, 0.15)', borderRadius: '8px', color: '#38bdf8' }}><Home size={18} /></span>
            </div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: '#38bdf8' }}>{totalOccupancyRate}%</div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Active tenants across all wings</p>
          </div>

          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase' }}>Active Residents</span>
              <span style={{ padding: '0.35rem', background: 'rgba(168, 85, 247, 0.15)', borderRadius: '8px', color: '#a855f7' }}><Users size={18} /></span>
            </div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: '#c084fc' }}>{residents.length}</div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Verified profiles with digital ID passes</p>
          </div>

          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase' }}>Verified Ledger</span>
              <span style={{ padding: '0.35rem', background: 'rgba(245, 158, 11, 0.15)', borderRadius: '8px', color: '#f59e0b' }}><CreditCard size={18} /></span>
            </div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: '#fbbf24' }}>${payments.reduce((acc, p) => p.status === 'verified' ? acc + p.amount : acc, 0)}</div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Reconciled rent receipts</p>
          </div>
        </section>

        {/* ── Navigation Tabs ── */}
        <div style={{ display: 'flex', gap: '0.75rem', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', paddingBottom: '0.75rem', marginBottom: '1.5rem' }}>
          <button 
            onClick={() => setActiveTab('rooms')} 
            style={{ 
              background: activeTab === 'rooms' ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
              color: activeTab === 'rooms' ? 'var(--primary)' : 'var(--text-secondary)',
              border: activeTab === 'rooms' ? '1px solid rgba(56, 189, 248, 0.3)' : '1px solid transparent',
              padding: '0.5rem 1.15rem',
              borderRadius: '10px',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            <Building2 size={16} /> Spatial Room Mapping
          </button>

          <button 
            onClick={() => setActiveTab('residents')} 
            style={{ 
              background: activeTab === 'residents' ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
              color: activeTab === 'residents' ? 'var(--primary)' : 'var(--text-secondary)',
              border: activeTab === 'residents' ? '1px solid rgba(56, 189, 248, 0.3)' : '1px solid transparent',
              padding: '0.5rem 1.15rem',
              borderRadius: '10px',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            <Users size={16} /> Residents Directory
          </button>

          <button 
            onClick={() => setActiveTab('payments')} 
            style={{ 
              background: activeTab === 'payments' ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
              color: activeTab === 'payments' ? 'var(--primary)' : 'var(--text-secondary)',
              border: activeTab === 'payments' ? '1px solid rgba(56, 189, 248, 0.3)' : '1px solid transparent',
              padding: '0.5rem 1.15rem',
              borderRadius: '10px',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            <CreditCard size={16} /> Rent Ledger
          </button>

          <button 
            onClick={() => setActiveTab('schema')} 
            style={{ 
              background: activeTab === 'schema' ? 'rgba(168, 85, 247, 0.15)' : 'transparent',
              color: activeTab === 'schema' ? '#c084fc' : 'var(--text-secondary)',
              border: activeTab === 'schema' ? '1px solid rgba(168, 85, 247, 0.3)' : '1px solid transparent',
              padding: '0.5rem 1.15rem',
              borderRadius: '10px',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              marginLeft: 'auto'
            }}
          >
            <ShieldCheck size={16} /> Supabase RLS Schema
          </button>
        </div>

        {/* ── TAB 1: SPATIAL ROOM NODES ── */}
        {activeTab === 'rooms' && (
          <div>
            {/* Filters bar */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '1rem' }}>
              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <Filter size={14} /> Wing:
                </span>
                {['All', 'North Wing', 'Downtown Executive', 'Penthouse Loft'].map(wing => (
                  <button 
                    key={wing}
                    onClick={() => setSelectedWing(wing)}
                    style={{
                      padding: '0.35rem 0.8rem',
                      borderRadius: '8px',
                      fontSize: '0.8rem',
                      border: '1px solid',
                      borderColor: selectedWing === wing ? 'var(--primary)' : 'rgba(255, 255, 255, 0.1)',
                      background: selectedWing === wing ? 'rgba(56, 189, 248, 0.2)' : 'transparent',
                      color: selectedWing === wing ? '#fff' : 'var(--text-secondary)',
                      cursor: 'pointer'
                    }}
                  >
                    {wing}
                  </button>
                ))}
              </div>

              <div style={{ display: 'flex', gap: '0.5rem' }}>
                {['All', 'available', 'occupied', 'reserved'].map(status => (
                  <button 
                    key={status}
                    onClick={() => setSelectedStatus(status)}
                    style={{
                      padding: '0.35rem 0.8rem',
                      borderRadius: '8px',
                      fontSize: '0.8rem',
                      border: '1px solid',
                      borderColor: selectedStatus === status ? 'var(--primary)' : 'rgba(255, 255, 255, 0.1)',
                      background: selectedStatus === status ? 'rgba(56, 189, 248, 0.2)' : 'transparent',
                      color: selectedStatus === status ? '#fff' : 'var(--text-secondary)',
                      cursor: 'pointer',
                      textTransform: 'capitalize'
                    }}
                  >
                    {status}
                  </button>
                ))}
              </div>
            </div>

            {/* Room Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.25rem' }}>
              {filteredRooms.map(room => (
                <div key={room.id} className="glass-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                      <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
                        <span style={{ fontSize: '1.5rem', fontWeight: 800, color: '#fff' }}>Room {room.room_number}</span>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Floor {room.floor_number}</span>
                      </div>
                      <span className={`badge badge-${room.status}`}>{room.status}</span>
                    </div>

                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                      <Building2 size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
                      {room.wing}
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem', background: 'rgba(0,0,0,0.25)', borderRadius: '8px', marginBottom: '1rem' }}>
                      <div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Capacity</div>
                        <div style={{ fontWeight: 600 }}>{room.capacity} Residents</div>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Monthly Rent</div>
                        <div style={{ fontWeight: 700, color: 'var(--primary)' }}>${room.monthly_rent} <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>/mo</span></div>
                      </div>
                    </div>
                  </div>

                  <button className="btn-secondary" style={{ width: '100%', justifyContent: 'center', fontSize: '0.85rem' }}>
                    View Node Properties <ChevronRight size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── TAB 2: RESIDENTS DIRECTORY ── */}
        {activeTab === 'residents' && (
          <div className="glass-card" style={{ overflow: 'hidden' }}>
            <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Registered Tenants</h2>
              <button className="btn-primary" style={{ padding: '0.45rem 1rem', fontSize: '0.85rem' }}>
                <Plus size={16} /> Add Resident
              </button>
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
                <thead>
                  <tr style={{ background: 'rgba(0, 0, 0, 0.3)', color: 'var(--text-secondary)', borderBottom: '1px solid rgba(255, 255, 255, 0.08)' }}>
                    <th style={{ padding: '1rem 1.5rem' }}>Full Name</th>
                    <th style={{ padding: '1rem 1.5rem' }}>Room #</th>
                    <th style={{ padding: '1rem 1.5rem' }}>Phone</th>
                    <th style={{ padding: '1rem 1.5rem' }}>Check-in Date</th>
                    <th style={{ padding: '1rem 1.5rem' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {residents.map((r, i) => (
                    <tr key={r.id} style={{ borderBottom: i !== residents.length - 1 ? '1px solid rgba(255, 255, 255, 0.04)' : 'none' }}>
                      <td style={{ padding: '1rem 1.5rem' }}>
                        <div style={{ fontWeight: 600 }}>{r.full_name}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{r.email}</div>
                      </td>
                      <td style={{ padding: '1rem 1.5rem', fontWeight: 600, color: 'var(--primary)' }}>Room 101</td>
                      <td style={{ padding: '1rem 1.5rem', color: 'var(--text-secondary)' }}>{r.phone}</td>
                      <td style={{ padding: '1rem 1.5rem', color: 'var(--text-secondary)' }}>{r.check_in_date}</td>
                      <td style={{ padding: '1rem 1.5rem' }}>
                        <span className="badge badge-available">{r.status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── TAB 3: RENT PAYMENTS LEDGER ── */}
        {activeTab === 'payments' && (
          <div className="glass-card" style={{ overflow: 'hidden' }}>
            <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid rgba(255, 255, 255, 0.08)' }}>
              <h2 style={{ fontSize: '1.15rem', fontWeight: 700 }}>UPI & Digital Rent Transactions</h2>
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
                <thead>
                  <tr style={{ background: 'rgba(0, 0, 0, 0.3)', color: 'var(--text-secondary)', borderBottom: '1px solid rgba(255, 255, 255, 0.08)' }}>
                    <th style={{ padding: '1rem 1.5rem' }}>Transaction Code</th>
                    <th style={{ padding: '1rem 1.5rem' }}>Resident</th>
                    <th style={{ padding: '1rem 1.5rem' }}>Month</th>
                    <th style={{ padding: '1rem 1.5rem' }}>Amount</th>
                    <th style={{ padding: '1rem 1.5rem' }}>Verification</th>
                  </tr>
                </thead>
                <tbody>
                  {payments.map((p, i) => (
                    <tr key={p.id} style={{ borderBottom: i !== payments.length - 1 ? '1px solid rgba(255, 255, 255, 0.04)' : 'none' }}>
                      <td style={{ padding: '1rem 1.5rem', fontFamily: 'monospace', color: 'var(--primary)' }}>{p.payment_code}</td>
                      <td style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>Pranjal Shukla</td>
                      <td style={{ padding: '1rem 1.5rem', color: 'var(--text-secondary)' }}>{p.billing_month}</td>
                      <td style={{ padding: '1rem 1.5rem', fontWeight: 700, color: '#34d399' }}>${p.amount}</td>
                      <td style={{ padding: '1rem 1.5rem' }}>
                        <span className={`badge ${p.status === 'verified' ? 'badge-available' : 'badge-reserved'}`}>{p.status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── TAB 4: SUPABASE SCHEMA & RLS GUIDE ── */}
        {activeTab === 'schema' && (
          <div className="glass-card" style={{ padding: '2rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
              <ShieldCheck size={28} color="#a855f7" />
              <div>
                <h2 style={{ fontSize: '1.35rem', fontWeight: 700 }}>Supabase PostgreSQL Schema & RLS Policies</h2>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Configured for multi-tenant isolation in `schema.sql`</p>
              </div>
            </div>

            <div style={{ background: 'rgba(0, 0, 0, 0.4)', borderRadius: '12px', padding: '1.25rem', border: '1px solid rgba(168, 85, 247, 0.2)', marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#c084fc', marginBottom: '0.5rem' }}>Active Row-Level Security Rules:</h3>
              <ul style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', paddingLeft: '1.25rem', lineHeight: 1.8 }}>
                <li><code>properties</code>: restricted by <code>hostel_id = get_auth_hostel_id()</code></li>
                <li><code>rooms</code>: restricted by <code>hostel_id = get_auth_hostel_id()</code></li>
                <li><code>residents</code>: restricted by <code>hostel_id = get_auth_hostel_id()</code></li>
                <li><code>payments</code>: restricted by <code>hostel_id = get_auth_hostel_id()</code></li>
              </ul>
            </div>

            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
              To apply this schema to your Supabase project, open your <strong>Supabase Dashboard → SQL Editor</strong> and execute the script from <code>schema.sql</code>.
            </p>

            <a 
              href="https://supabase.com/dashboard" 
              target="_blank" 
              rel="noreferrer"
              className="btn-primary"
              style={{ textDecoration: 'none' }}
            >
              Open Supabase Dashboard <ExternalLink size={16} />
            </a>
          </div>
        )}
      </main>

      {/* ── Footer ── */}
      <footer style={{ borderTop: '1px solid rgba(255, 255, 255, 0.08)', padding: '1.5rem', textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
        ROOMMET Multi-Tenant Hostel Operating System • Deployed on Vercel & Supabase
      </footer>
    </div>
  );
}
