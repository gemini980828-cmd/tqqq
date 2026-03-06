import { NavLink, Outlet } from 'react-router-dom'

const SUB_NAV = [
  { to: '/managers', label: 'Overview', end: true },
  { to: '/managers/core-strategy', label: 'Core Strategy' },
  { to: '/managers/stocks', label: 'Stocks' },
  { to: '/managers/real-estate', label: 'Real Estate' },
  { to: '/managers/cash-debt', label: 'Cash & Debt' },
]

export default function ManagersLayout() {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">Managers</p>
        <h2 className="mt-2 text-3xl font-semibold tracking-[-0.05em] text-white">자산군별 운영 매니저</h2>
      </div>
      <div className="flex flex-wrap gap-2">
        {SUB_NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `rounded-full border px-4 py-2 text-sm font-medium transition ${
                isActive
                  ? 'border-sky-300/30 bg-sky-400/12 text-sky-100'
                  : 'border-white/10 bg-white/[0.03] text-slate-300 hover:border-white/20 hover:bg-white/[0.06]'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </div>
      <Outlet />
    </div>
  )
}
