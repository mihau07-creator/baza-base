from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime
from fastapi.responses import FileResponse
import os

from .database import get_db
from . import models

router = APIRouter(prefix="/api")

@router.get("/search")
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

@router.get("/order/{order_id}")
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

@router.get("/stats/sales")
def get_sales_stats(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    source: Optional[str] = None,
    client: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Order.date, models.Order.total).filter(models.Order.date.isnot(None))
    
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

    # Query 1: Sales (from Orders)
    orders = query.all()
    
    stats = {}
    for o in orders:
        if not o.date: continue
        month_key = o.date.strftime("%Y-%m")
        if month_key not in stats:
            stats[month_key] = {"total_sales": 0.0, "quantity": 0, "count": 0}
        stats[month_key]["total_sales"] += (o.total or 0.0)
        stats[month_key]["count"] += 1

    # Query 2: Quantity (from Items) - Aggregated by Order Date
    # We need to filter items but group by Order Date (Month)
    # It's cleaner to fetch all relevant items with their order dates
    
    qty_query = db.query(models.Order.date, models.Item.quantity)\
        .join(models.Order)\
        .filter(models.Order.date.isnot(None))\
        .filter(
            ~models.Item.name.ilike("%wysyłka%"),
            ~models.Item.name.ilike("%GLS%")
        )
        
    # Apply same filters to qty_query
    if date_from:
        try:
            d_from = datetime.strptime(date_from, "%Y-%m-%d")
            qty_query = qty_query.filter(models.Order.date >= d_from)
        except: pass
    if date_to:
        try:
            d_to = datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            qty_query = qty_query.filter(models.Order.date <= d_to)
        except: pass
    if source:
        qty_query = qty_query.filter(models.Order.source == source)
    if client:
        search_client = f"%{client}%"
        qty_query = qty_query.filter(
            (models.Order.client_name.like(search_client)) |
            (models.Order.nip.like(search_client))
        )

    # Execute Qty Query
    # Note: Fetching raw tuples (date, quantity)
    # This might be many rows (one per item). 
    # For 30k orders with avg 3 items = 90k rows. 
    # Ideally we group by Month in SQL but date manipulation in SQL is dialect specific (SQLite vs others).
    # Since we use Python datetime in model, let's fetch and aggregate. RAM should be fine for <100k rows.
    
    qty_results = qty_query.all()
    
    for date_val, qty_val in qty_results:
        if not date_val: continue
        month_key = date_val.strftime("%Y-%m")
         # Ensure key exists (in case order has items but 0 total or somehow missed in first query - though unlikely if joins match)
        if month_key not in stats:
            stats[month_key] = {"total_sales": 0.0, "quantity": 0, "count": 0}
        stats[month_key]["quantity"] += (qty_val or 0)

    # Convert to list and sort
    result = []
    for month in sorted(stats.keys()):
        result.append({
            "month": month,
            "total_sales": stats[month]["total_sales"],
            "quantity": stats[month]["quantity"],
            "count": stats[month]["count"]
        })

    return result

@router.get("/stats/products")
def get_top_products(
    limit: int = 10, 
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    source: Optional[str] = None,
    client: Optional[str] = None,
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

@router.get("/stats/summary")
def get_stats_summary(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    source: Optional[str] = None,
    client: Optional[str] = None,
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

@router.get("/sources")
def get_sources(db: Session = Depends(get_db)):
    # Get distinct sources
    sources = db.query(models.Order.source).distinct().filter(models.Order.source != "").all()
    # verify tuple unpacking
    return [s[0] for s in sources if s[0]]

@router.get("/files/{order_id}/{file_type}")
def get_file(order_id: str, file_type: str, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    file_path = None
    if file_type == "invoice":
        file_path = order.invoice_path
    elif file_type == "receipt":
        file_path = order.receipt_path
    else:
        raise HTTPException(status_code=400, detail="Invalid file type")
        
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
        
    return FileResponse(file_path)
