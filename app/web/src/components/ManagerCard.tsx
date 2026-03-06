import { Link } from 'react-router-dom'

type ManagerCardData = {
  manager_id: string
  title?: string
  label?: string
  headline?: string
  summary?: string
  status?: string
}

const managerRoutes: Record<string, string> = {
  core_strategy: '/managers/core-strategy',
  stock_research: '/managers/stocks',
  real_estate: '/managers/real-estate',
  cash_debt: '/managers/cash-debt',
}

export default function ManagerCard({ card }: { card: ManagerCardData }) {
  const route = managerRoutes[card.manager_id] ?? '/'

  return (
    <Link
      to={route}
      className="group rounded-[24px] border border-white/8 bg-white/[0.04] p-5 shadow-[0_18px_36px_rgba(15,23,42,0.18)] transition hover:-translate-y-0.5 hover:border-sky-300/20 hover:bg-white/[0.06]"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">{card.status ?? 'tracking'}</p>
          <h3 className="mt-2 text-xl font-semibold tracking-[-0.03em] text-white">{card.title ?? card.label ?? card.manager_id}</h3>
        </div>
        <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs text-slate-300 transition group-hover:border-sky-300/20 group-hover:text-sky-100">
          Open
        </span>
      </div>
      <p className="mt-4 text-lg font-medium text-slate-100">{card.headline ?? '준비 중'}</p>
      <p className="mt-2 text-sm leading-6 text-slate-400">{card.summary ?? 'Manager 상세 화면에서 더 많은 정보를 확인할 수 있습니다.'}</p>
    </Link>
  )
}
