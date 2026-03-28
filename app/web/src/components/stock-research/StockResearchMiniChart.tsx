import type { StockChartMarker, StockChartPoint } from '../../types/stockResearch'

function formatMarkerTone(kind: StockChartMarker['kind']) {
  switch (kind) {
    case 'earnings':
      return { stroke: '#38bdf8', fill: 'rgba(56,189,248,0.14)' }
    case 'risk':
      return { stroke: '#f59e0b', fill: 'rgba(245,158,11,0.14)' }
    default:
      return { stroke: '#a78bfa', fill: 'rgba(167,139,250,0.14)' }
  }
}

export function StockResearchMiniChart({
  series,
  markers,
}: {
  series: StockChartPoint[]
  markers: StockChartMarker[]
}) {
  if (!series.length) {
    return <div className="flex h-56 items-center justify-center rounded-2xl border border-white/8 bg-slate-950/40 text-sm text-slate-400">차트 데이터 없음</div>
  }

  const width = 640
  const height = 220
  const padding = 22
  const closes = series.map((point) => point.close)
  const min = Math.min(...closes)
  const max = Math.max(...closes)
  const range = max - min || 1
  const stepX = series.length === 1 ? 0 : (width - padding * 2) / (series.length - 1)
  const markerByDate = new Map(markers.map((marker) => [marker.date, marker]))

  const points = series.map((point, index) => {
    const x = padding + stepX * index
    const y = height - padding - ((point.close - min) / range) * (height - padding * 2)
    return { ...point, x, y, marker: markerByDate.get(point.date) }
  })
  const polyline = points.map((point) => `${point.x},${point.y}`).join(' ')

  return (
    <div className="rounded-2xl border border-white/8 bg-slate-950/40 p-4">
      <svg viewBox={`0 0 ${width} ${height}`} className="h-56 w-full">
        <defs>
          <linearGradient id="stock-line-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="rgba(56,189,248,0.24)" />
            <stop offset="100%" stopColor="rgba(56,189,248,0.02)" />
          </linearGradient>
        </defs>
        <polyline
          fill="none"
          stroke="#38bdf8"
          strokeWidth="3"
          strokeLinejoin="round"
          strokeLinecap="round"
          points={polyline}
        />
        <polygon
          fill="url(#stock-line-fill)"
          points={`${points[0].x},${height - padding} ${polyline} ${points.at(-1)?.x},${height - padding}`}
        />
        {points.map((point) => (
          <g key={point.date}>
            <circle cx={point.x} cy={point.y} r="3.5" fill="#e2e8f0" />
            {point.marker ? (
              <g>
                <line x1={point.x} y1={point.y - 12} x2={point.x} y2={point.y - 32} stroke={formatMarkerTone(point.marker.kind).stroke} strokeDasharray="4 4" />
                <circle cx={point.x} cy={point.y - 36} r="8" fill={formatMarkerTone(point.marker.kind).fill} stroke={formatMarkerTone(point.marker.kind).stroke} />
                <text x={point.x} y={point.y - 40} fill="#e2e8f0" fontSize="10" textAnchor="middle">{point.marker.label}</text>
              </g>
            ) : null}
          </g>
        ))}
      </svg>
      {markers.length ? (
        <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-300">
          {markers.map((marker) => (
            <span key={`${marker.date}:${marker.label}`} className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1">{marker.date} · {marker.label}</span>
          ))}
        </div>
      ) : null}
    </div>
  )
}
