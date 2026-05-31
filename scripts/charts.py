import html
import math
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
RAW_DATA_DIR = DATA_DIR / 'raw'
ANALYSIS_DATA_DIR = DATA_DIR / 'analysis'
CHARTS_DIR = DATA_DIR / 'charts'


def prompt_input(prompt: str) -> str | None:
    try:
        return input(prompt).strip()
    except EOFError:
        print('\nEntrada finalizada. Volviendo al menu anterior.')
        return None


def list_csv_files() -> list[Path]:
    files = []
    for directory in [ANALYSIS_DATA_DIR, RAW_DATA_DIR]:
        if directory.exists():
            files.extend(directory.glob('*.csv'))
    return sorted(files, key=lambda path: path.stat().st_mtime, reverse=True)


def select_csv_file() -> Path | None:
    files = list_csv_files()
    if not files:
        print('No hay archivos CSV en data/raw o data/analysis.')
        return None

    print(build_charts_dashboard())
    print('\n=== Archivos CSV disponibles ===')
    for index, file_path in enumerate(files, start=1):
        default_marker = ' (ultimo generado)' if index == 1 else ''
        print(f'{index}) {file_path.relative_to(PROJECT_ROOT)}{default_marker}')
    print('A) Atras')

    choice = prompt_input('Selecciona archivo CSV (Enter para ultimo, A para atras): ')
    if choice is None or choice.lower() == 'a':
        return None
    if not choice:
        return files[0]
    if choice.isdigit() and 1 <= int(choice) <= len(files):
        return files[int(choice) - 1]

    print('Opcion no valida.')
    return None


def build_output_path(extension: str, prefix: str = 'chart') -> Path:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime('%y%m%d%H%M%S')
    for counter in range(1, 100):
        candidate = CHARTS_DIR / f'{prefix}{timestamp}{counter:02d}.{extension}'
        if not candidate.exists():
            return candidate
    raise RuntimeError('No se pudo crear un nombre unico de salida.')


def read_chart_data(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    required_columns = {'datetime', 'open', 'high', 'low', 'close'}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f'Faltan columnas para grafico de velas: {", ".join(sorted(missing_columns))}')

    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    for column in ['open', 'high', 'low', 'close']:
        df[column] = pd.to_numeric(df[column], errors='coerce')
    return df.dropna(subset=['datetime', 'open', 'high', 'low', 'close'])


def build_charts_dashboard() -> str:
    raw_count = len(list(RAW_DATA_DIR.glob('*.csv'))) if RAW_DATA_DIR.exists() else 0
    analysis_count = len(list(ANALYSIS_DATA_DIR.glob('*.csv'))) if ANALYSIS_DATA_DIR.exists() else 0
    latest = list_csv_files()[0].relative_to(PROJECT_ROOT) if list_csv_files() else 'sin CSV'
    return (
        '\n--- Estado actual de graficos ---\n'
        f'CSV raw: {raw_count}\n'
        f'CSV analysis: {analysis_count}\n'
        f'Archivo por defecto: {latest}\n'
        f'Salida de graficos: {CHARTS_DIR.relative_to(PROJECT_ROOT)}'
    )


def make_plotly_html(csv_path: Path, df: pd.DataFrame) -> Path:
    output_path = build_output_path('html', 'chart')
    title = html.escape(csv_path.name)
    dates = [value.isoformat() for value in df['datetime']]

    html_content = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    html, body, #chart {{ width: 100%; height: 100%; margin: 0; background: #111827; }}
  </style>
</head>
<body>
  <div id="chart"></div>
  <script>
    const trace = {{
      x: {dates},
      open: {df['open'].tolist()},
      high: {df['high'].tolist()},
      low: {df['low'].tolist()},
      close: {df['close'].tolist()},
      type: 'candlestick',
      increasing: {{ line: {{ color: '#16a34a' }} }},
      decreasing: {{ line: {{ color: '#dc2626' }} }}
    }};
    Plotly.newPlot('chart', [trace], {{
      title: {title!r},
      paper_bgcolor: '#111827',
      plot_bgcolor: '#111827',
      font: {{ color: '#e5e7eb' }},
      xaxis: {{ rangeslider: {{ visible: false }}, gridcolor: '#374151' }},
      yaxis: {{ gridcolor: '#374151' }},
      margin: {{ l: 60, r: 30, t: 50, b: 45 }}
    }}, {{ responsive: true }});
  </script>
</body>
</html>
"""
    output_path.write_text(html_content, encoding='utf-8')
    return output_path


def open_chart_on_screen() -> None:
    csv_path = select_csv_file()
    if csv_path is None:
        return

    df = read_chart_data(csv_path)
    output_path = make_plotly_html(csv_path, df)
    print(f'Grafico HTML creado: {output_path}')
    webbrowser.open(output_path.resolve().as_uri())


def pdf_escape(value: str) -> str:
    return value.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def write_pdf(path: Path, title: str, commands: list[str]) -> None:
    content = '\n'.join(commands).encode('latin-1', errors='replace')
    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 842 595] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        b'<< /Length ' + str(len(content)).encode('ascii') + b' >>\nstream\n' + content + b'\nendstream',
    ]

    offsets = []
    pdf = bytearray(b'%PDF-1.4\n')
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f'{index} 0 obj\n'.encode('ascii'))
        pdf.extend(obj)
        pdf.extend(b'\nendobj\n')

    xref_offset = len(pdf)
    pdf.extend(f'xref\n0 {len(objects) + 1}\n'.encode('ascii'))
    pdf.extend(b'0000000000 65535 f \n')
    for offset in offsets:
        pdf.extend(f'{offset:010d} 00000 n \n'.encode('ascii'))
    pdf.extend(
        f'trailer << /Size {len(objects) + 1} /Root 1 0 R /Title ({pdf_escape(title)}) >>\n'
        f'startxref\n{xref_offset}\n%%EOF\n'.encode('ascii', errors='replace')
    )
    path.write_bytes(pdf)


def export_pdf_chart() -> None:
    csv_path = select_csv_file()
    if csv_path is None:
        return

    df = read_chart_data(csv_path).tail(180)
    output_path = build_output_path('pdf', 'chart')
    commands = build_candlestick_pdf_commands(csv_path.name, df)
    write_pdf(output_path, csv_path.name, commands)
    print(f'PDF horizontal creado: {output_path}')


def build_candlestick_pdf_commands(title: str, df: pd.DataFrame) -> list[str]:
    width, height = 842, 595
    left, right, bottom, top = 60, 30, 55, 55
    chart_width = width - left - right
    chart_height = height - bottom - top
    price_min = float(df['low'].min())
    price_max = float(df['high'].max())
    if math.isclose(price_min, price_max):
        price_max = price_min + 1

    def x_at(index: int) -> float:
        if len(df) <= 1:
            return left + chart_width / 2
        return left + (index / (len(df) - 1)) * chart_width

    def y_at(value: float) -> float:
        return bottom + ((value - price_min) / (price_max - price_min)) * chart_height

    commands = [
        '0 0 0 rg',
        f'BT /F1 15 Tf 60 565 Td ({pdf_escape(title)}) Tj ET',
        '0.25 0.25 0.25 RG',
        f'{left} {bottom} {chart_width} {chart_height} re S',
        '0.85 0.85 0.85 rg',
        f'BT /F1 8 Tf 60 35 Td (Velas OHLC - PDF horizontal) Tj ET',
    ]

    candle_width = max(2, min(8, chart_width / max(len(df), 1) * 0.55))
    for index, (_, row) in enumerate(df.iterrows()):
        x = x_at(index)
        open_y = y_at(float(row['open']))
        close_y = y_at(float(row['close']))
        high_y = y_at(float(row['high']))
        low_y = y_at(float(row['low']))
        if float(row['close']) >= float(row['open']):
            commands.append('0.08 0.64 0.29 RG 0.08 0.64 0.29 rg')
        else:
            commands.append('0.86 0.15 0.15 RG 0.86 0.15 0.15 rg')
        commands.append(f'{x:.2f} {low_y:.2f} m {x:.2f} {high_y:.2f} l S')
        body_y = min(open_y, close_y)
        body_h = max(abs(close_y - open_y), 1)
        commands.append(f'{x - candle_width / 2:.2f} {body_y:.2f} {candle_width:.2f} {body_h:.2f} re f')

    return commands


def numeric_columns(df: pd.DataFrame) -> list[str]:
    excluded = {'timestamp'}
    columns = []
    for column in df.columns:
        if column in excluded or column == 'datetime':
            continue
        numeric = pd.to_numeric(df[column], errors='coerce')
        if numeric.notna().any():
            columns.append(column)
    return columns


def dxf_pair(code: int, value: str | int | float) -> str:
    return f'{code}\n{value}\n'


def sanitize_layer_name(value: str) -> str:
    cleaned = ''.join(char if char.isalnum() else '_' for char in value)
    return cleaned[:200] or 'DATA'


def export_dxf_chart() -> None:
    csv_path = select_csv_file()
    if csv_path is None:
        return

    df = pd.read_csv(csv_path)
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    columns = numeric_columns(df)
    if not columns:
        print('No hay columnas numericas para exportar a DXF.')
        return

    mode = prompt_input('Modo DXF: 1) Polilinea + puntos  2) Solo puntos X [1/2]: ')
    if mode is None:
        return
    use_polyline = mode != '2'

    output_path = build_output_path('dxf', 'dxf')
    output_path.write_text(build_dxf_content(df, columns, use_polyline), encoding='ascii')
    print(f'DXF creado: {output_path}')


def build_dxf_content(df: pd.DataFrame, columns: list[str], use_polyline: bool) -> str:
    layer_names = [sanitize_layer_name(column) for column in columns]
    parts = ['0\nSECTION\n2\nTABLES\n0\nTABLE\n2\nLAYER\n']
    for layer in layer_names:
        parts.append(f'0\nLAYER\n2\n{layer}\n70\n0\n62\n7\n6\nCONTINUOUS\n')
    parts.append('0\nENDTAB\n0\nENDSEC\n0\nSECTION\n2\nENTITIES\n')

    x_spacing = 10.0
    cross_size = 2.5
    for column, layer in zip(columns, layer_names):
        series = pd.to_numeric(df[column], errors='coerce')
        points = [(index * x_spacing, float(value)) for index, value in enumerate(series) if pd.notna(value)]
        if use_polyline and points:
            parts.append(f'0\nLWPOLYLINE\n8\n{layer}\n90\n{len(points)}\n70\n0\n')
            for x, y in points:
                parts.append(dxf_pair(10, f'{x:.6f}'))
                parts.append(dxf_pair(20, f'{y:.6f}'))
            for x, y in points:
                parts.append(f'0\nPOINT\n8\n{layer}\n10\n{x:.6f}\n20\n{y:.6f}\n30\n0\n')
        else:
            for x, y in points:
                parts.append(f'0\nLINE\n8\n{layer}\n10\n{x - cross_size:.6f}\n20\n{y - cross_size:.6f}\n30\n0\n11\n{x + cross_size:.6f}\n21\n{y + cross_size:.6f}\n31\n0\n')
                parts.append(f'0\nLINE\n8\n{layer}\n10\n{x - cross_size:.6f}\n20\n{y + cross_size:.6f}\n30\n0\n11\n{x + cross_size:.6f}\n21\n{y - cross_size:.6f}\n31\n0\n')

    parts.append('0\nENDSEC\n0\nEOF\n')
    return ''.join(parts)


def show_menu() -> None:
    print(build_charts_dashboard())
    print('\n=== Graficos ===')
    print('1) Ver en pantalla')
    print('2) Exportar grafico en PDF horizontal')
    print('3) Exportar grafico en CAD/DXF')
    print('4) Volver al menu principal')


def main() -> None:
    while True:
        show_menu()
        choice = prompt_input('Selecciona una opcion [1-4]: ')
        if choice is None:
            break

        try:
            if choice == '1':
                open_chart_on_screen()
            elif choice == '2':
                export_pdf_chart()
            elif choice == '3':
                export_dxf_chart()
            elif choice == '4':
                break
            else:
                print('Opcion no valida. Intenta de nuevo.')
        except (OSError, ValueError, RuntimeError) as exc:
            print(f'Error al crear grafico: {exc}')


if __name__ == '__main__':
    main()
