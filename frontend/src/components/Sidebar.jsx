import { NavLink } from 'react-router-dom'

const NAV = [
  { to: '/',        icon: '▦', label: 'Dashboard'  },
  { to: '/uploads', icon: '↑', label: 'Uploads'    },
  { to: '/reviews', icon: '✓', label: 'Reviews'    },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <span style={{
          width: 28, height: 28, borderRadius: 7, background: '#111827',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff', fontSize: 11, fontWeight: 700,
        }}>B</span>
        <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#111827' }}>BreatheESG</span>
      </div>

      <nav className="sidebar-nav">
        <p style={{
          padding: '0 20px', marginBottom: 4,
          fontSize: '0.65rem', fontWeight: 600, color: '#9ca3af',
          textTransform: 'uppercase', letterSpacing: '0.08em',
        }}>Menu</p>
        {NAV.map(({ to, icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <span style={{ fontSize: '1rem', lineHeight: 1 }}>{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>

      <div style={{ padding: '16px 20px', borderTop: '1px solid #e5e7eb' }}>
        <p className="text-xs text-gray-500">v0.1.0 · BreatheESG</p>
      </div>
    </aside>
  )
}
