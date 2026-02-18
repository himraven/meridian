#!/usr/bin/env python3
"""
Backfill FINRA RegSHO dark pool data to Mac Mini DuckDB
Gap period: 2025-02-01 to 2025-12-15
"""
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Constants
FINRA_URL_TEMPLATE = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{date}.txt"
START_DATE = "2025-02-03"  # First Monday after Feb 1
END_DATE = "2025-12-15"
RATE_LIMIT_SECONDS = 0.5
OUTPUT_DIR = Path("")
OUTPUT_PARQUET = OUTPUT_DIR / "darkpool_backfill.parquet"

def is_weekday(date):
    """Check if date is a weekday (Monday=0, Sunday=6)"""
    return date.weekday() < 5

def download_finra_file(date_str):
    """Download FINRA RegSHO file for a specific date"""
    url = FINRA_URL_TEMPLATE.format(date=date_str.replace("-", ""))
    try:
        print(f"Downloading {date_str}...", end=" ", flush=True)
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            print(f"✓ ({len(response.text)} bytes)")
            return response.text
        elif response.status_code == 404:
            print("✗ (not found - likely holiday)")
            return None
        else:
            print(f"✗ (HTTP {response.status_code})")
            return None
    except Exception as e:
        print(f"✗ (error: {e})")
        return None

def parse_finra_data(text_data, date_str):
    """Parse FINRA pipe-delimited text into DataFrame"""
    from io import StringIO
    
    # FINRA format: Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market
    df = pd.read_csv(StringIO(text_data), sep='|')
    
    # Transform to canonical schema
    result = pd.DataFrame({
        'ticker': df['Symbol'],
        'date': pd.to_datetime(date_str),
        'total_volume': df['TotalVolume'].astype('Int64'),
        'off_exchange_volume': df['ShortVolume'].astype('Int64'),  # FINRA ShortVolume = off-exchange proxy
        'short_volume': df['ShortVolume'].astype('Int64'),  # Also map to new canonical field
        'off_exchange_pct': (df['ShortVolume'] / df['TotalVolume'] * 100).round(2),
        'short_pct': (df['ShortVolume'] / df['TotalVolume'] * 100).round(2),
        'source': 'finra_regsho',
        # Leave z_score, z_score_window, avg_trade_size, price_close as NULL for now
        'z_score': pd.NA,
        'z_score_window': pd.NA,
        'avg_trade_size': pd.NA,
        'price_close': pd.NA
    })
    
    # Filter out invalid data (division by zero, etc.)
    result = result[result['total_volume'] > 0]
    
    return result

def main():
    """Main backfill process"""
    print("=" * 80)
    print("FINRA RegSHO Dark Pool Backfill")
    print("=" * 80)
    print(f"Date range: {START_DATE} to {END_DATE}")
    print(f"Output: {OUTPUT_PARQUET}")
    print()
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate date range
    start = datetime.strptime(START_DATE, "%Y-%m-%d")
    end = datetime.strptime(END_DATE, "%Y-%m-%d")
    
    all_data = []
    success_count = 0
    skip_count = 0
    
    current = start
    while current <= end:
        if is_weekday(current):
            date_str = current.strftime("%Y-%m-%d")
            
            # Download and parse
            raw_data = download_finra_file(date_str)
            if raw_data:
                try:
                    df = parse_finra_data(raw_data, date_str)
                    all_data.append(df)
                    success_count += 1
                    print(f"  → Parsed {len(df):,} tickers")
                except Exception as e:
                    print(f"  → Parse error: {e}")
                    skip_count += 1
            else:
                skip_count += 1
            
            # Rate limiting
            time.sleep(RATE_LIMIT_SECONDS)
        
        current += timedelta(days=1)
    
    print()
    print("=" * 80)
    print(f"Download complete: {success_count} files, {skip_count} skipped")
    
    if not all_data:
        print("ERROR: No data downloaded!")
        sys.exit(1)
    
    # Combine all data
    print("Combining data...")
    combined = pd.concat(all_data, ignore_index=True)
    
    # Remove duplicates (ticker + date)
    print(f"Total rows before dedup: {len(combined):,}")
    combined = combined.drop_duplicates(subset=['ticker', 'date'], keep='first')
    print(f"Total rows after dedup: {len(combined):,}")
    
    # Basic stats
    print()
    print("Data Summary:")
    print(f"  Date range: {combined['date'].min()} to {combined['date'].max()}")
    print(f"  Unique tickers: {combined['ticker'].nunique():,}")
    print(f"  Unique dates: {combined['date'].nunique():,}")
    print(f"  Total rows: {len(combined):,}")
    
    # Save to parquet
    print()
    print(f"Saving to {OUTPUT_PARQUET}...")
    combined.to_parquet(OUTPUT_PARQUET, index=False, compression='snappy')
    
    file_size_mb = OUTPUT_PARQUET.stat().st_size / 1024 / 1024
    print(f"✓ Saved {file_size_mb:.2f} MB")
    
    # Estimate transfer time
    transfer_time_min = (file_size_mb * 1024) / 100 / 60  # 100KB/s via Cloudflare tunnel
    print(f"  Estimated transfer time: {transfer_time_min:.1f} minutes @ 100KB/s")
    
    print()
    print("Next steps:")
    print("1. SCP to Mac Mini: scp data/backfill/darkpool_backfill.parquet macmini:~/nova-workspace/data/")
    print("2. Import to DuckDB on Mac Mini")
    print("=" * 80)

if __name__ == "__main__":
    main()
