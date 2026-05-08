import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv


@dataclass
class Config:
    quicknode_http_url: str
    quicknode_wss_url: str
    bot_private_key: str
    target_wallets: List[str]
    jupiter_quote_url: str
    jupiter_swap_url: str
    quote_mint: str
    max_sol_per_trade: float
    max_open_positions: int
    slippage_bps: int
    poll_seconds: float
    training_export_enabled: bool
    training_export_path: str


class ConfigError(ValueError):
    pass


def load_config() -> Config:
    load_dotenv()

    quicknode_http_url = os.getenv("QUICKNODE_HTTP_URL", "").strip()
    quicknode_wss_url = os.getenv("QUICKNODE_WSS_URL", "").strip()
    bot_private_key = os.getenv("BOT_PRIVATE_KEY", "").strip()
    target_wallets_raw = os.getenv("TARGET_WALLETS", "").strip()
    jupiter_quote_url = os.getenv("JUPITER_QUOTE_URL", "https://quote-api.jup.ag/v6/quote").strip()
    jupiter_swap_url = os.getenv("JUPITER_SWAP_URL", "https://quote-api.jup.ag/v6/swap").strip()
    quote_mint = os.getenv("QUOTE_MINT", "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v").strip()
    max_sol_per_trade = float(os.getenv("MAX_SOL_PER_TRADE", "0.25"))
    max_open_positions = int(os.getenv("MAX_OPEN_POSITIONS", "5"))
    slippage_bps = int(os.getenv("SLIPPAGE_BPS", "100"))
    poll_seconds = float(os.getenv("POLL_SECONDS", "1.5"))
    training_export_enabled = os.getenv("TRAINING_EXPORT_ENABLED", "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    training_export_path = os.getenv("TRAINING_EXPORT_PATH", "exports/training_data.jsonl").strip()

    target_wallets = [w.strip() for w in target_wallets_raw.split(",") if w.strip()]

    if not quicknode_http_url:
        raise ConfigError("QUICKNODE_HTTP_URL is required.")
    if not quicknode_wss_url:
        raise ConfigError("QUICKNODE_WSS_URL is required.")
    if not bot_private_key:
        raise ConfigError("BOT_PRIVATE_KEY is required.")
    if not target_wallets:
        raise ConfigError("TARGET_WALLETS requires at least one wallet.")

    return Config(
        quicknode_http_url=quicknode_http_url,
        quicknode_wss_url=quicknode_wss_url,
        bot_private_key=bot_private_key,
        target_wallets=target_wallets,
        jupiter_quote_url=jupiter_quote_url,
        jupiter_swap_url=jupiter_swap_url,
        quote_mint=quote_mint,
        max_sol_per_trade=max_sol_per_trade,
        max_open_positions=max_open_positions,
        slippage_bps=slippage_bps,
        poll_seconds=poll_seconds,
        training_export_enabled=training_export_enabled,
        training_export_path=training_export_path,
    )

