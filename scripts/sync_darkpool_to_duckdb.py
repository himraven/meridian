#!/usr/bin/env python3
"""
Sync VPS darkpool.json to Mac Mini DuckDB (incremental updates)

Run this after darkpool collector runs to keep DuckDB in sync with latest signals.
Can be added to cron: darkpool.py && sync_darkpool_to_duckdb.py
"""
import json
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

VPS_DATA_FILE = Path("")
MAC_DUCKDB_PATH = "~/nova-workspace/data/stocks.duckdb"
MAC_PYTHON_VENV = "~/nova-workspace/.venv/bin/activate"

def load_vps_data():
    """Load latest darkpool.json from VPS"""
    if not VPS_DATA_FILE.exists():
        print(f"ERROR: {VPS_DATA_FILE} not found!")
        sys.exit(1)
    
    with open(VPS_DATA_FILE) as f:
        data = json.load(f)
    
    tickers_data = data.get("tickers", [])
    print(f"Loaded {len(tickers_data)} tickers from VPS darkpool.json")
    print(f"Date range: {data['metadata'].get('date_range', 'N/A')}")
    
    return tickers_data

def check_mac_mini_connection():
    """Verify SSH connection to Mac Mini"""
    result = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=5", "macmini", "echo 'OK'"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("ERROR: Cannot connect to Mac Mini via SSH")
        print(f"  {result.stderr}")
        sys.exit(1)
    
    print("✓ Mac Mini SSH connection OK")

def get_existing_dates():
    """Get existing dates in DuckDB to avoid duplicates"""
    cmd = f"""ssh macmini "source {MAC_PYTHON_VENV} && python3 -c \\"
import duckdb
db = duckdb.connect('{MAC_DUCKDB_PATH}')
dates = db.execute('SELECT DISTINCT date FROM darkpool ORDER BY date DESC LIMIT 30').fetchall()
for d in dates:
    print(d[0])
db.close()
\\""  """
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"WARNING: Could not fetch existing dates: {result.stderr}")
        return set()
    
    dates = set(line.strip() for line in result.stdout.strip().split('\n') if line.strip())
    print(f"Found {len(dates)} recent dates in DuckDB")
    return dates

def sync_to_duckdb(tickers_data):
    """
    Sync tickers to Mac Mini DuckDB
    
    Strategy: Create temp CSV, SCP to Mac Mini, INSERT via DuckDB
    """
    print(f"\nPreparing {len(tickers_data)} records for sync...")
    
    # Create temp CSV
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_csv = f.name
        
        # Write CSV header
        f.write("ticker,date,total_volume,off_exchange_volume,short_volume,")
        f.write("off_exchange_pct,short_pct,z_score,z_score_window,source\n")
        
        # Write data rows
        for item in tickers_data:
            # Map fields (handle missing values)
            def fmt(val, default=''):
                """Format value for CSV, empty string for NULL"""
                if val is None or val == '':
                    return ''
                return str(val)
            
            row = [
                item.get('ticker', ''),
                item.get('date', ''),
                fmt(item.get('total_volume'), '0'),
                fmt(item.get('off_exchange_volume'), '0'),
                fmt(item.get('short_volume', item.get('off_exchange_volume')), '0'),
                fmt(item.get('off_exchange_pct'), '0'),
                fmt(item.get('short_pct', item.get('off_exchange_pct')), '0'),
                fmt(item.get('z_score')),  # Empty = NULL
                fmt(item.get('z_score_window')),
                item.get('source', 'finra_regsho')
            ]
            f.write(','.join(row) + '\n')
    
    print(f"Created temp CSV: {temp_csv}")
    
    # SCP to Mac Mini
    remote_csv = f"/tmp/darkpool_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    print(f"Transferring to Mac Mini: {remote_csv}")
    
    scp_result = subprocess.run(
        ["scp", temp_csv, f"macmini:{remote_csv}"],
        capture_output=True,
        text=True
    )
    
    if scp_result.returncode != 0:
        print(f"ERROR: SCP failed: {scp_result.stderr}")
        Path(temp_csv).unlink()
        sys.exit(1)
    
    Path(temp_csv).unlink()
    print("✓ Transfer complete")
    
    # Import via DuckDB on Mac Mini
    print("Importing to DuckDB...")
    
    import_cmd = f"""ssh macmini "source {MAC_PYTHON_VENV} && python3 -c \\"
import duckdb
db = duckdb.connect('{MAC_DUCKDB_PATH}')

# Import new data (will skip duplicates if ticker+date is unique)
db.execute('''
    INSERT INTO darkpool (
        ticker, date, total_volume, off_exchange_volume, off_exchange_pct, source,
        short_volume, short_pct, z_score, z_score_window, avg_trade_size, price_close
    )
    SELECT 
        ticker, 
        CAST(date AS DATE),
        total_volume,
        off_exchange_volume,
        off_exchange_pct,
        source,
        short_volume,
        short_pct,
        z_score::DOUBLE,
        z_score_window::INTEGER,
        NULL::DOUBLE as avg_trade_size,
        NULL::DOUBLE as price_close
    FROM read_csv_auto('{remote_csv}')
    WHERE NOT EXISTS (
        SELECT 1 FROM darkpool d 
        WHERE d.ticker = read_csv_auto.ticker 
        AND d.date = CAST(read_csv_auto.date AS DATE)
    )
''')

# Get stats
result = db.execute('SELECT COUNT(*), MIN(date), MAX(date) FROM darkpool').fetchone()
print(f'Total rows: {{result[0]:,}}')
print(f'Date range: {{result[1]}} to {{result[2]}}')

db.close()
print('✓ Import complete')
\\" && rm {remote_csv}" """
    
    import_result = subprocess.run(import_cmd, shell=True, capture_output=True, text=True)
    
    if import_result.returncode != 0:
        print(f"ERROR: DuckDB import failed: {import_result.stderr}")
        sys.exit(1)
    
    print(import_result.stdout)

def main():
    print("=" * 80)
    print("Dark Pool VPS → Mac Mini DuckDB Sync")
    print("=" * 80)
    
    # Check connection
    check_mac_mini_connection()
    
    # Load VPS data
    tickers_data = load_vps_data()
    
    if not tickers_data:
        print("No data to sync!")
        return
    
    # Sync to DuckDB
    sync_to_duckdb(tickers_data)
    
    print("=" * 80)
    print("✓ Sync complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
