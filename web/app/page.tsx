'use client'

import { useEffect, useState, useCallback } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'

type Portfolio = {
  account: {
    equity: number; cash: number; buying_power: number
    pnl_today: number; pnl_total: number; pnl_total_pct: number
  }
  positions: {
    symbol: string; qty: number; market_value: number
    avg_entry_price: number; current_price: number
    unrealized_pl: number; unrealized_plpc: number; side: string
  }[]
  history: { timestamps: number[]; equity: number[]; profit_loss: number[] }
}

type Trade = {
  logged_at: string; action: string; symbol: string
  qty: number; price: number; reasoning: string
  order?: any; portfolio?: any
}

type LastCycle = {
  timestamp: string; reasoning: string
  actions_taken: any[]; portfolio_state: any
  session?: string
}

type DayGroup = {
  dateKey: string
  label: string
  trades: Trade[]
}

// ── helpers ──────────────────────────────────────────────────────────────────

function getNextCycleTime(): Date {
  const now = new Date()
  const next = new Date(now)
  next.setUTCSeconds(0, 0)
  next.setUTCMinutes(0)
  next.setUTCHours(next.getUTCHours() + 1)
  for (let i = 0; i < 200; i++) {
    const h = next.getUTCHours(), dow = next.getUTCDay()
    if (dow >= 1 && dow <= 5 && h >= 8 && h <= 23) return next
    next.setUTCHours(next.getUTCHours() + 1)
  }
  return next
}

function useCountdown(target: Date) {
  const [diff, setDiff] = useState(Math.max(0, target.getTime() - Date.now()))
  useEffect(() => {
    const id = setInterval(() => setDiff(Math.max(0, target.getTime() - Date.now())), 1000)
    return () => clearInterval(id)
  }, [target])
  const h = Math.floor(diff / 3_600_000)
  const m = Math.floor((diff % 3_600_000) / 60_000)
  const s = Math.floor((diff % 60_000) / 1_000)
  return { h, m, s, diff }
}

function usd(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n)
}
function pct(n: number) { return `${n >= 0 ? '+' : ''}${n.toFixed(2)}%` }
function colorClass(n: number) {
  if (n > 0) return 'text-emerald-400'
  if (n < 0) return 'text-red-400'
  return 'text-gray-300'
}

function fmtTime(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function fmtDayLabel(dateKey: string) {
  const d = new Date(dateKey + 'T12:00:00')
  return d.toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
}

function groupTradesByDay(trades: Trade[]): DayGroup[] {
  const map: Record<string, Trade[]> = {}
  for (const t of trades) {
    const key = new Date(t.logged_at).toISOString().slice(0, 10)
    if (!map[key]) map[key] = []
    map[key].push(t)
  }
  return Object.entries(map)
    .sort(([a], [b]) => b.localeCompare(a))
    .map(([dateKey, ts]) => ({
      dateKey,
      label: fmtDayLabel(dateKey),
      trades: ts.sort((a, b) => new Date(b.logged_at).getTime() - new Date(a.logged_at).getTime()),
    }))
}

function briefDescription(reasoning: string): string {
  if (!reasoning) return ''
  const first = reasoning.split('.')[0]
  return first.length > 120 ? first.slice(0, 120) + '…' : first + '.'
}

// ── sub-components ────────────────────────────────────────────────────────────

function MetricCard({ label, value, sub, color }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">
      <p className="text-xs text-gray-500 uppercase tracking-widest mb-2">{label}</p>
      <p className={`text-2xl font-bold ${color ?? 'text-gray-100'}`}>{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  )
}

function Badge({ text, variant }: { text: string; variant: 'green' | 'red' | 'yellow' | 'gray' }) {
  const cls = {
    green: 'bg-emerald-900/40 text-emerald-400 border-emerald-800',
    red: 'bg-red-900/40 text-red-400 border-red-800',
    yellow: 'bg-yellow-900/40 text-yellow-400 border-yellow-800',
    gray: 'bg-gray-800/40 text-gray-400 border-gray-700',
  }[variant]
  return <span className={`text-xs px-2 py-0.5 rounded border font-semibold ${cls}`}>{text}</span>
}

function PortfolioChart({ history }: { history: Portfolio['history'] }) {
  if (!history.timestamps?.length) return (
    <div className="flex items-center justify-center h-40 text-gray-600 text-sm">Sin datos de historial aún</div>
  )
  const data = history.timestamps.map((ts, i) => ({
    date: new Date(ts * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    equity: history.equity[i],
  }))
  const baseline = data[0]?.equity ?? 0
  const min = Math.min(...data.map(d => d.equity)) * 0.999
  const max = Math.max(...data.map(d => d.equity)) * 1.001
  const last = data[data.length - 1]?.equity ?? baseline
  const lineColor = last >= baseline ? '#34d399' : '#f87171'
  return (
    <ResponsiveContainer width="100%" height={180}>
      <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
        <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#6b7280' }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
        <YAxis domain={[min, max]} tick={{ fontSize: 11, fill: '#6b7280' }} tickLine={false} axisLine={false} tickFormatter={v => `$${(v / 1000).toFixed(1)}k`} width={52} />
        <Tooltip contentStyle={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 6, fontSize: 12 }} formatter={(v: any) => [usd(v), 'Portfolio']} labelStyle={{ color: '#9ca3af' }} />
        <ReferenceLine y={baseline} stroke="#374151" strokeDasharray="4 4" />
        <Line type="monotone" dataKey="equity" stroke={lineColor} strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  )
}

function TradeRow({ trade }: { trade: Trade }) {
  const [open, setOpen] = useState(false)
  const isBuy = trade.action === 'buy'
  return (
    <div className="border-b border-[#21262d] last:border-0">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center gap-3 py-2.5 px-3 hover:bg-[#1c2128] rounded text-left transition-colors"
      >
        <span className="text-xs text-gray-500 tabular-nums w-14 shrink-0">{fmtTime(trade.logged_at)}</span>
        <span className={`text-xs font-bold uppercase w-8 shrink-0 ${isBuy ? 'text-emerald-400' : 'text-red-400'}`}>
          {trade.action}
        </span>
        <span className="font-semibold text-gray-100 w-14 shrink-0">{trade.symbol}</span>
        <span className="text-gray-400 text-xs">{trade.qty} shares @ {usd(trade.price)}</span>
        <span className="ml-auto text-gray-600 text-xs shrink-0">{open ? '▲' : '▼'}</span>
      </button>
      {open && trade.reasoning && (
        <p className="px-3 pb-3 text-xs text-gray-400 leading-relaxed">
          {briefDescription(trade.reasoning)}
        </p>
      )}
    </div>
  )
}

function DayAccordion({ group, defaultOpen }: { group: DayGroup; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen ?? false)
  const symbols = [...new Set(group.trades.map(t => t.symbol))].join(', ')
  const buys = group.trades.filter(t => t.action === 'buy').length
  const sells = group.trades.filter(t => t.action === 'sell').length
  const summary = [buys > 0 && `${buys} buy`, sells > 0 && `${sells} sell`].filter(Boolean).join(' · ')

  return (
    <div className="border border-[#30363d] rounded-lg overflow-hidden mb-3">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center gap-3 px-4 py-3 bg-[#161b22] hover:bg-[#1c2128] transition-colors text-left"
      >
        <span className="text-sm font-semibold text-gray-200">{group.label}</span>
        <span className="text-xs text-gray-500">·</span>
        <span className={`text-xs font-semibold ${group.trades.length > 0 ? 'text-emerald-400' : 'text-gray-500'}`}>
          {group.trades.length > 0 ? summary : 'Sin operaciones'}
        </span>
        {symbols && <span className="text-xs text-gray-500 truncate">{symbols}</span>}
        <span className="ml-auto text-gray-500 text-xs">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="bg-[#0d1117] px-1">
          {group.trades.map((t, i) => <TradeRow key={i} trade={t} />)}
        </div>
      )}
    </div>
  )
}

function LastCycleStatus({ lastCycle }: { lastCycle: LastCycle }) {
  const traded = lastCycle.actions_taken?.length > 0
  const symbols = traded
    ? [...new Set(lastCycle.actions_taken.map((a: any) => a.symbol ?? a.inputs?.symbol))].join(', ')
    : null
  const timeAgo = (() => {
    const diff = Date.now() - new Date(lastCycle.timestamp).getTime()
    const m = Math.floor(diff / 60_000)
    if (m < 1) return 'just now'
    if (m < 60) return `${m}m ago`
    return `${Math.floor(m / 60)}h ago`
  })()

  return (
    <div className={`flex items-center gap-3 px-4 py-2.5 rounded-lg border text-sm ${
      traded
        ? 'bg-emerald-900/20 border-emerald-800/40'
        : 'bg-[#161b22] border-[#30363d]'
    }`}>
      <span className={`text-xs font-bold uppercase ${traded ? 'text-emerald-400' : 'text-gray-500'}`}>
        {traded ? 'OPERÓ' : 'SIN CAMBIOS'}
      </span>
      {traded && <span className="font-semibold text-gray-200">{symbols}</span>}
      {!traded && <span className="text-gray-500">El agente revisó el portfolio y decidió mantener posiciones</span>}
      <span className="ml-auto text-xs text-gray-600">{timeAgo} · {new Date(lastCycle.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
    </div>
  )
}

// ── main ──────────────────────────────────────────────────────────────────────

export default function Dashboard() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [trades, setTrades] = useState<Trade[]>([])
  const [lastCycle, setLastCycle] = useState<LastCycle | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())
  const [nextCycle] = useState<Date>(() => getNextCycleTime())
  const countdown = useCountdown(nextCycle)

  const fetchData = useCallback(async () => {
    try {
      const [portRes, tradesRes] = await Promise.all([fetch('/api/portfolio'), fetch('/api/trades')])
      if (!portRes.ok) throw new Error(`Portfolio API error ${portRes.status}`)
      const portData = await portRes.json()
      const tradesData = await tradesRes.json()
      if (portData.error) throw new Error(portData.error)
      setPortfolio(portData)
      setTrades(tradesData.trades ?? [])
      setLastCycle(tradesData.last_cycle ?? null)
      setError(null)
      setLastRefresh(new Date())
    } catch (e: any) { setError(e.message) }
  }, [])

  useEffect(() => {
    fetchData()
    const id = setInterval(fetchData, 30_000)
    return () => clearInterval(id)
  }, [fetchData])

  const acct = portfolio?.account
  const dayGroups = groupTradesByDay(trades)

  return (
    <div className="min-h-screen bg-[#0d1117]">

      {/* Header */}
      <header className="bg-[#161b22] border-b border-[#30363d] px-6 py-4 flex items-center gap-4">
        <div>
          <h1 className="text-lg font-bold text-blue-400">BEA Trading Agent</h1>
          <p className="text-xs text-gray-500">Autonomous · $1500 capital · 30-day horizon</p>
        </div>
        <div className="ml-auto flex items-center gap-3">
          <Badge text="PAPER TRADING" variant="yellow" />
          <Badge text="ACTIVE" variant="green" />
          <div className="flex items-center gap-2 bg-[#0d1117] border border-[#30363d] rounded-lg px-3 py-1.5">
            <span className="text-xs text-gray-500">Next cycle</span>
            <span className="text-xs font-bold text-blue-400 tabular-nums">
              {countdown.diff === 0
                ? 'Running...'
                : `${String(countdown.h).padStart(2,'0')}:${String(countdown.m).padStart(2,'0')}:${String(countdown.s).padStart(2,'0')}`}
            </span>
            <span className="text-xs text-gray-600">
              {nextCycle.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
          <span className="text-xs text-gray-600">Updated {lastRefresh.toLocaleTimeString()}</span>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6 space-y-6">

        {error && (
          <div className="bg-red-900/30 border border-red-800 rounded-lg px-4 py-3 text-red-400 text-sm">⚠ {error}</div>
        )}

        {/* Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard label="Portfolio Value" value={acct ? usd(acct.equity) : '—'} sub={acct ? `${usd(acct.cash)} cash` : undefined} color={acct ? colorClass(acct.equity - 1500) : undefined} />
          <MetricCard label="Total P&L" value={acct ? usd(acct.pnl_total) : '—'} sub={acct ? pct(acct.pnl_total_pct) : undefined} color={acct ? colorClass(acct.pnl_total) : undefined} />
          <MetricCard label="Today's P&L" value={acct ? usd(acct.pnl_today) : '—'} color={acct ? colorClass(acct.pnl_today) : undefined} />
          <MetricCard
            label="Trades Executed"
            value={String(trades.length)}
            sub={`${trades.filter(t => t.action === 'buy').length} buys / ${trades.filter(t => t.action === 'sell').length} sells`}
          />
        </div>

        {/* Chart */}
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">
          <h2 className="text-xs text-gray-500 uppercase tracking-widest mb-4">Portfolio — últimos 30 días</h2>
          {portfolio ? <PortfolioChart history={portfolio.history} /> : (
            <div className="h-40 flex items-center justify-center text-gray-600 text-sm">Cargando...</div>
          )}
        </div>

        {/* Positions */}
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">
          <h2 className="text-xs text-gray-500 uppercase tracking-widest mb-4">Posiciones abiertas</h2>
          {!portfolio ? (
            <p className="text-gray-600 text-sm">Cargando...</p>
          ) : portfolio.positions.length === 0 ? (
            <p className="text-gray-600 text-sm py-4">Sin posiciones abiertas</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 text-xs uppercase border-b border-[#30363d]">
                  <th className="text-left pb-2">Ticker</th>
                  <th className="text-right pb-2">Qty</th>
                  <th className="text-right pb-2">Entrada</th>
                  <th className="text-right pb-2">Precio actual</th>
                  <th className="text-right pb-2">Valor</th>
                  <th className="text-right pb-2">P&L no realizado</th>
                </tr>
              </thead>
              <tbody>
                {portfolio.positions.map(p => (
                  <tr key={p.symbol} className="border-b border-[#21262d] hover:bg-[#1c2128]">
                    <td className="py-3 font-bold text-gray-100">{p.symbol}</td>
                    <td className="py-3 text-right text-gray-300">{p.qty}</td>
                    <td className="py-3 text-right text-gray-400">{usd(p.avg_entry_price)}</td>
                    <td className="py-3 text-right text-gray-200">{usd(p.current_price)}</td>
                    <td className="py-3 text-right text-gray-300">{usd(p.market_value)}</td>
                    <td className={`py-3 text-right font-semibold ${colorClass(p.unrealized_pl)}`}>
                      {usd(p.unrealized_pl)} ({pct(p.unrealized_plpc)})
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Activity Log */}
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xs text-gray-500 uppercase tracking-widest">Actividad del agente</h2>
            {trades.length > 0 && (
              <span className="text-xs text-gray-600">{trades.length} operaciones en total</span>
            )}
          </div>

          {/* Last cycle status */}
          {lastCycle && (
            <div className="mb-4">
              <p className="text-xs text-gray-600 mb-1.5">Última iteración</p>
              <LastCycleStatus lastCycle={lastCycle} />
            </div>
          )}

          {/* Daily log */}
          {dayGroups.length === 0 ? (
            <p className="text-gray-600 text-sm py-4">Sin actividad registrada aún.</p>
          ) : (
            <div>
              {dayGroups.map((g, i) => (
                <DayAccordion key={g.dateKey} group={g} defaultOpen={i === 0} />
              ))}
            </div>
          )}
        </div>

      </main>

      <footer className="text-center text-xs text-gray-700 py-6">
        BEA Trading Agent · Paper Trading · Auto-refresh cada 30s
      </footer>
    </div>
  )
}
