# Solana Copy Trading Bot (Python)

Python bot to mirror wallet actions on Solana using:
- QuickNode RPC/WSS
- Solana Web3 (`solana-py` + `solders`)
- Jupiter swap API for execution

## What this bot does
- Monitors target wallets for recent token movement
- Infers `buy` or `sell` direction from token balance deltas
- Executes mirrored swaps from your bot wallet
- Applies simple risk controls:
  - max open positions
  - max trade budget
  - slippage bps
- Exports action + decision logs to JSONL for AI training

## Important notes
- This is a starter bot and **not production-grade**.
- DEX/CEX behaviors can be hard to infer from public transactions.
- Before real funds:
  - test on small size
  - add strict token allowlist/blocklist
  - add PnL and stop-loss logic
  - add transaction simulation and route checks

## Setup
1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy env file:
   ```bash
   copy .env.example .env
   ```
4. Fill `.env`:
   - `QUICKNODE_HTTP_URL`
   - `QUICKNODE_WSS_URL`
   - `BOT_PRIVATE_KEY` (base58 keypair)
   - `TARGET_WALLETS` (comma-separated)
   - optional risk params
   - `TRAINING_EXPORT_ENABLED` / `TRAINING_EXPORT_PATH`

## Run
```bash
python bot.py
```

## AI training export
- When enabled, the bot appends one record per action to `TRAINING_EXPORT_PATH` as JSONL.
- Each row includes:
  - source action (signature, mint, side, amount)
  - bot decision (`mirrored`, `skip`, `failed`)
  - mirrored transaction signature (if present)
  - reason (for skipped/failed decisions)
- You can use this dataset to train ranking/classification models for:
  - when to copy
  - position sizing
  - token/wallet filtering

## Next upgrades (recommended)
- Replace polling with websocket subscriptions for low latency.
- Add exact parser for known DEX programs (Raydium, Orca, Meteora).
- Add per-wallet weighting (copy 20%, 50%, etc.).
- Add persistence (SQLite/Postgres) for seen signatures and position state.
- Add Telegram/Discord alerts and kill-switch.

