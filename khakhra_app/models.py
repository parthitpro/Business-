from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum, CheckConstraint
from datetime import datetime
import enum

db = SQLAlchemy()

# Enums for Type Safety
class OrderStatus(enum.Enum):
    PENDING = 'pending'
    MANUFACTURING = 'manufacturing'
    READY = 'ready'
    DELIVERED = 'delivered'

class PaymentStatus(enum.Enum):
    UNPAID = 'unpaid'
    PAID = 'paid'

class OrderType(enum.Enum):
    RETAIL = 'retail'
    WHOLESALE = 'wholesale'

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    address = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship: One Customer has Many Orders
    orders = db.relationship('Order', backref='customer', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Customer {self.name}>'

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    
    # Relationship: One Product has Many Variants
    variants = db.relationship('ProductVariant', backref='product', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Product {self.name}>'

class ProductVariant(db.Model):
    __tablename__ = 'product_variants'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    weight_label = db.Column(db.String(50), nullable=False) # e.g., "200g", "1kg"
    retail_price = db.Column(db.Numeric(10, 2), nullable=False)
    wholesale_price = db.Column(db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationship: One Variant is in Many Order Items
    order_items = db.relationship('OrderItem', backref='variant', lazy=True)

    def __repr__(self):
        return f'<Variant {self.product.name} - {self.weight_label}>'

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    
    # Business Logic Fields
    order_type = db.Column(Enum(OrderType), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), default=0.00)
    
    # Workflow Status
    status = db.Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    payment_status = db.Column(Enum(PaymentStatus), default=PaymentStatus.UNPAID, nullable=False)
    
    # Soft Delete Logic
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    delete_reason = db.Column(db.String(255), nullable=True)
    delete_note = db.Column(db.Text, nullable=True)
    
    # Relationship: One Order has Many Items
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")

    def soft_delete(self, reason, note=None):
        """Helper method to handle soft deletion logic"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.delete_reason = reason
        self.delete_note = note

    def __repr__(self):
        return f'<Order #{self.id} - {self.customer.name}>'

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=False)
    
    quantity = db.Column(db.Integer, nullable=False)
    
    # Critical Business Logic: Price at time of order (allows overrides)
    price_at_time = db.Column(db.Numeric(10, 2), nullable=False)
    
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return f'<OrderItem {self.quantity} x {self.variant.weight_label}>'
