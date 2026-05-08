import { NextRequest, NextResponse } from 'next/server'
import { kv } from '@vercel/kv'

const MAX_TRADES = 200

export async function GET() {
  try {
    const trades = (await kv.get<any[]>('bea:trades')) ?? []
    const lastCycle = await kv.get<any>('bea:last_cycle')
    return NextResponse.json({ trades: trades.slice(-50).reverse(), last_cycle: lastCycle })
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  const secret = process.env.TRADES_API_SECRET
  if (secret && req.headers.get('x-api-secret') !== secret) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  try {
    const body = await req.json()

    if (body.type === 'cycle_summary') {
      await kv.set('bea:last_cycle', body)
      return NextResponse.json({ ok: true })
    }

    const trades = (await kv.get<any[]>('bea:trades')) ?? []
    trades.push({ ...body, logged_at: new Date().toISOString() })
    if (trades.length > MAX_TRADES) trades.splice(0, trades.length - MAX_TRADES)
    await kv.set('bea:trades', trades)
    return NextResponse.json({ ok: true })
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 })
  }
}
