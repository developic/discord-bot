import os
import re

import aiohttp
import discord
from discord import app_commands, ui
from discord.ext import commands

from ._utils import COLOR, check_allowed, fetch_json, warn

TATUM_API_KEY = os.getenv("TATUM_API_KEY")

COINS: dict[str, str] = {
    "bitcoin": "Bitcoin (BTC)",
    "ethereum": "Ethereum (ETH)",
    "solana": "Solana (SOL)",
    "litecoin": "Litecoin (LTC)",
    "ripple": "XRP",
    "cardano": "Cardano (ADA)",
    "dogecoin": "Dogecoin (DOGE)",
    "polkadot": "Polkadot (DOT)",
    "avalanche-2": "Avalanche (AVAX)",
    "polygon": "Polygon (MATIC)",
    "chainlink": "Chainlink (LINK)",
    "stellar": "Stellar (XLM)",
    "tron": "TRON (TRX)",
    "cosmos": "Cosmos (ATOM)",
    "near": "NEAR Protocol (NEAR)",
    "arbitrum": "Arbitrum (ARB)",
    "optimism": "Optimism (OP)",
}

ADDRESS_DETECT: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$"), "bitcoin"),
    (re.compile(r"^bc1[a-z0-9]{39,59}$"), "bitcoin"),
    (re.compile(r"^bc1p[a-z0-9]{38,58}$"), "bitcoin"),
    (re.compile(r"^0x[a-fA-F0-9]{40}$"), "ethereum"),
    (re.compile(r"^[LM][a-km-zA-HJ-NP-Z1-9]{26,33}$"), "litecoin"),
    (re.compile(r"^D[a-km-zA-HJ-NP-Z1-9]{25,34}$"), "dogecoin"),
    (re.compile(r"^T[a-zA-Z0-9]{33}$"), "tron"),
]

TATUM_CHAINS: dict[str, str] = {
    "bitcoin": "bitcoin",
    "ethereum": "ethereum",
    "litecoin": "litecoin",
    "dogecoin": "dogecoin",
    "tron": "tron",
}

SUPPORTED_BALANCE_COINS = ", ".join(
    f"`{c}`" for c in TATUM_CHAINS
)


def _resolve_coin(query: str) -> str | None:
    q = query.lower().replace(" ", "-")
    if q in COINS:
        return q
    for cid, display in COINS.items():
        if q in cid or q in display.lower():
            return cid
    return None


def _detect_coin(address: str) -> str | None:
    for pattern, coin_id in ADDRESS_DETECT:
        if pattern.match(address.strip()):
            return coin_id
    return None


TATUM_NODE_CHAINS: dict[str, str] = {
    "ethereum": "ethereum-mainnet",
}


def _tatum_chain(coin_id: str) -> str | None:
    return TATUM_CHAINS.get(coin_id)


async def _tatum_json_rpc(coin_id: str, method: str, params: list) -> dict | None:
    chain = TATUM_NODE_CHAINS.get(coin_id)
    if not chain or not TATUM_API_KEY:
        return None
    url = f"https://api.tatum.io/v3/blockchain/node/{chain}/"
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers={"x-api-key": TATUM_API_KEY}) as resp:
            if resp.status != 200:
                return None
            return await resp.json()


async def _tatum_balance(coin_id: str, address: str) -> tuple[float, float] | None:
    if not TATUM_API_KEY:
        return None

    if coin_id in TATUM_NODE_CHAINS:
        data = await _tatum_json_rpc(coin_id, "eth_getBalance", [address, "latest"])
        if data and data.get("result"):
            return int(data["result"], 16) / 1e18, 0
        return None

    chain = _tatum_chain(coin_id)
    if not chain:
        return None
    url = f"https://api.tatum.io/v3/{chain}/address/balance/{address}"
    async with aiohttp.ClientSession() as session:
        data = await fetch_json(session, url, headers={"x-api-key": TATUM_API_KEY})
    if data is None:
        return None
    try:
        confirmed = float(data.get("balance", 0))
        pending = float(data.get("incomingPending", 0))
        return confirmed, pending
    except (ValueError, TypeError):
        return None


async def _tatum_transactions(coin_id: str, address: str, limit: int = 5) -> list[dict] | None:
    if coin_id in TATUM_NODE_CHAINS:
        return None
    chain = _tatum_chain(coin_id)
    if not chain or not TATUM_API_KEY:
        return None
    url = f"https://api.tatum.io/v3/{chain}/transaction/address/{address}?pageSize={limit}"
    async with aiohttp.ClientSession() as session:
        data = await fetch_json(session, url, headers={"x-api-key": TATUM_API_KEY})
    if data is None:
        return None
    return data if isinstance(data, list) else None


class PriceLayout(ui.LayoutView):
    def __init__(self, coin_id: str, price: float | None, change: float | None, mcap: float | None):
        super().__init__()

        display = COINS.get(coin_id, coin_id.replace("-", " ").title())
        lines = [f"### {display}"]

        if price is not None:
            if price < 0.01:
                price_str = f"${price:.8f}"
            elif price < 1:
                price_str = f"${price:.4f}"
            else:
                price_str = f"${price:,.2f}"
            lines.append(f"**Price:** {price_str}")

        if change is not None:
            arrow = "\u2191" if change >= 0 else "\u2193"
            lines.append(f"**24h Change:** {arrow} {abs(change):.2f}%")

        if mcap is not None:
            lines.append(f"**Market Cap:** ${mcap:,.0f}")

        container = ui.Container(
            ui.TextDisplay("\n".join(lines)),
            accent_color=COLOR,
        )
        self.add_item(container)


class BalanceLayout(ui.LayoutView):
    def __init__(self, coin_id: str, address: str, balance: float, pending: float = 0, transactions: list[dict] | None = None):
        super().__init__()
        self.coin_id = coin_id
        self.address = address
        self.transactions = transactions

        ticker = COINS.get(coin_id, coin_id.upper()).split("(")[-1].rstrip(")") if "(" in COINS.get(coin_id, "") else coin_id.upper()
        display = COINS.get(coin_id, coin_id.replace("-", " ").title())
        lines = [
            f"### {display} Balance",
            f"**Address:** `{address}`",
            f"**Balance:** {balance:,.8f} {ticker}",
        ]
        if pending > 0:
            lines.append(f"**Pending:** {pending:,.8f} {ticker}")

        children: list = [
            ui.TextDisplay("\n".join(lines)),
        ]

        btn = ui.Button(
            label="View Transactions",
            custom_id="view_tx",
            style=discord.ButtonStyle.success,
        )
        btn.callback = self.on_view_tx
        children.append(ui.ActionRow(btn))

        self.add_item(ui.Container(*children, accent_color=COLOR))

    async def on_view_tx(self, interaction: discord.Interaction):
        if self.transactions is not None:
            await interaction.response.edit_message(
                view=TxLayout(self.coin_id, self.address, self.transactions)
            )
            return

        txs = await _tatum_transactions(self.coin_id, self.address)
        if txs is None:
            await interaction.response.send_message(
                "Transaction history not available for this coin.", ephemeral=True
            )
            return
        self.transactions = txs
        await interaction.response.edit_message(
            view=TxLayout(self.coin_id, self.address, txs)
        )


class TxLayout(ui.LayoutView):
    def __init__(self, coin_id: str, address: str, transactions: list[dict]):
        super().__init__()
        self.coin_id = coin_id
        self.address = address

        ticker = (
            COINS.get(coin_id, coin_id.upper()).split("(")[-1].rstrip(")")
            if "(" in COINS.get(coin_id, "")
            else coin_id.upper()
        )
        display = COINS.get(coin_id, coin_id.replace("-", " ").title())
        lines = [f"### Recent {display} Transactions"]

        if not transactions:
            lines.append("No recent transactions found.")
        else:
            for i, tx in enumerate(transactions[:5], 1):
                txid = tx.get("txId") or tx.get("txHash") or ""
                short_txid = f"{txid[:10]}...{txid[-4:]}" if len(txid) > 16 else txid
                value = tx.get("value", "0")
                try:
                    val = float(value)
                    if coin_id == "ethereum" and val > 1e12:
                        val /= 1e18
                    value_str = f"{val:+.8f}" if val else "0"
                except (ValueError, TypeError):
                    value_str = str(value)
                lines.append(f"{i}. `{short_txid}`  {value_str} {ticker}")

        children: list = [ui.TextDisplay("\n".join(lines))]

        back = ui.Button(
            label="\u2190 Back to Balance",
            custom_id="back_to_balance",
            style=discord.ButtonStyle.secondary,
        )
        back.callback = self.on_back
        children.append(ui.ActionRow(back))

        self.add_item(ui.Container(*children, accent_color=COLOR))

    async def on_back(self, interaction: discord.Interaction):
        result = await _tatum_balance(self.coin_id, self.address)
        if result is None:
            await interaction.response.send_message(
                "Could not re-fetch balance.", ephemeral=True
            )
            return
        confirmed, pending = result
        await interaction.response.edit_message(
            view=BalanceLayout(self.coin_id, self.address, confirmed, pending, transactions=None)
        )


class Crypto(commands.GroupCog, group_name="crypto"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _autocomplete_coin(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        current_lower = current.lower()
        return [
            app_commands.Choice(name=display, value=coin_id)
            for coin_id, display in COINS.items()
            if current_lower in coin_id or current_lower in display.lower()
        ][:25]

    @app_commands.command(name="price", description="Check current price of a cryptocurrency")
    @app_commands.autocomplete(coin=_autocomplete_coin)
    @app_commands.describe(coin="The cryptocurrency to look up")
    async def price(self, interaction: discord.Interaction, coin: str):
        if not await check_allowed(interaction):
            return
        await interaction.response.defer()

        coin_id = _resolve_coin(coin)
        if coin_id is None:
            coin_id = coin.lower().replace(" ", "-")

        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true&precision=full"

        async with aiohttp.ClientSession() as session:
            data = await fetch_json(session, url, timeout=aiohttp.ClientTimeout(total=10))

        if data is None or coin_id not in data:
            await interaction.followup.send(embed=warn(f"Could not find price for `{coin}`."))
            return

        info = data[coin_id]
        view = PriceLayout(
            coin_id=coin_id,
            price=info.get("usd"),
            change=info.get("usd_24h_change"),
            mcap=info.get("usd_market_cap"),
        )
        await interaction.followup.send(view=view)

    @app_commands.command(name="balance", description="Check real on-chain balance of a wallet address")
    @app_commands.autocomplete(coin=_autocomplete_coin)
    @app_commands.describe(
        address="The wallet address to check",
        coin="Optional — override auto-detected coin",
    )
    async def balance(self, interaction: discord.Interaction, address: str, coin: str | None = None):
        if not await check_allowed(interaction):
            return
        await interaction.response.defer()

        if not TATUM_API_KEY:
            await interaction.followup.send(
                embed=warn("Tatum API key not configured. Set `TATUM_API_KEY` in `.env`.")
            )
            return

        coin_id = _resolve_coin(coin) if coin else _detect_coin(address)

        if coin_id is None:
            hint = coin if coin else "auto-detect"
            await interaction.followup.send(
                embed=warn(
                    f"Could not {hint} from the provided address.\n"
                    f"Supported coins: {SUPPORTED_BALANCE_COINS}\n\n"
                    "Try: `/crypto balance <address> bitcoin` or use `coin` param."
                )
            )
            return

        chain = _tatum_chain(coin_id)
        if not chain:
            await interaction.followup.send(
                embed=warn(f"Balance checking not supported for `{COINS.get(coin_id, coin_id)}`.\nSupported: {SUPPORTED_BALANCE_COINS}")
            )
            return

        result = await _tatum_balance(coin_id, address)
        if result is None:
            await interaction.followup.send(
                embed=warn(f"Could not fetch balance for `{address}`.\nMake sure it's a valid {COINS.get(coin_id, coin_id)} address.")
            )
            return

        confirmed, pending = result
        view = BalanceLayout(coin_id, address, confirmed, pending)
        await interaction.followup.send(view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Crypto(bot))
