from flask import Flask, render_template, flash, redirect, url_for
from models import db, Customer, Product, ProductVariant, Order, OrderItem, OrderStatus, PaymentStatus, OrderType
import os
from datetime import datetime, timedelta

def create_app():
    app = Flask(__name__)
    
    # Configuration - Offline SQLite for simplicity (can switch to MySQL)
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'khakhra.db')
    # For MySQL use: 'mysql+pymysql://user:password@localhost/khakhra_business'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'khakhra-secret-key-change-in-production'
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize Extensions
    db.init_app(app)
    
    # Register Blueprints
    from blueprints.main import main_bp
    from blueprints.customers import customers_bp
    from blueprints.products import products_bp
    from blueprints.orders import orders_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(customers_bp, url_prefix='/customers')
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(orders_bp, url_prefix='/orders')
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
        
        # Seed initial data if tables are empty
        if Product.query.count() == 0:
            seed_initial_data()
            
    return app

def seed_initial_data():
    """Helper to add default products if DB is empty"""
    print("Seeding initial data...")
    
    # Add sample products
    products_data = [
        {"name": "Plain Khakhra", "variants": [
            {"weight": "200g", "retail": 40.00, "wholesale": 35.00},
            {"weight": "500g", "retail": 90.00, "wholesale": 80.00},
            {"weight": "1kg", "retail": 170.00, "wholesale": 150.00}
        ]},
        {"name": "Masala Khakhra", "variants": [
            {"weight": "200g", "retail": 45.00, "wholesale": 40.00},
            {"weight": "500g", "retail": 100.00, "wholesale": 90.00},
            {"weight": "1kg", "retail": 190.00, "wholesale": 170.00}
        ]},
        {"name": "Jeera Khakhra", "variants": [
            {"weight": "200g", "retail": 42.00, "wholesale": 37.00},
            {"weight": "500g", "retail": 95.00, "wholesale": 85.00},
            {"weight": "1kg", "retail": 180.00, "wholesale": 160.00}
        ]}
    ]
    
    for prod_data in products_data:
        product = Product(name=prod_data["name"])
        db.session.add(product)
        db.session.commit()
        
        for var_data in prod_data["variants"]:
            variant = ProductVariant(
                product_id=product.id,
                weight_label=var_data["weight"],
                retail_price=var_data["retail"],
                wholesale_price=var_data["wholesale"],
                is_active=True
            )
            db.session.add(variant)
    
    # Add sample customer
    customer = Customer(name="Sample Customer", phone="9876543210", address="Sample Address")
    db.session.add(customer)
    
    db.session.commit()
    print("Initial data seeded.")

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
