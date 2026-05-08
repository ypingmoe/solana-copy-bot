import asyncio

from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient

from .config import Config, ConfigError, load_config
from .exporter import TrainingDataExporter
from .risk import PositionBook
from .trader import JupiterTrader
from .wallet_monitor import QuickNodeWalletMonitor


def load_keypair_from_base58(secret: str) -> Keypair:
    try:
        return Keypair.from_base58_string(secret)
    except Exception as exc:
        raise ConfigError("BOT_PRIVATE_KEY must be a valid base58 Solana keypair.") from exc


async def run_bot(config: Config) -> None:
    payer = load_keypair_from_base58(config.bot_private_key)
    rpc_client = AsyncClient(config.quicknode_http_url, commitment="confirmed")
    monitor = QuickNodeWalletMonitor(rpc_client, config.target_wallets, config.poll_seconds)
    trader = JupiterTrader(config, payer, rpc_client)
    book = PositionBook(config.max_open_positions)
    exporter = TrainingDataExporter(
        enabled=config.training_export_enabled,
        output_path=config.training_export_path,
    )

    print("[bot] started")
    print(f"[bot] watching: {', '.join(config.target_wallets)}")
    print(f"[bot] wallet: {payer.pubkey()}")
    if config.training_export_enabled:
        print(f"[export] training dataset path: {config.training_export_path}")

    try:
        async for action in monitor.stream_actions():
            mint = action["mint"]
            side = action["side"]
            amount_ui = float(action["amount_ui"])
            sig = action["signature"]

            if side == "buy" and not book.can_open(mint):
                print(f"[risk] skip buy mint={mint} reason=max-open-positions")
                exporter.export_action(
                    action=action,
                    decision="skip",
                    mirrored_tx=None,
                    reason="max-open-positions",
                )
                continue

            print(f"[copy] source_sig={sig} side={side} mint={mint} amount={amount_ui:.6f}")
            tx_sig = await trader.execute(side=side, token_mint=mint, token_amount_ui=amount_ui)
            if not tx_sig:
                print("[copy] execution skipped/failed")
                exporter.export_action(
                    action=action,
                    decision="failed",
                    mirrored_tx=None,
                    reason="execution-skipped-or-failed",
                )
                continue

            if side == "buy":
                book.open_or_add(mint, amount_ui)
            else:
                book.reduce_or_close(mint, amount_ui)

            print(f"[copy] mirrored tx={tx_sig}")
            exporter.export_action(
                action=action,
                decision="mirrored",
                mirrored_tx=tx_sig,
            )
    finally:
        await trader.close()
        await rpc_client.close()


async def run_from_env() -> None:
    await run_bot(load_config())


def main() -> None:
    asyncio.run(run_from_env())

