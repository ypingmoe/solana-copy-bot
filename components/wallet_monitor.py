import asyncio
import time
from typing import Dict, List, Optional, Set

from solders.pubkey import Pubkey
from solders.signature import Signature
from solana.rpc.async_api import AsyncClient


class QuickNodeWalletMonitor:
    def __init__(self, rpc_client: AsyncClient, wallets: List[str], poll_seconds: float) -> None:
        self.rpc_client = rpc_client
        self.wallets = wallets
        self.poll_seconds = poll_seconds
        self.seen_signatures: Set[str] = set()

    async def stream_actions(self):
        while True:
            for wallet in self.wallets:
                try:
                    actions = await self._fetch_recent_actions(wallet)
                    for action in actions:
                        yield action
                except Exception as exc:
                    print(f"[monitor] wallet={wallet} error={exc}")
            await asyncio.sleep(self.poll_seconds)

    async def _fetch_recent_actions(self, wallet: str) -> List[Dict]:
        owner = Pubkey.from_string(wallet)
        resp = await self.rpc_client.get_signatures_for_address(owner, limit=15)
        values = resp.value or []

        out: List[Dict] = []
        for item in values:
            sig = str(item.signature)
            if sig in self.seen_signatures:
                continue
            self.seen_signatures.add(sig)

            parsed = await self._parse_signature(sig)
            if parsed:
                out.append(parsed)
        return out

    async def _parse_signature(self, sig: str) -> Optional[Dict]:
        tx = await self.rpc_client.get_transaction(
            Signature.from_string(sig),
            encoding="jsonParsed",
            max_supported_transaction_version=0,
        )
        tx_value = tx.value
        if not tx_value or not tx_value.meta:
            return None

        pre = tx_value.meta.pre_token_balances or []
        post = tx_value.meta.post_token_balances or []

        if not pre and not post:
            return None

        # Heuristic: detect dominant token delta from token balances.
        deltas: Dict[str, float] = {}
        owner_hints: Set[str] = set()
        for b in pre:
            if b.owner:
                owner_hints.add(str(b.owner))
            mint = str(b.mint)
            ui = float(b.ui_token_amount.ui_amount or 0.0)
            deltas[mint] = deltas.get(mint, 0.0) - ui
        for b in post:
            if b.owner:
                owner_hints.add(str(b.owner))
            mint = str(b.mint)
            ui = float(b.ui_token_amount.ui_amount or 0.0)
            deltas[mint] = deltas.get(mint, 0.0) + ui

        if not deltas:
            return None

        mint, delta = max(deltas.items(), key=lambda kv: abs(kv[1]))
        if abs(delta) < 1e-10:
            return None

        side = "buy" if delta > 0 else "sell"
        return {
            "signature": sig,
            "mint": mint,
            "side": side,
            "amount_ui": abs(delta),
            "timestamp": int(time.time()),
            "owner_hints": list(owner_hints),
        }

