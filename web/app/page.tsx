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

function usd(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n)
}

function pct(n: number) {
  return `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`
}

function colorClass(n: number) {
  if (n > 0) return 'text-emerald-400'
  if (n < 0) return 'text-red-400'
  return 'text-gray-300'
}

function MetricCard({ label, value, sub, color }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">
      <p className="text-xs text-gray-500 uppercase tracking-widest mb-2">{label}</p>
      <p className={`text-2xl font-bold ${color ?? 'text-gray-100'}`}>{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  )
}

function PortfolioChart({ history }: { history: Portfolio['history'] }) {
  if (!history.timestamps?.length) return (
    <div className="flex items-center justify-center h-40 text-gray-600 text-sm">
      Sin datos de historial aún
    </div>
  )

  const data = history.timestamps.map((ts, i) => ({
    date: new Date(ts * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    equity: history.equity[i],
    pnl: history.profit_loss[i],
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
        <Tooltip
          contentStyle={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 6, fontSize: 12 }}
          formatter={(v: any) => [usd(v), 'Portfolio']}
          labelStyle={{ color: '#9ca3af' }}
        />
        <ReferenceLine y={baseline} stroke="#374151" strokeDasharray="4 4" />
        <Line type="monotone" dataKey="equity" stroke={lineColor} strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
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

export default function Dashboard() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [trades, setTrades] = useState<Trade[]>([])
  const [lastCycle, setLastCycle] = useState<LastCycle | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())

  const fetchData = useCallback(async () => {
    try {
      const [portRes, tradesRes] = await Promise.all([
        fetch('/api/portfolio'),
        fetch('/api/trades'),
      ])
      if (!portRes.ok) throw new Error(`Portfolio API error ${portRes.status}`)
      const portData = await portRes.json()
      const tradesData = await tradesRes.json()
      if (portData.error) throw new Error(portData.error)
      setPortfolio(portData)
      setTrades(tradesData.trades ?? [])
      setLastCycle(tradesData.last_cycle ?? null)
      setError(null)
      setLastRefresh(new Date())
    } catch (e: any) {
      setError(e.message)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const id = setInterval(fetchData, 30_000)
    return () => clearInterval(id)
  }, [fetchData])

  const acct = portfolio?.account
  const startCapital = 1500

  return (
    <div className="min-h-screen bg-[#0d1117]">
      {/* Header */}
      <header className="bg-[#161b22] border-b border-[#30363d] px-6 py-4 flex items-center gap-4">
        <div>
          <h1 className="text-lg font-bold text-blue-400">BEA Trading Agent</h1>
          <p className="text-xs text-gray-500">Autonomous • $1500 capital • 30-day horizon</p>
        </div>
        <div className="ml-auto flex items-center gap-3">
          <Badge text="PAPER TRADING" variant="yellow" />
          <Badge text="ACTIVE" variant="green" />
          <span className="text-xs text-gray-600">
            Updated {lastRefresh.toLocaleTimeString()}
          </span>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6 space-y-6">

        {error && (
          <div className="bg-red-900/30 border border-red-800 rounded-lg px-4 py-3 text-red-400 text-sm">
            ⚠ {error}
          </div>
        )}

        {/* Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard
            label="Portfolio Value"
            value={acct ? usd(acct.equity) : '—'}
            sub={acct ? `${usd(acct.cash)} cash` : undefined}
            color={acct ? colorClass(acct.equity - startCapital) : undefined}
          />
          <MetricCard
            label="Total P&L"
            value={acct ? usd(acct.pnl_total) : '—'}
            sub={acct ? pct(acct.pnl_total_pct) : undefined}
            color={acct ? colorClass(acct.pnl_total) : undefined}
          />
          <MetricCard
            label="Today's P&L"
            value={acct ? usd(acct.pnl_today) : '—'}
            color={acct ? colorClass(acct.pnl_today) : undefined}
          />
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

        {/* Last Cycle */}
        {lastCycle && (
          <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xs text-gray-500 uppercase tracking-widest">Última iteración del agente</h2>
              <div className="flex items-center gap-2">
                {lastCycle.session && (
                  <Badge
                    text={lastCycle.session.toUpperCase()}
                    variant={lastCycle.session === 'regular' ? 'green' : lastCycle.session.includes('market') ? 'yellow' : 'gray'}
                  />
                )}
                <span className="text-xs text-gray-600">
                  {new Date(lastCycle.timestamp).toLocaleString()}
                </span>
              </div>
            </div>

            {/* Actions taken */}
            {lastCycle.actions_taken?.length > 0 && (
              <div className="mb-4 space-y-2">
                {lastCycle.actions_taken.map((a: any, i: number) => (
                  <div key={i} className={`flex items-center gap-3 px-3 py-2 rounded text-sm border ${
                    a.side === 'buy' || a.action === 'buy'
                      ? 'bg-emerald-900/20 border-emerald-800/50'
                      : 'bg-red-900/20 border-red-800/50'
                  }`}>
                    <span className={`font-bold uppercase text-xs ${
                      a.side === 'buy' || a.action === 'buy' ? 'text-emerald-400' : 'text-red-400'
                    }`}>
                      {a.side ?? a.action}
                    </span>
                    <span className="font-semibold text-gray-200">{a.symbol ?? a.inputs?.symbol}</span>
                    <span className="text-gray-400">{a.qty ?? a.inputs?.qty} shares</span>
                  </div>
                ))}
              </div>
            )}

            {/* Reasoning */}
            <div className="bg-[#0d1117] rounded-lg px-4 py-3">
              <p className="text-xs text-gray-500 uppercase mb-2">Razonamiento del agente</p>
              <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
                {lastCycle.reasoning ?? 'Sin razonamiento registrado.'}
              </p>
            </div>
          </div>
        )}

        {/* Trade Journal */}
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">
          <h2 className="text-xs text-gray-500 uppercase tracking-widest mb-4">
            Historial de trades — argumentos del agente
          </h2>
          {trades.length === 0 ? (
            <p className="text-gray-600 text-sm py-4">Sin trades aún. El agente corre cada hora en horario de mercado.</p>
          ) : (
            <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
              {trades.map((t, i) => (
                <div
                  key={i}
                  className={`rounded-lg p-4 border-l-4 bg-[#0d1117] ${
                    t.action === 'buy' ? 'border-emerald-500' : 'border-red-500'
                  }`}
                >
                  <div className="flex flex-wrap items-center gap-3 mb-2">
                    <span className={`font-bold uppercase text-xs ${
                      t.action === 'buy' ? 'text-emerald-400' : 'text-red-400'
                    }`}>{t.action}</span>
                    <span className="font-semibold text-gray-100">{t.symbol}</span>
                    <span className="text-gray-400 text-sm">{t.qty} shares @ {usd(t.price)}</span>
                    <span className="text-gray-600 text-xs ml-auto">
                      {new Date(t.logged_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-300 leading-relaxed">{t.reasoning}</p>
                </div>
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
