import { NextResponse } from 'next/server'

const ALPACA_KEY = process.env.ALPACA_API_KEY!
const ALPACA_SECRET = process.env.ALPACA_SECRET_KEY!
const ALPACA_BASE = process.env.ALPACA_BASE_URL ?? 'https://paper-api.alpaca.markets'

const headers = {
  'APCA-API-KEY-ID': ALPACA_KEY,
  'APCA-API-SECRET-KEY': ALPACA_SECRET,
}

async function alpaca(path: string) {
  const res = await fetch(`${ALPACA_BASE}${path}`, { headers, next: { revalidate: 15 } })
  if (!res.ok) throw new Error(`Alpaca ${path} → ${res.status}`)
  return res.json()
}

export async function GET() {
  try {
    const [account, positions, history] = await Promise.all([
      alpaca('/v2/account'),
      alpaca('/v2/positions'),
      alpaca('/v2/account/portfolio/history?period=1M&timeframe=1D&intraday_reporting=market_hours'),
    ])

    const startEquity = history.equity?.[0] ?? parseFloat(account.equity)
    const totalPnl = parseFloat(account.equity) - startEquity

    return NextResponse.json({
      account: {
        equity: parseFloat(account.equity),
        cash: parseFloat(account.cash),
        buying_power: parseFloat(account.buying_power),
        pnl_today: parseFloat(account.equity) - parseFloat(account.last_equity),
        pnl_total: totalPnl,
        pnl_total_pct: startEquity > 0 ? (totalPnl / startEquity) * 100 : 0,
      },
      positions: positions.map((p: any) => ({
        symbol: p.symbol,
        qty: parseFloat(p.qty),
        market_value: parseFloat(p.market_value),
        avg_entry_price: parseFloat(p.avg_entry_price),
        current_price: parseFloat(p.current_price),
        unrealized_pl: parseFloat(p.unrealized_pl),
        unrealized_plpc: parseFloat(p.unrealized_plpc) * 100,
        side: p.side,
      })),
      history: {
        timestamps: history.timestamp ?? [],
        equity: history.equity ?? [],
        profit_loss: history.profit_loss ?? [],
      },
    })
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 })
  }
}
