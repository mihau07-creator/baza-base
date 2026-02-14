import csv
import os
import re
import sys
import glob
from datetime import datetime
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from . import models
import pandas as pd

# Ensure tables exist
models.Base.metadata.create_all(bind=engine)

def parse_items(items_str):
    """
    Parses the 'Przedmioty' column.
    Format example: "1x Product Name (100.00 PLN)\n2x Product B (20.00 PLN)"
    Returns a list of dicts: [{'name':Str, 'quantity':Int, 'price':Float}]
    """
    items = []
    if not items_str or items_str == 'nan':
        return items
    
    # Split by newline if multiple items
    lines = items_str.split('\n')
    
    # Regex to capture "1x Name (Price Currency)"
    # Example: "1x Listwa gięta 880x53x8 mm (3.80 PLN)"
    pattern = re.compile(r"(\d+)x\s+(.*)\s+\((\d+\.\d+)\s+([A-Z]+)\)")
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        match = pattern.match(line)
        if match:
            qty = int(match.group(1))
            name = match.group(2).strip()
            price = float(match.group(3))
            # sku logic if present in name? For now, no explicit SKU in this parser.
            # Maybe SKU is in brackets? "Name (SKU) (Price)"? Regex above assumes (Price Currency) at end.
            sku = None 
            
            items.append({
                "name": name,
                "quantity": qty,
                "price": price,
                "sku": sku
            })
        else:
            # Fallback for lines that don't match exactly
            items.append({
                "name": line,
                "quantity": 1,
                "price": 0.0,
                "sku": None
            })
    return items

def find_file(base_dir, search_terms):
    """
    Scans base_dir for files matching search_terms.
    Simple recursive walk (can be slow for huge backup drives, but acceptable for this use case).
    """
    if not os.path.exists(base_dir):
        return None
        
    clean_terms = []
    for term in search_terms:
        if term:
            clean_terms.append(term.replace('/', '_').replace('\\', '_'))
            clean_terms.append(term.replace('/', '-'))
            clean_terms.append(term)

    # Allow limiting search depth or optimizing later if G: traffic is high
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if not file.lower().endswith('.pdf'):
                continue
                
            file_lower = file.lower()
            for term in clean_terms:
                if term.lower() in file_lower:
                    return os.path.join(root, file)
    return None

import shutil

def import_csv(csv_path, backup_dir=None):
    """
    Reads CSV and updates DB.
    Optimized for speed:
    1. Copies to local temp first.
    2. Uses batch processing.
    """
    session = SessionLocal()
    new_orders = 0
    
    # Local copy to avoid G: drive network lag
    base_name = os.path.basename(csv_path)
    temp_path = os.path.join(".", "temp_import_" + base_name)
    
    try:
        print(f"Copying {csv_path} to local temp...")
        shutil.copy2(csv_path, temp_path)
        
        print(f"Reading {temp_path}...")
        df = pd.read_csv(temp_path)
        
        # Pre-fetch existing IDs to avoid unique constraint errors if not using merge
        # For bulk_save_objects, we need to be careful about primary key collisions.
        # Simplest 'fast' way:
        # 1. Identify IDs in this CSV.
        # 2. Delete them from DB (to handle updates).
        # 3. Bulk insert new objects.
        
        ids_in_csv = df['Numer'].astype(str).tolist()
        # Filter out nans
        ids_in_csv = [x for x in ids_in_csv if x and x != 'nan']
        
        if ids_in_csv:
            print(f"Syncing {len(ids_in_csv)} records (Clearing old versions)...")
            # Split into chunks for SQLite limit (999 vars)
            # Actually easier to just iterate and collect objects, 
            # then use SQLite Upsert or just delete-then-insert.
            # Delete-then-insert is robust.
            
            # Chunking delete
            chunk_size = 900
            for i in range(0, len(ids_in_csv), chunk_size):
                chunk = ids_in_csv[i:i+chunk_size]
                session.query(models.Order).filter(models.Order.id.in_(chunk)).delete(synchronize_session=False)
                session.query(models.Item).filter(models.Item.order_id.in_(chunk)).delete(synchronize_session=False)
            session.commit()
            
        print("Preparing objects for bulk insert...")
        
        orders_batch = []
        items_batch = []
        
        for index, row in df.iterrows():
            try:
                order_id = str(row.get('Numer', ''))
                if not order_id or order_id == 'nan':
                    continue
                
                # Basic Fields
                client = str(row.get('Imię Nazwisko', ''))
                email = str(row.get('E-mail', ''))
                phone = str(row.get('Telefon', ''))
                nip = str(row.get('Dane do faktury - NIP', ''))
                if nip == 'nan': nip = None
                
                # Address
                addr_parts = [
                    str(row.get('Adres dostawy -  adres (ulica i nr domu)', '')),
                    str(row.get('Adres dostawy - kod pocztowy', '')),
                    str(row.get('Adres dostawy -  miasto', ''))
                ]
                address = ", ".join([p for p in addr_parts if p and p != 'nan'])
                
                # Date
                date_str = str(row.get('Data złożenia', ''))
                try:
                    order_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                except:
                    order_date = None
                    
                # Financials
                try: total = float(row.get('Kwota', 0.0))
                except: total = 0.0
                    
                currency = str(row.get('Waluta', 'PLN'))
                source = str(row.get('Źródło', ''))
                
                shipping_method = str(row.get('Sposób wysyłki', ''))
                try: shipping_cost = float(row.get('Koszt wysyłki', 0.0))
                except: shipping_cost = 0.0
                
                # Docs metadata
                inv_num = str(row.get('Numer faktury', ''))
                if inv_num == 'nan': inv_num = None
                
                receipt_num = str(row.get('Numer paragonu', ''))
                if receipt_num == 'nan': receipt_num = None
                
                order = models.Order(
                    id=order_id,
                    client_name=client,
                    email=email,
                    phone=phone,
                    nip=nip,
                    address=address,
                    date=order_date,
                    total=total,
                    currency=currency,
                    source=source,
                    shipping_method=shipping_method,
                    shipping_cost=shipping_cost,
                    invoice_number=inv_num,
                    receipt_number=receipt_num
                )
                orders_batch.append(order)
                
                # Items
                items_content = str(row.get('Przedmioty', ''))
                parsed = parse_items(items_content)
                for i_data in parsed:
                    item = models.Item(
                        order_id=order_id,
                        name=i_data['name'],
                        quantity=i_data['quantity'],
                        price=i_data['price'],
                        sku=i_data['sku']
                    )
                    items_batch.append(item)
                    
            except Exception as e:
                print(f"Row error: {e}")
                continue
                
        # Bulk Save
        print(f"Inserting {len(orders_batch)} orders and {len(items_batch)} items...")
        session.bulk_save_objects(orders_batch)
        session.bulk_save_objects(items_batch)
        session.commit()
        
        new_orders = len(orders_batch)
        print(f"Done. Imported {new_orders} orders.")
        
    except Exception as e:
        print(f"Fatal error importing {csv_path}: {e}")
        session.rollback()
    finally:
        session.close()
        # Cleanup
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        
    return new_orders

def find_latest_csvs(root_dir):
    """
    Finds the latest CSV file in each leaf directory (e.g. per month).
    Assumes filename is sortable date (YYYYMMDD...).
    """
    csv_files = []
    print(f"Scanning {root_dir}...")
    
    # We want to find "leaf" directories that contain CSVs, 
    # and pick the latest one from each.
    # BaseLinker Backup/2025/2025_02/Zamówienia/*.csv
    
    for root, dirs, files in os.walk(root_dir):
        # Filter for CSVs
        csvs = [f for f in files if f.lower().endswith('.csv')]
        if not csvs:
            continue
            
        # Sort by name (descending) to get latest date
        # Filename format: YYYYMMDD_HHMMSS.csv -> String sort works perfectly for date desc
        csvs.sort(reverse=True)
        latest_csv = csvs[0]
        full_path = os.path.join(root, latest_csv)
        
        # Heuristic: only pick if it looks like a backup file (contains 202...)
        if '202' in latest_csv:
            csv_files.append(full_path)
            # print(f"Selected {latest_csv} from {os.path.basename(root)}")
        
    return csv_files

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m backend.importer <csv_file_or_directory>")
        sys.exit(1)

    target_path = sys.argv[1]
    
    if os.path.isdir(target_path):
        # Directory mode
        files_to_import = find_latest_csvs(target_path)
        print(f"Found {len(files_to_import)} monthly backup files to process.")
        
        files_to_import.sort() # Process oldest to newest or whatever order
        
        total_count = 0
        for i, csv_file in enumerate(files_to_import):
            print(f"--- [{i+1}/{len(files_to_import)}] {csv_file} ---")
            total_count += import_csv(csv_file)
            
        print(f"BATCH IMPORT COMPLETE. Total processed: {total_count}")
        
    else:
        # Single file mode
        import_csv(target_path)
