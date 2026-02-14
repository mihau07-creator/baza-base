import sys
import os
sys.path.append(os.getcwd())
from backend.database import SessionLocal
from backend import models
from datetime import datetime

def find_file(base_dir, year, terms):
    year_dir = os.path.join(base_dir, str(year))
    if not os.path.exists(year_dir):
        return None
        
    clean_terms = [t.replace('/', '_').replace('\\', '_') for t in terms]
    clean_terms.extend([t.replace('/', '-') for t in terms])
    clean_terms.extend(terms)
    
    for root, dirs, files in os.walk(year_dir):
        for file in files:
            if not file.lower().endswith('.pdf'):
                continue
            f_lower = file.lower()
            for term in clean_terms:
                if term.lower() in f_lower:
                    return os.path.join(root, file)
    return None

def update_2025(base_dir):
    session = SessionLocal()
    try:
        # Filter strictly for 2025 and missing files
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 12, 31, 23, 59, 59)
        
        orders = session.query(models.Order).filter(
            models.Order.date >= start_date,
            models.Order.date <= end_date,
            (models.Order.invoice_path == None) | (models.Order.receipt_path == None)
        ).all()
        
        print(f"Checking {len(orders)} orders from 2025...")
        
        updates = 0
        for i, order in enumerate(orders):
            changed = False
            
            # Invoice
            if not order.invoice_path and order.invoice_number:
                path = find_file(base_dir, 2025, [order.invoice_number])
                if path:
                    order.invoice_path = path
                    changed = True
                    print(f"Found Inv: {path}")

            # Receipt
            if not order.receipt_path:
                terms = [order.id]
                if order.receipt_number:
                    terms.append(order.receipt_number)
                path = find_file(base_dir, 2025, terms)
                if path:
                    order.receipt_path = path
                    changed = True
                    print(f"Found Rec: {path}")
            
            if changed:
                updates += 1
                if updates % 10 == 0:
                    session.commit()
            
            if i % 100 == 0:
                print(f"Progress: {i}/{len(orders)}")

        session.commit()
        print(f"Done. Updated {updates} 2025 orders.")
        
    finally:
        session.close()

if __name__ == "__main__":
    update_2025("BaseLinker Backup")
