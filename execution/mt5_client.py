"""
Institutional MetaTrader 5 Execution Client for AlgrokQuant
Communicates with the headless Wine MT5 REST microservice on localhost:8001.
Supports multi-desk dynamic routing (Capital Propio $1,000 & Prop Firm $50,000).
Designed for 24/7 autonomous VPS execution.
"""

import logging
from typing import Any, Dict, List, Optional
import requests

logger = logging.getLogger("MT5Client")


class MT5Client:
    def __init__(self, base_url: str = "http://127.0.0.1:8001", timeout: float = 25.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def is_healthy(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            return r.status_code == 200 and r.json().get("status") == "ok"
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def get_health(self) -> Dict[str, Any]:
        r = requests.get(f"{self.base_url}/health", timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def get_account_info(self, account: Optional[str] = None) -> Dict[str, Any]:
        params = {"account": account} if account else {}
        r = requests.get(f"{self.base_url}/account", params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def get_accounts_summary(self) -> Dict[str, Any]:
        r = requests.get(f"{self.base_url}/accounts_summary", timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        r = requests.get(f"{self.base_url}/symbol_info", params={"symbol": symbol}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def get_tick(self, symbol: str) -> Dict[str, Any]:
        r = requests.get(f"{self.base_url}/tick", params={"symbol": symbol}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def get_positions(self, symbol: Optional[str] = None, account: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {}
        if symbol:
            params["symbol"] = symbol
        if account:
            params["account"] = account
        r = requests.get(f"{self.base_url}/positions", params=params, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        return data.get("positions", [])

    def open_order(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        sl: float = 0.0,
        tp: float = 0.0,
        deviation: int = 20,
        magic: int = 20261028,
        comment: str = "AlgrokQuant MT5",
        account: Optional[str] = None
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "symbol": symbol,
            "type": order_type.upper(),
            "volume": float(volume),
            "sl": float(sl),
            "tp": float(tp),
            "deviation": int(deviation),
            "magic": int(magic),
            "comment": comment
        }
        if account:
            payload["account"] = account
        r = requests.post(f"{self.base_url}/order", json=payload, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def close_position(self, ticket: int, volume: Optional[float] = None, account: Optional[str] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"ticket": int(ticket)}
        if volume is not None:
            payload["volume"] = float(volume)
        if account:
            payload["account"] = account
        r = requests.post(f"{self.base_url}/close", json=payload, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def close_all(self, symbol: Optional[str] = None, account: Optional[str] = None) -> List[Dict[str, Any]]:
        positions = self.get_positions(symbol=symbol, account=account)
        results = []
        for pos in positions:
            ticket = pos.get("ticket")
            if ticket:
                res = self.close_position(ticket, account=account)
                results.append(res)
        return results
