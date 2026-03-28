import { NavLink } from 'react-router-dom'

const links = [
  { to: '/', label: 'Home', end: true },
  { to: '/managers', label: 'Managers' },
  { to: '/research', label: 'Research' },
  { to: '/inbox', label: 'Inbox' },
  { to: '/reports', label: 'Reports' },
]

export default function TopNav() {
  return (
    <header className="sticky top-0 z-30 border-b border-white/8 bg-slate-950/75 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 md:px-8 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.32em] text-slate-500">Wealth operating system</p>
          <h1 className="mt-2 text-2xl font-semibold tracking-[-0.05em] text-white md:text-3xl">
            Alpha <span className="text-sky-300">Wealth Desk</span>
          </h1>
          <p className="mt-2 text-sm text-slate-400">투자운영 중심 자산관리 시스템 · Home에서 상태를 보고 Manager에서 깊게 작업합니다.</p>
        </div>

        <nav className="flex flex-wrap gap-6 text-sm font-medium">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) =>
                `transition ${
                  isActive
                    ? 'text-white border-b-2 border-sky-400 pb-1'
                    : 'text-slate-400 hover:text-white'
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  )
}
