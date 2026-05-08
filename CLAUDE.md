# BEA Trading Agent

Agente de trading autónomo que opera en mercados estadounidenses usando Claude Opus 4.7 como cerebro. Capital: $1500. Horizonte: 30 días. Estrategia: agresiva.

## Fase actual

**Paper trading — semana 1.** Migrar a live en semana 2 si los resultados son satisfactorios.
Para pasar a live: cambiar `ALPACA_BASE_URL` y `PAPER_TRADING` en la rutina (ver abajo).

## Links clave

| Recurso | URL |
|---------|-----|
| Dashboard público | https://bea-agent.vercel.app |
| Rutina autónoma | https://claude.ai/code/routines/trig_01KRkEEVAMzF3upuZenRBM5M |
| Repo GitHub | https://github.com/felipe-rayalab/bea-Agent |

## Stack

- **Brain**: Claude Opus 4.7 vía Anthropic SDK (agentic loop, 20 herramientas)
- **Broker**: Alpaca Markets (alpaca-py)
- **Datos real-time**: Polygon.io
- **Noticias / SEC / Insiders**: Financial Datasets API
- **Earnings calendar**: EODHD API
- **Dashboard**: Next.js 14 + Vercel (`web/`)
- **Trade journal**: Upstash Redis (persiste entre sesiones)
- **Scheduler autónomo**: Rutina Anthropic Cloud, `0 8-23 * * 1-5` UTC = cada hora 4am–7pm ET

## Estructura del proyecto

```
bea_agent/
├── agent/
│   ├── main.py        # Agentic loop — punto de entrada
│   ├── prompts.py     # System prompt del agente trader
│   ├── tools.py       # 20 herramientas disponibles para Claude
│   └── risk.py        # Stop-losses automáticos pre-ciclo
├── broker/
│   └── alpaca_client.py   # Wrapper Alpaca REST API + extended hours
├── data/
│   ├── market.py      # Polygon.io (movers, snapshots, analyst ratings)
│   ├── news.py        # Financial Datasets + EODHD (noticias, earnings, SEC)
│   └── portfolio.py   # Trade journal local + POST a Vercel dashboard
├── web/               # Dashboard Next.js (deployado en Vercel)
│   ├── app/
│   │   ├── page.tsx               # UI principal
│   │   ├── api/portfolio/route.ts # Proxy Alpaca API
│   │   └── api/trades/route.ts    # Trade journal (Upstash Redis)
│   └── package.json
├── dashboard/         # Dashboard local FastAPI (alternativa offline)
├── journal/
│   └── trades.json    # Log local (no persiste en CCR)
├── scheduler.py       # APScheduler local (alternativa al cloud)
└── .env               # API keys (nunca commitear)
```

## Variables de entorno (.env)

```
ANTHROPIC_API_KEY=
ALPACA_API_KEY=                    # empieza con PK...
ALPACA_SECRET_KEY=
ALPACA_BASE_URL=https://paper-api.alpaca.markets   # → https://api.alpaca.markets para live
POLYGON_API_KEY=
FINANCIAL_DATASETS_API_KEY=
EODHD_API_KEY=
VERCEL_API_URL=https://bea-agent.vercel.app
TRADES_API_SECRET=bea-secret-2026
CAPITAL_TOTAL=1500.0
MAX_POSITION_PCT=0.30
STOP_LOSS_PCT=0.15
MAX_OPEN_POSITIONS=3
CRYPTO_ALLOCATION_PCT=0.40
PAPER_TRADING=true
```

## Variables de entorno Vercel (web/)

```
ALPACA_API_KEY=
ALPACA_SECRET_KEY=
ALPACA_BASE_URL=https://paper-api.alpaca.markets
TRADES_API_SECRET=bea-secret-2026
UPSTASH_REDIS_REST_URL=
UPSTASH_REDIS_REST_TOKEN=
```

## Cómo correr localmente

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Un ciclo manual
python agent/main.py

# Scheduler local (cada 15 min, 4am–8pm ET)
python scheduler.py

# Dashboard local
python dashboard/app.py   # → http://localhost:8000
```

## Estrategia de trading

Momentum + event-driven:

1. **Earnings plays** — entrar antes/después de earnings con alta convicción
2. **News catalyst** — reaccionar a noticias de alto impacto en los primeros minutos
3. **Pre-market movers** — stocks con >3% de ganancia pre-mercado y volumen alto
4. **Rotación sectorial** — anticipar movimientos cuando un líder del sector reporta
5. **Crypto 24/7** — hasta 40% en BTC/ETH/SOL para cobertura overnight y fines de semana

## Sesiones de trading

| Sesión | Horario ET | Tipo de orden |
|--------|-----------|---------------|
| Pre-market | 4am – 9:30am | Limit con extended_hours=True |
| Regular | 9:30am – 4pm | Market orders (máxima liquidez) |
| After-hours | 4pm – 8pm | Limit con extended_hours=True |
| Overnight / finde | resto | Solo crypto (BTC, ETH, SOL) |

## Reglas de riesgo (hardcoded en agent/risk.py)

- Stop-loss automático al -15% por posición
- Máximo 30% del portfolio en una posición
- Máximo 3 posiciones abiertas simultáneamente
- Extended hours: market orders se convierten automáticamente a limit en mid±0.5%

## Pasar a live trading

1. Depositar $1500 en Alpaca live account (app.alpaca.markets)
2. En la rutina `trig_01KRkEEVAMzF3upuZenRBM5M`, cambiar en el .env del prompt:
   ```
   ALPACA_BASE_URL=https://api.alpaca.markets
   PAPER_TRADING=false
   ```
3. Actualizar también las variables en Vercel (dashboard)
4. Validar con una orden pequeña antes de activar completamente

## Arquitectura de la rutina autónoma

```
Anthropic Cloud (cada hora, 4am–7pm ET)
  → Clona github.com/felipe-rayalab/bea-Agent
  → pip install -r requirements.txt
  → Crea .env con API keys
  → python agent/main.py
      → RiskGuard: enforce stop-losses
      → Claude Opus 4.7: research → decide → execute
      → Alpaca API: place orders
      → POST /api/trades → Vercel → Upstash Redis
      → Dashboard actualizado en https://bea-agent.vercel.app
```

## Notas importantes

- El `trades.json` local **no persiste** entre sesiones CCR. El razonamiento sí persiste en Upstash Redis.
- El estado real del portfolio siempre vive en Alpaca — el agente lo lee al inicio de cada ciclo.
- **Rotar API keys** después de la primera semana (quedaron expuestas en el historial del chat).
