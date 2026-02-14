from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, index=True)  # "Numer" (e.g. 119288253)
    client_name = Column(String, index=True)
    email = Column(String, index=True)
    phone = Column(String)
    nip = Column(String, index=True, nullable=True)
    address = Column(String)
    date = Column(DateTime)
    total = Column(Float)
    currency = Column(String)
    source = Column(String)
    shipping_method = Column(String, nullable=True) # "Sposób wysyłki"
    shipping_cost = Column(Float, default=0.0)      # "Koszt wysyłki"
    invoice_number = Column(String, index=True, nullable=True)
    receipt_number = Column(String, index=True, nullable=True)
    
    # Paths to files (computed during import or scan)
    invoice_path = Column(String, nullable=True)
    receipt_path = Column(String, nullable=True)

    items = relationship("Item", back_populates="order")

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, ForeignKey("orders.id"))
    name = Column(String)
    quantity = Column(Integer)
    price = Column(Float)
    sku = Column(String, nullable=True)

    order = relationship("Order", back_populates="items")
