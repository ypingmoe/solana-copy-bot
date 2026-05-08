from typing import Dict, Optional

import httpx
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient

from .config import Config
from .constants import LAMPORTS_PER_SOL, USDC_DECIMALS


class JupiterTrader:
    def __init__(self, config: Config, payer: Keypair, rpc_client: AsyncClient) -> None:
        self.config = config
        self.payer = payer
        self.rpc_client = rpc_client
        self.http = httpx.AsyncClient(timeout=20.0)

    async def close(self) -> None:
        await self.http.aclose()

    async def execute(self, side: str, token_mint: str, token_amount_ui: float) -> Optional[str]:
        if token_mint == self.config.quote_mint:
            return None

        if side == "buy":
            in_mint = self.config.quote_mint
            out_mint = token_mint
            in_amount = int(self.config.max_sol_per_trade * LAMPORTS_PER_SOL / 25)
            if in_amount <= 0:
                return None
        else:
            in_mint = token_mint
            out_mint = self.config.quote_mint
            in_amount = max(1, int(token_amount_ui * (10**USDC_DECIMALS)))

        quote = await self._get_quote(in_mint, out_mint, in_amount)
        if not quote:
            return None

        swap_tx_b64 = await self._build_swap_tx(quote)
        if not swap_tx_b64:
            return None

        return await self._send_swap_transaction(swap_tx_b64)

    async def _get_quote(self, in_mint: str, out_mint: str, amount: int) -> Optional[Dict]:
        params = {
            "inputMint": in_mint,
            "outputMint": out_mint,
            "amount": amount,
            "slippageBps": self.config.slippage_bps,
        }
        resp = await self.http.get(self.config.jupiter_quote_url, params=params)
        if resp.status_code != 200:
            print(f"[trader] quote failed status={resp.status_code} body={resp.text[:300]}")
            return None
        data = resp.json()
        routes = data.get("data", [])
        return routes[0] if routes else None

    async def _build_swap_tx(self, quote: Dict) -> Optional[str]:
        payload = {
            "quoteResponse": quote,
            "userPublicKey": str(self.payer.pubkey()),
            "wrapAndUnwrapSol": True,
            "dynamicComputeUnitLimit": True,
            "prioritizationFeeLamports": "auto",
        }
        resp = await self.http.post(self.config.jupiter_swap_url, json=payload)
        if resp.status_code != 200:
            print(f"[trader] swap-build failed status={resp.status_code} body={resp.text[:300]}")
            return None
        data = resp.json()
        return data.get("swapTransaction")

    async def _send_swap_transaction(self, swap_tx_b64: str) -> Optional[str]:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sendTransaction",
            "params": [
                swap_tx_b64,
                {
                    "encoding": "base64",
                    "skipPreflight": False,
                    "maxRetries": 3,
                },
            ],
        }
        resp = await self.http.post(self.config.quicknode_http_url, json=payload)
        if resp.status_code != 200:
            print(f"[trader] send failed status={resp.status_code} body={resp.text[:300]}")
            return None
        data = resp.json()
        return data.get("result")

