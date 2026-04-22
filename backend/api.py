from fastapi import APIRouter, Depends, HTTPException, Query, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime
from fastapi.responses import FileResponse, StreamingResponse
import os
import io
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from .database import get_db
from . import models

# Inicjalizacja Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), 'google_credentials.json')

drive_service = None
google_creds_env = os.getenv("GOOGLE_CREDENTIALS_JSON")

try:
    if google_creds_env:
        creds_info = json.loads(google_creds_env)
        creds = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        drive_service = build('drive', 'v3', credentials=creds)
        print("Udało się podłączyć do Google Drive API (przez Cloud ENV)!")
    elif os.path.exists(SERVICE_ACCOUNT_FILE):
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        drive_service = build('drive', 'v3', credentials=creds)
        print("Udało się podłączyć do Google Drive API (przez lokalny plik)!")
except Exception as e:
    print(f"Błąd inicjalizacji Google Drive API: {e}")

router = APIRouter(prefix="/api")

security = HTTPBearer()
PASSWORD = os.getenv("APP_PASSWORD", "archiwum2025")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != PASSWORD:
        raise HTTPException(status_code=401, detail="Nieprawidlowe haslo")
    return credentials.credentials

@router.get("/search", dependencies=[Depends(verify_token)])
def search_orders(
    q: Optional[str] = None,
    nip: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    client: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    source: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(models.Order)

    if date_from:
        try:
            d_from = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(models.Order.date >= d_from)
        except: pass
        
    if date_to:
        try:
            d_to = datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            query = query.filter(models.Order.date <= d_to)
        except: pass

    if source:
        query = query.filter(models.Order.source == source)
        
    if client:
        search_client = f"%{client}%"
        query = query.filter(
            (models.Order.client_name.like(search_client)) |
            (models.Order.nip.like(search_client))
        )

    if q:
        search_terms = q.strip().split()
        for term in search_terms:
            t_search = f"%{term}%"
            query = query.filter(
                (models.Order.id.like(t_search)) |
                (models.Order.client_name.like(t_search)) |
                (models.Order.email.like(t_search)) |
                (models.Order.phone.like(t_search)) |
                (models.Order.nip.like(t_search)) |
                (models.Order.address.like(t_search))
            )
    
    if nip:
        query = query.filter(models.Order.nip.like(f"%{nip}%"))
    if email:
        query = query.filter(models.Order.email.like(f"%{email}%"))
    if phone:
        query = query.filter(models.Order.phone.like(f"%{phone}%"))

    # Sorting by date desc
    query = query.order_by(models.Order.date.desc())

    total_count = query.count()
    orders = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "total": total_count,
        "page": page,
        "limit": limit,
        "data": orders
    }

@router.get("/order/{order_id}", dependencies=[Depends(verify_token)])
def get_order_details(order_id: str, db: Session = Depends(get_db)):
    order = db.query(models.Order).options(joinedload(models.Order.items)).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Manually fetch items to ensure they are returned (though lazy loading might work, implicit is better)
    # The relationship 'items' in model should handle it if configured, but let's be safe for JSON serialization.
    # Actually FastAPI Pydantic models (if used) would handle it, but here we return ORM objects directly.
    # Defaults in FastAPI usually serialize relationships if loaded.
    # Explicitly serialize to dict to ensure items are included
    return {
        "id": order.id,
        "client_name": order.client_name,
        "email": order.email,
        "phone": order.phone,
        "nip": order.nip,
        "address": order.address,
        "date": order.date,
        "total": order.total,
        "currency": order.currency,
        "source": order.source,
        "shipping_method": order.shipping_method,
        "shipping_cost": order.shipping_cost,
        "invoice_number": order.invoice_number,
        "receipt_number": order.receipt_number,
        "invoice_path": order.invoice_path,
        "receipt_path": order.receipt_path,
        "items": [
            {
                "name": item.name,
                "quantity": item.quantity,
                "price": item.price,
                "sku": item.sku
            } for item in order.items
        ]
    }

@router.get("/stats/sales", dependencies=[Depends(verify_token)])
def get_sales_stats(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    source: Optional[str] = None,
    client: Optional[str] = None,
    product: Optional[str] = None,
    db: Session = Depends(get_db)
):
    d_from_obj = None
    d_to_obj = None
    if date_from:
        try: d_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
        except: pass
    if date_to:
        try: d_to_obj = datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        except: pass

    # Determine grouping: Day vs Month
    group_by_day = False
    if d_from_obj and d_to_obj:
        if (d_to_obj - d_from_obj).days <= 90:
            group_by_day = True
    elif d_from_obj and not d_to_obj:
        if (datetime.now() - d_from_obj).days <= 90:
            group_by_day = True
            
    date_format = "%Y-%m-%d" if group_by_day else "%Y-%m"
    stats = {}

    if product:
        # Single query for specific product
        query = db.query(models.Order.date, models.Item.quantity, models.Item.price)\
                  .join(models.Order)\
                  .filter(models.Order.date.isnot(None))
        
        search_product = f"%{product}%"
        query = query.filter((models.Item.name.ilike(search_product)) | (models.Item.sku.ilike(search_product)))
        
        if d_from_obj: query = query.filter(models.Order.date >= d_from_obj)
        if d_to_obj: query = query.filter(models.Order.date <= d_to_obj)
        if source: query = query.filter(models.Order.source == source)
        if client:
            search_client = f"%{client}%"
            query = query.filter((models.Order.client_name.ilike(search_client)) | (models.Order.nip.ilike(search_client)))

        results = query.all()
        for date_val, qty_val, price_val in results:
            if not date_val: continue
            date_key = date_val.strftime(date_format)
            if date_key not in stats:
                stats[date_key] = {"total_sales": 0.0, "quantity": 0, "count": 0}
            stats[date_key]["total_sales"] += (qty_val or 0) * (price_val or 0.0)
            stats[date_key]["quantity"] += (qty_val or 0)
            stats[date_key]["count"] += 1
    else:
        # Two queries for overall stats
        query = db.query(models.Order.date, models.Order.total).filter(models.Order.date.isnot(None))
        if d_from_obj: query = query.filter(models.Order.date >= d_from_obj)
        if d_to_obj: query = query.filter(models.Order.date <= d_to_obj)
        if source: query = query.filter(models.Order.source == source)
        if client:
            search_client = f"%{client}%"
            query = query.filter((models.Order.client_name.ilike(search_client)) | (models.Order.nip.ilike(search_client)))
            
        orders = query.all()
        for o in orders:
            if not o.date: continue
            date_key = o.date.strftime(date_format)
            if date_key not in stats:
                stats[date_key] = {"total_sales": 0.0, "quantity": 0, "count": 0}
            stats[date_key]["total_sales"] += (o.total or 0.0)
            stats[date_key]["count"] += 1

        qty_query = db.query(models.Order.date, models.Item.quantity)\
            .join(models.Order)\
            .filter(models.Order.date.isnot(None))\
            .filter(~models.Item.name.ilike("%wysyłka%"), ~models.Item.name.ilike("%GLS%"))
            
        if d_from_obj: qty_query = qty_query.filter(models.Order.date >= d_from_obj)
        if d_to_obj: qty_query = qty_query.filter(models.Order.date <= d_to_obj)
        if source: qty_query = qty_query.filter(models.Order.source == source)
        if client:
            qty_query = qty_query.filter((models.Order.client_name.ilike(search_client)) | (models.Order.nip.ilike(search_client)))

        qty_results = qty_query.all()
        for date_val, qty_val in qty_results:
            if not date_val: continue
            date_key = date_val.strftime(date_format)
            if date_key not in stats:
                stats[date_key] = {"total_sales": 0.0, "quantity": 0, "count": 0}
            stats[date_key]["quantity"] += (qty_val or 0)

    result = []
    for date_k in sorted(stats.keys()):
        result.append({
            "month": date_k,
            "total_sales": stats[date_k]["total_sales"],
            "quantity": stats[date_k]["quantity"],
            "count": stats[date_k]["count"]
        })

    return result

@router.get("/stats/products", dependencies=[Depends(verify_token)])
def get_top_products(
    limit: int = 10, 
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    source: Optional[str] = None,
    client: Optional[str] = None,
    product: Optional[str] = None,
    sort_by: str = "qty", # 'qty' or 'value'
    db: Session = Depends(get_db)
):
    query = db.query(
        models.Item.name,
        func.sum(models.Item.quantity).label("total_qty"),
        func.sum(models.Item.quantity * models.Item.price).label("total_val") # Approx revenue
    ).join(models.Order).filter(models.Order.date.isnot(None))

    if date_from:
        try:
            d_from = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(models.Order.date >= d_from)
        except: pass
        
    if date_to:
        try:
            d_to = datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            query = query.filter(models.Order.date <= d_to)
        except: pass

    if source:
        query = query.filter(models.Order.source == source)
        
    if client:
        search_client = f"%{client}%"
        query = query.filter(
            (models.Order.client_name.like(search_client)) |
            (models.Order.nip.like(search_client))
        )

    if product:
        search_product = f"%{product}%"
        query = query.filter(
            (models.Item.name.ilike(search_product)) |
            (models.Item.sku.ilike(search_product))
        )

    # Exclude shipping from top products
    query = query.filter(
        ~models.Item.name.ilike("%wysyłka%"),
        ~models.Item.name.ilike("%GLS%")
    )

    query = query.group_by(models.Item.name)
    
    if sort_by == "value":
        query = query.order_by(desc("total_val"))
    else:
        query = query.order_by(desc("total_qty"))
        
    top_products = query.limit(limit).all()

    return [
        {"name": row.name, "quantity": row.total_qty, "revenue": row.total_val}
        for row in top_products
    ]

@router.get("/stats/summary", dependencies=[Depends(verify_token)])
def get_stats_summary(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    source: Optional[str] = None,
    client: Optional[str] = None,
    product: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Base query for items
    query = db.query(models.Item).join(models.Order).filter(models.Order.date.isnot(None))

    if date_from:
        try:
            d_from = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(models.Order.date >= d_from)
        except: pass
        
    if date_to:
        try:
            d_to = datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            query = query.filter(models.Order.date <= d_to)
        except: pass

    if source:
        query = query.filter(models.Order.source == source)
        
    if client:
        search_client = f"%{client}%"
        query = query.filter(
            (models.Order.client_name.like(search_client)) |
            (models.Order.nip.like(search_client))
        )

    if product:
        search_product = f"%{product}%"
        query = query.filter(
            (models.Item.name.ilike(search_product)) |
            (models.Item.sku.ilike(search_product))
        )

    # Calculate totals
    # We must fetch or use aggregates. Aggregates are faster.
    
    # 1. Total Product Revenue & Qty (excluding shipping)
    products_stats = query.filter(
        ~models.Item.name.ilike("%wysyłka%"),
        ~models.Item.name.ilike("%GLS%")
    ).with_entities(
        func.sum(models.Item.quantity * models.Item.price),
        func.sum(models.Item.quantity)
    ).first()
    
    total_revenue = products_stats[0] or 0.0
    total_qty = products_stats[1] or 0
    
    # 2. Shipping Costs (items matching shipping keywords)
    shipping_stats = query.filter(
        (models.Item.name.ilike("%wysyłka%")) | 
        (models.Item.name.ilike("%GLS%"))
    ).with_entities(
        func.sum(models.Item.quantity * models.Item.price)
    ).first()
    
    shipping_revenue = shipping_stats[0] or 0.0
    
    # Also check Order.shipping_cost field? 
    # The user asked to sum "Products with name 'wysyłka'".
    # But usually shipping is also in Order.shipping_cost. 
    # Let's sum Order.shipping_cost as well for completeness? 
    # User specifically said: "Produkty z nazwą ... pomin i umieść pod spodem jako wartość kosztów wysyłki"
    # So we strictly follow that for the "Shipping Costs" metric derived from items.
    
    return {
        "revenue": total_revenue,
        "quantity": total_qty,
        "shipping_cost": shipping_revenue
    }

@router.get("/sources", dependencies=[Depends(verify_token)])
def get_sources(db: Session = Depends(get_db)):
    # Get distinct sources
    sources = db.query(models.Order.source).distinct().filter(models.Order.source != "").all()
    # verify tuple unpacking
    return [s[0] for s in sources if s[0]]

@router.get("/files/{order_id}/{file_type}")
def get_file(order_id: str, file_type: str, token: str = Query(...), db: Session = Depends(get_db)):
    if token != PASSWORD:
        raise HTTPException(status_code=401, detail="Nieprawidlowe haslo")
    
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Zamowienie nie znalezione")
    
    doc_num = order.invoice_number if file_type == "invoice" else order.receipt_number
    if not doc_num:
        raise HTTPException(status_code=404, detail="Brak numeru dokumentu w bazie")

    if not drive_service:
        raise HTTPException(status_code=500, detail="Brak polaczenia z Dyskiem Google")

    # Wyszukiwanie pliku na Dysku
    clean_num_1 = doc_num.replace('/', '_').replace('\\', '_')
    clean_num_2 = doc_num.replace('/', '-')
    
    query = f"mimeType='application/pdf' and (name contains '{doc_num}' or name contains '{clean_num_1}' or name contains '{clean_num_2}')"
    results = drive_service.files().list(q=query, pageSize=1, fields="files(id, name)").execute()
    items = results.get('files', [])
    
    # Próba awaryjna po numerze zamówienia
    if not items:
        query_fallback = f"mimeType='application/pdf' and name contains '{order_id}'"
        results = drive_service.files().list(q=query_fallback, pageSize=1, fields="files(id, name)").execute()
        items = results.get('files', [])
        
    if not items:
        raise HTTPException(status_code=404, detail="Plik nie zostal odnaleziony na Dysku Google")

    file_id = items[0]['id']
    file_name = items[0]['name']

    # Strumieniowanie z Google do Przeglądarki Użytkownika
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    
    fh.seek(0)
    return StreamingResponse(fh, media_type="application/pdf", headers={"Content-Disposition": f"inline; filename={file_name}"})
