# BEA Trading Agent

Agente de trading autónomo que opera en mercados estadounidenses usando Claude Opus 4.7 como cerebro. Capital: $1500. Horizonte: 30 días. Estrategia: agresiva.

## Fase actual

**Paper trading — semana 1.** Primer ciclo ejecutado el 2026-05-08 con 3 posiciones (AMD, TSLA, NVDA).
Migrar a live en semana 2 si los resultados son satisfactorios.

## Links clave

| Recurso | URL |
|---------|-----|
| Dashboard público | https://bea-agent.vercel.app |
| Rutina autónoma | https://claude.ai/code/routines/trig_01KRkEEVAMzF3upuZenRBM5M |
| Repo GitHub | https://github.com/felipe-rayalab/bea-Agent |

## Stack

- **Brain**: Claude Opus 4.7 vía Anthropic SDK (agentic loop, 20+ herramientas)
- **Broker**: Alpaca Markets (alpaca-py) — paper + live
- **Datos real-time**: Yahoo Finance via `yfinance` (gratis, sin API key)
- **Quotes exactos + históricos**: Alpaca Data API (incluido con la cuenta)
- **Noticias**: Alpaca News API (incluido con la cuenta, sin costo extra)
- **Dashboard**: Next.js 14 + Vercel (`web/`)
- **Trade journal**: Upstash Redis (persiste entre sesiones CCR)
- **Scheduler autónomo**: Rutina Anthropic Cloud, `0 8-23 * * 1-5` UTC = cada hora 4am–7pm ET

## Fuentes de datos

| Fuente | Qué provee | API Key |
|--------|-----------|---------|
| Alpaca Data API | Quotes real-time, OHLCV histórico | Misma key del broker |
| Alpaca News API | Noticias por ticker y mercado general | Misma key del broker |
| Yahoo Finance (yfinance) | Movers, snapshots, earnings calendar, analyst ratings | No requiere |

> Polygon.io, EODHD y Financial Datasets fueron removidos — free tiers con límites que rompían el ciclo.

## Compatibilidad

**Python 3.9+** — el código usa `if/elif` en lugar de `match/case`, y `Optional[T]` en lugar de `T | None`.
`load_dotenv()` se llama al inicio de `agent/main.py` para cargar el `.env` antes de cualquier import.

## Estructura del proyecto

```
bea_agent/
├── agent/
│   ├── main.py        # Agentic loop — punto de entrada (load_dotenv al top)
│   ├── prompts.py     # System prompt del agente trader
│   ├── tools.py       # 20+ herramientas (if/elif, Python 3.9 compatible)
│   └── risk.py        # Stop-losses automáticos pre-ciclo
├── broker/
│   └── alpaca_client.py   # Wrapper Alpaca REST API + extended hours support
├── data/
│   ├── market.py      # Yahoo Finance: movers, snapshots, analyst ratings
│   ├── news.py        # Financial Datasets (noticias) + yfinance (earnings)
│   └── portfolio.py   # Trade journal local + POST a Vercel dashboard
├── web/               # Dashboard Next.js (deployado en Vercel)
│   ├── app/
│   │   ├── page.tsx               # UI principal (dark theme, auto-refresh 30s)
│   │   ├── api/portfolio/route.ts # Proxy Alpaca API
│   │   └── api/trades/route.ts    # Trade journal (Upstash Redis)
│   └── package.json
├── dashboard/         # Dashboard local FastAPI (alternativa offline)
├── journal/
│   └── trades.json    # Log local (no persiste en CCR)
├── scheduler.py       # APScheduler local (cada 15 min, 4am–8pm ET)
└── .env               # API keys (nunca commitear — está en .gitignore)
```

## Variables de entorno (.env)

```
ANTHROPIC_API_KEY=
ALPACA_API_KEY=                    # empieza con PK...
ALPACA_SECRET_KEY=
ALPACA_BASE_URL=https://paper-api.alpaca.markets   # → https://api.alpaca.markets para live
FINANCIAL_DATASETS_API_KEY=        # free tier, para noticias y SEC
VERCEL_API_URL=https://bea-agent.vercel.app
TRADES_API_SECRET=bea-secret-2026
CAPITAL_TOTAL=1500.0
MAX_POSITION_PCT=0.30
STOP_LOSS_PCT=0.15
MAX_OPEN_POSITIONS=3
CRYPTO_ALLOCATION_PCT=0.40
PAPER_TRADING=true
```

> `POLYGON_API_KEY` y `EODHD_API_KEY` ya no son necesarios.

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
cd ~/Documents/bea_agent
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Un ciclo manual
python3 -m agent.main

# Scheduler local (cada 15 min, 4am–8pm ET)
python3 scheduler.py

# Dashboard local
python3 dashboard/app.py   # → http://localhost:8000
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
- Máximo 10 posiciones abiertas simultáneamente
- Extended hours: market orders se convierten automáticamente a limit en mid±0.5%

## Lógica de rotación (agent/prompts.py)

El agente evalúa posiciones existentes en cada ciclo y rota activamente:
- Puntúa cada posición: ¿sigue activo el catalizador original? ¿hay noticias negativas?
- Si encuentra una oportunidad con catalizador más fuerte, vende la posición más débil y compra la nueva
- Permite operar aunque el cash sea bajo — la rotación no requiere cash libre

## Pasar a live trading

1. Depositar $1500 en Alpaca live account (app.alpaca.markets)
2. En la rutina `trig_01KRkEEVAMzF3upuZenRBM5M`, actualizar el .env del prompt:
   ```
   ALPACA_BASE_URL=https://api.alpaca.markets
   PAPER_TRADING=false
   ```
3. Actualizar `ALPACA_BASE_URL` también en las variables de entorno de Vercel
4. Validar con una orden pequeña antes de activar completamente

## Arquitectura de la rutina autónoma

```
Anthropic Cloud (cada hora, 4am–7pm ET, lun–vie)
  → Clona github.com/felipe-rayalab/bea-Agent (GitHub autorizado)
  → pip install -r requirements.txt
  → Crea .env con API keys
  → python3 -m agent.main
      → load_dotenv() carga el .env
      → RiskGuard: enforce stop-losses pre-ciclo
      → Claude Opus 4.7: research → decide → execute
          → yfinance: movers, snapshots, earnings
          → Alpaca Data: quotes exactos, OHLCV
          → Financial Datasets: noticias, SEC
          → Alpaca Trading: place orders
      → POST cycle summary → Vercel → Upstash Redis
      → Dashboard actualizado en https://bea-agent.vercel.app
```

## Primer ciclo (2026-05-08)

- AMD: 65 shares @ $438.43
- TSLA: 65 shares @ $429.25
- NVDA: 130 shares @ $215.88
- Portfolio: $100,017 (+$17) | Cash: $15,536 | Deployed: 84.5%
- Razonamiento: momentum tape, AMD post-earnings continuation, TSLA uptrend, NVDA breakout

## Notas importantes

- El `trades.json` local **no persiste** entre sesiones CCR. El razonamiento persiste en Upstash Redis.
- El estado real del portfolio siempre vive en Alpaca — el agente lo lee al inicio de cada ciclo.
- **Rotar API keys** — quedaron expuestas en el historial del chat. Hacerlo después de la semana 1.
- La rutina puede dar "prompt injection" warnings — es Claude siendo cauteloso. El mensaje está diseñado para dejar claro que es una rutina autorizada.
