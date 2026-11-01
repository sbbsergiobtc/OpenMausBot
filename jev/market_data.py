"""Capa 1: Recopilación de Datos de Mercado (Market Data).

Ingesta síncrona o asíncrona de fuentes primarias (APIs de exchanges, archivos CSV/Parquet).
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import logging
import pandas as pd

from .models import Candle
from .exceptions import DataIngestionError

logger = logging.getLogger("jev.market_data")


class BaseMarketDataIngestion(ABC):
    """Interfaz abstracta para la ingesta de datos de mercado."""

    @abstractmethod
    def fetch_recent_candles(self, symbol: str, timeframe: str, limit: int = 250) -> List[Candle]:
        """Obtiene las últimas 'limit' velas para el símbolo y marco temporal especificado."""
        pass


class CSVMarketDataIngestion(BaseMarketDataIngestion):
    """Ingesta de datos de mercado a partir de archivos locales procesados."""

    def __init__(self, data_directory: str):
        self.data_dir = Path(data_directory)
        if not self.data_dir.exists():
            raise DataIngestionError(f"El directorio de datos no existe: {self.data_dir}")

    def fetch_recent_candles(self, symbol: str, timeframe: str, limit: int = 250) -> List[Candle]:
        normalized_symbol = symbol.replace("/", "_").lower()
        filename = f"{normalized_symbol}_{timeframe}.csv"
        file_path = self.data_dir / filename

        if not file_path.exists():
            raise DataIngestionError(f"Archivo de mercado no encontrado: {file_path}")

        try:
            logger.info("Cargando datos históricos desde: %s (límite: %d velas)", file_path, limit)
            df = pd.read_csv(file_path)
            
            # Normalizar columnas
            cols = {c.lower(): c for c in df.columns}
            time_col = cols.get("timestamp") or cols.get("time") or cols.get("date")
            open_col = cols.get("open")
            high_col = cols.get("high")
            low_col = cols.get("low")
            close_col = cols.get("close")
            vol_col = cols.get("volume")

            if not all([time_col, open_col, high_col, low_col, close_col, vol_col]):
                raise DataIngestionError(f"El dataset {file_path} no contiene las columnas OHLCV obligatorias.")

            df = df.tail(limit).copy()
            candles: List[Candle] = []

            for _, row in df.iterrows():
                try:
                    ts_val = row[time_col]
                    if isinstance(ts_val, (int, float)):
                        ts = datetime.fromtimestamp(ts_val / 1000 if ts_val > 1e11 else ts_val)
                    else:
                        ts = pd.to_datetime(ts_val).to_pydatetime()

                    candles.append(
                        Candle(
                            timestamp=ts,
                            open=float(row[open_col]),
                            high=float(row[high_col]),
                            low=float(row[low_col]),
                            close=float(row[close_col]),
                            volume=float(row[vol_col]),
                        )
                    )
                except Exception as parse_err:
                    logger.warning("Vela descartada por error de parseo: %s", parse_err)

            if len(candles) < 30:
                raise DataIngestionError(f"Insuficientes velas ({len(candles)}) para calcular indicadores fiables.")

            return candles

        except Exception as e:
            if isinstance(e, DataIngestionError):
                raise
            raise DataIngestionError(f"Error procesando datos desde {file_path}: {e}") from e


class SimulatedRealtimeDataIngestion(BaseMarketDataIngestion):
    """Simulador de ingesta en tiempo real que emite streams de velas para tests."""

    def __init__(self, base_candles: List[Candle]):
        self.candles = base_candles

    def fetch_recent_candles(self, symbol: str, timeframe: str, limit: int = 250) -> List[Candle]:
        return self.candles[-limit:]
