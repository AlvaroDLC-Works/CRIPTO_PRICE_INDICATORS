from pathlib import Path
import json

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INDICATORS_PATH = PROJECT_ROOT / 'config' / 'indicators.json'


DEFAULT_INDICATORS = [
    {
        'id': 'ema',
        'name': 'EMA',
        'description': 'Media movil exponencial. Uso comun en corto y mediano plazo.',
        'default_source': 'close',
        'default_length': 40,
    },
    {
        'id': 'sma',
        'name': 'SMA',
        'description': 'Media movil simple para tendencia base.',
        'default_source': 'close',
        'default_length': 50,
    },
    {
        'id': 'rsi',
        'name': 'RSI',
        'description': 'Indice de fuerza relativa para momentum.',
        'default_source': 'close',
        'default_length': 14,
    },
    {
        'id': 'macd',
        'name': 'MACD',
        'description': 'Cruce de medias para momentum y tendencia.',
        'default_source': 'close',
        'fast_length': 12,
        'slow_length': 26,
        'signal_length': 9,
    },
    {
        'id': 'bbands',
        'name': 'Bollinger Bands',
        'description': 'Bandas de volatilidad sobre una media movil.',
        'default_source': 'close',
        'default_length': 20,
        'std_multiplier': 2,
    },
    {
        'id': 'atr',
        'name': 'ATR',
        'description': 'Rango verdadero promedio para volatilidad.',
        'default_length': 14,
    },
    {
        'id': 'roc',
        'name': 'ROC',
        'description': 'Rate of Change para impulso de precio.',
        'default_source': 'close',
        'default_length': 12,
    },
]


def save_indicators(indicators: list[dict]) -> None:
    INDICATORS_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDICATORS_PATH.write_text(
        json.dumps({'indicators': indicators}, indent=2, ensure_ascii=False) + '\n',
        encoding='utf-8',
    )


def load_indicators() -> list[dict]:
    if not INDICATORS_PATH.exists():
        save_indicators(DEFAULT_INDICATORS)

    data = json.loads(INDICATORS_PATH.read_text(encoding='utf-8'))
    indicators = data.get('indicators', [])
    if not indicators:
        indicators = DEFAULT_INDICATORS
        save_indicators(indicators)
    return indicators


def get_indicator(indicator_id: str) -> dict:
    normalized_id = indicator_id.strip().lower()
    for indicator in load_indicators():
        if indicator['id'] == normalized_id:
            return indicator
    raise ValueError(f'Indicador no soportado: {indicator_id}')


def numeric_series(df: pd.DataFrame, source: str) -> pd.Series:
    if source not in df.columns:
        raise ValueError(f'No existe la columna requerida: {source}')
    return pd.to_numeric(df[source], errors='coerce')


def add_ema(df: pd.DataFrame, source: str = 'close', length: int = 40) -> tuple[pd.DataFrame, list[str]]:
    result = df.copy()
    column = f'ema_{length}'
    result[column] = numeric_series(result, source).ewm(span=length, adjust=False).mean()
    return result, [column]


def add_sma(df: pd.DataFrame, source: str = 'close', length: int = 50) -> tuple[pd.DataFrame, list[str]]:
    result = df.copy()
    column = f'sma_{length}'
    result[column] = numeric_series(result, source).rolling(window=length, min_periods=1).mean()
    return result, [column]


def add_rsi(df: pd.DataFrame, source: str = 'close', length: int = 14) -> tuple[pd.DataFrame, list[str]]:
    result = df.copy()
    close = numeric_series(result, source)
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window=length, min_periods=length).mean()
    loss = (-delta.clip(upper=0)).rolling(window=length, min_periods=length).mean()
    column = f'rsi_{length}'
    rs = gain / loss
    result[column] = 100 - (100 / (1 + rs))
    result.loc[(loss == 0) & (gain > 0), column] = 100
    result.loc[(loss == 0) & (gain == 0), column] = 50
    return result, [column]


def add_macd(
    df: pd.DataFrame,
    source: str = 'close',
    fast_length: int = 12,
    slow_length: int = 26,
    signal_length: int = 9,
) -> tuple[pd.DataFrame, list[str]]:
    result = df.copy()
    close = numeric_series(result, source)
    fast = close.ewm(span=fast_length, adjust=False).mean()
    slow = close.ewm(span=slow_length, adjust=False).mean()
    macd_column = f'macd_{fast_length}_{slow_length}'
    signal_column = f'macd_signal_{signal_length}'
    histogram_column = 'macd_histogram'
    result[macd_column] = fast - slow
    result[signal_column] = result[macd_column].ewm(span=signal_length, adjust=False).mean()
    result[histogram_column] = result[macd_column] - result[signal_column]
    return result, [macd_column, signal_column, histogram_column]


def add_bbands(
    df: pd.DataFrame,
    source: str = 'close',
    length: int = 20,
    std_multiplier: float = 2,
) -> tuple[pd.DataFrame, list[str]]:
    result = df.copy()
    close = numeric_series(result, source)
    middle = close.rolling(window=length, min_periods=1).mean()
    std = close.rolling(window=length, min_periods=1).std()
    middle_column = f'bb_middle_{length}'
    upper_column = f'bb_upper_{length}'
    lower_column = f'bb_lower_{length}'
    result[middle_column] = middle
    result[upper_column] = middle + (std * std_multiplier)
    result[lower_column] = middle - (std * std_multiplier)
    return result, [middle_column, upper_column, lower_column]


def add_atr(df: pd.DataFrame, length: int = 14) -> tuple[pd.DataFrame, list[str]]:
    for column in ['high', 'low', 'close']:
        if column not in df.columns:
            raise ValueError(f'No existe la columna requerida: {column}')

    result = df.copy()
    high = numeric_series(result, 'high')
    low = numeric_series(result, 'low')
    previous_close = numeric_series(result, 'close').shift(1)
    true_range = pd.concat([
        high - low,
        (high - previous_close).abs(),
        (low - previous_close).abs(),
    ], axis=1).max(axis=1)
    column = f'atr_{length}'
    result[column] = true_range.rolling(window=length, min_periods=1).mean()
    return result, [column]


def add_roc(df: pd.DataFrame, source: str = 'close', length: int = 12) -> tuple[pd.DataFrame, list[str]]:
    result = df.copy()
    column = f'roc_{length}'
    close = numeric_series(result, source)
    result[column] = close.pct_change(periods=length) * 100
    return result, [column]


def apply_indicator(df: pd.DataFrame, indicator_config: dict) -> tuple[pd.DataFrame, list[str]]:
    indicator_id = indicator_config.get('indicator_id', indicator_config.get('id', indicator_config.get('type', 'ema'))).strip().lower()
    source = indicator_config.get('source') or indicator_config.get('default_source', 'close')
    length = int(indicator_config.get('length', indicator_config.get('default_length', 40)))

    if indicator_id == 'ema':
        return add_ema(df, source=source, length=length)
    if indicator_id == 'sma':
        return add_sma(df, source=source, length=length)
    if indicator_id == 'rsi':
        return add_rsi(df, source=source, length=length)
    if indicator_id == 'macd':
        return add_macd(
            df,
            source=source,
            fast_length=int(indicator_config.get('fast_length', 12)),
            slow_length=int(indicator_config.get('slow_length', 26)),
            signal_length=int(indicator_config.get('signal_length', 9)),
        )
    if indicator_id == 'bbands':
        return add_bbands(
            df,
            source=source,
            length=length,
            std_multiplier=float(indicator_config.get('std_multiplier', 2)),
        )
    if indicator_id == 'atr':
        return add_atr(df, length=length)
    if indicator_id == 'roc':
        return add_roc(df, source=source, length=length)

    raise ValueError(f'Indicador no soportado: {indicator_id}')
