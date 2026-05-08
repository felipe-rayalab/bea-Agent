# BEA Trading Agent

Agente de trading autónomo que opera en mercados estadounidenses usando Claude Opus 4.7 como cerebro. Capital inicial: $1500. Horizonte: 30 días. Estrategia: agresiva.

## Stack

- **Brain**: Claude Opus 4.7 vía Anthropic SDK (agentic loop)
- **Broker**: Alpaca Markets (paper + live trading)
- **Datos real-time**: Polygon.io (precios, movers, snapshots)
- **Noticias/SEC/Insiders**: Financial Datasets API
- **Earnings calendar**: EODHD API
- **Dashboard**: FastAPI + HTML en localhost:8000
- **Scheduler autónomo**: Rutina en Anthropic Cloud (`trig_01KRkEEVAMzF3upuZenRBM5M`), cada hora lun–vie 9am–4pm ET

## Estructura

```
bea_agent/
├── agent/
│   ├── main.py        # Agentic loop principal — punto de entrada
│   ├── prompts.py     # System prompt del agente trader
│   ├── tools.py       # 20 herramientas disponibles para Claude
│   └── risk.py        # Stop-losses automáticos pre-ciclo
├── broker/
│   └── alpaca_client.py   # Wrapper Alpaca REST API
├── data/
│   ├── market.py      # Polygon.io (movers, snapshots, analyst ratings)
│   ├── news.py        # Financial Datasets + EODHD (noticias, earnings, SEC)
│   └── portfolio.py   # Trade journal (trades.json)
├── dashboard/
│   ├── app.py         # FastAPI server
│   └── templates/index.html
├── journal/
│   └── trades.json    # Log de cada trade con razonamiento del agente
├── scheduler.py       # APScheduler local (alternativa al cloud)
└── .env               # API keys (nunca commitear)
```

## Variables de entorno (.env)

```
ANTHROPIC_API_KEY=
ALPACA_API_KEY=           # empieza con PK...
ALPACA_SECRET_KEY=
ALPACA_BASE_URL=https://paper-api.alpaca.markets   # cambiar a live cuando esté listo
POLYGON_API_KEY=
FINANCIAL_DATASETS_API_KEY=
EODHD_API_KEY=
CAPITAL_TOTAL=1500.0
MAX_POSITION_PCT=0.30
STOP_LOSS_PCT=0.15
MAX_OPEN_POSITIONS=3
CRYPTO_ALLOCATION_PCT=0.20
PAPER_TRADING=true
```

## Cómo correr

### Ciclo manual (una sola vez)
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python agent/main.py
```

### Dashboard
```bash
python dashboard/app.py
# Abrir http://localhost:8000
```

### Scheduler local (alternativa al cloud)
```bash
python scheduler.py
# Corre cada 15 min, lun–vie 9:00–15:45 ET
```

## Rutina autónoma en Anthropic Cloud

La rutina ya está creada y configurada:

- **ID**: `trig_01KRkEEVAMzF3upuZenRBM5M`
- **URL**: https://claude.ai/code/routines/trig_01KRkEEVAMzF3upuZenRBM5M
- **Schedule**: cada hora, lun–vie 13:00–20:00 UTC (9am–4pm ET)
- **Estado**: deshabilitada hasta que se configuren las API keys reales

### Para activar la rutina
1. Ir a https://claude.ai/code/routines
2. Editar el prompt de `BEA-Trading-Agent`
3. Reemplazar cada `REPLACE_WITH_*` con las API keys reales
4. Habilitar la rutina (toggle ON)

## Estrategia de trading

El agente sigue una estrategia **momentum + event-driven**:

1. **Earnings plays** — entrar antes/después de earnings con alta convicción
2. **News catalyst** — reaccionar a noticias de alto impacto en los primeros minutos
3. **Pre-market movers** — stocks con >3% de ganancia pre-mercado y volumen alto
4. **Rotación sectorial** — anticipar movimientos cuando un líder del sector reporta
5. **Crypto** — hasta 20% en BTC/ETH para operar fuera de horario

## Reglas de riesgo (hardcoded en agent/risk.py)

- Máximo 30% del portfolio en una posición
- Stop-loss automático al -15%
- Máximo 3 posiciones abiertas simultáneamente
- No operar en los últimos 30 min del mercado (después de 3:30pm ET)

## Pasar a live trading

1. Depositar $1500 en Alpaca live account
2. Cambiar en `.env`: `ALPACA_BASE_URL=https://api.alpaca.markets`
3. Cambiar: `PAPER_TRADING=false`
4. Actualizar la rutina en claude.ai con el nuevo `ALPACA_BASE_URL`
5. Validar con una orden pequeña antes de activar el agente completamente

## Notas importantes

- El `trades.json` **no persiste** entre ejecuciones de la rutina cloud (cada sesión es aislada). El estado real del portfolio vive en Alpaca.
- Si se quiere acumular el historial de razonamiento, conectar un storage externo (Supabase, Google Sheets).
- El dashboard local (`python dashboard/app.py`) sí muestra el estado de Alpaca en tiempo real.
