import os
import sys
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from . import models
from datetime import datetime

def find_file_in_year(base_dir, year, search_terms):
    """
    Scans base_dir/year for files matching search_terms.
    """
    year_dir = os.path.join(base_dir, str(year))
    if not os.path.exists(year_dir):
        print(f"Directory not found: {year_dir}")
        return None
        
    clean_terms = [t.replace('/', '_').replace('\\', '_') for t in search_terms]
    clean_terms.extend([t.replace('/', '-') for t in search_terms])
    clean_terms.extend(search_terms)
    
    # print(f"Scanning {year_dir} for {clean_terms}")
    
    for root, dirs, files in os.walk(year_dir):
        for file in files:
            if not file.lower().endswith('.pdf'):
                continue
            
            f_lower = file.lower()
            for term in clean_terms:
                if term.lower() in f_lower:
                    return os.path.join(root, file)
    return None

def update_paths(base_dir):
    session = SessionLocal()
    try:
        # Get orders that need files
        orders = session.query(models.Order).filter(
            (models.Order.invoice_path == None) | (models.Order.receipt_path == None)
        ).all()
        
        print(f"Checking {len(orders)} orders for missing files...")
        
        count = 0
        updates = 0
        for order in orders:
            changed = False
            
            # Determine Order Year
            if not order.date:
                continue
                
            year = order.date.year
            
            # Invoice
            if not order.invoice_path and order.invoice_number:
                path = find_file_in_year(base_dir, year, [order.invoice_number])
                if path:
                    order.invoice_path = path
                    changed = True
                    print(f"Found Invoice for {order.id}: {path}")

            # Receipt
            if not order.receipt_path:
                terms = [order.id]
                if order.receipt_number:
                    terms.append(order.receipt_number)
                
                path = find_file_in_year(base_dir, year, terms)
                if path:
                    order.receipt_path = path
                    changed = True
                    print(f"Found Receipt for {order.id}: {path}")
            
            if changed:
                updates += 1
                if updates % 10 == 0:
                    session.commit()
            
            count += 1
            if count % 100 == 0:
                print(f"Processed {count} orders...")

        session.commit()
        print(f"Finished. Updated {updates} orders.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m backend.update_paths <directory>")
    else:
        update_paths(sys.argv[1])
