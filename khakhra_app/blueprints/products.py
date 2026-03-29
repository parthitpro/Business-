from flask import Blueprint, render_template, request, flash, redirect, url_for
from models import db, Product, ProductVariant

products_bp = Blueprint('products', __name__)

@products_bp.route('/')
def list_products():
    """List all products with variants"""
    products = Product.query.all()
    return render_template('products/list.html', products=products)

@products_bp.route('/add', methods=['GET', 'POST'])
def add_product():
    """Add new product with variants"""
    if request.method == 'POST':
        name = request.form.get('name')
        
        # Check for duplicate
        existing = Product.query.filter_by(name=name).first()
        if existing:
            flash('Product with this name already exists!', 'danger')
            return redirect(url_for('products.list_products'))
        
        product = Product(name=name)
        db.session.add(product)
        db.session.commit()
        
        # Add variants
        weights = request.form.getlist('weight[]')
        retail_prices = request.form.getlist('retail_price[]')
        wholesale_prices = request.form.getlist('wholesale_price[]')
        
        for i in range(len(weights)):
            if weights[i] and retail_prices[i]:
                variant = ProductVariant(
                    product_id=product.id,
                    weight_label=weights[i],
                    retail_price=float(retail_prices[i]),
                    wholesale_price=float(wholesale_prices[i]) if wholesale_prices[i] else float(retail_prices[i]),
                    is_active=True
                )
                db.session.add(variant)
        
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('products.list_products'))
    
    return render_template('products/form.html', product=None)

@products_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    """Edit product and variants"""
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        
        # Remove old variants
        ProductVariant.query.filter_by(product_id=product.id).delete()
        
        # Add new variants
        weights = request.form.getlist('weight[]')
        retail_prices = request.form.getlist('retail_price[]')
        wholesale_prices = request.form.getlist('wholesale_price[]')
        
        for i in range(len(weights)):
            if weights[i] and retail_prices[i]:
                variant = ProductVariant(
                    product_id=product.id,
                    weight_label=weights[i],
                    retail_price=float(retail_prices[i]),
                    wholesale_price=float(wholesale_prices[i]) if wholesale_prices[i] else float(retail_prices[i]),
                    is_active=True
                )
                db.session.add(variant)
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('products.list_products'))
    
    return render_template('products/form.html', product=product)

@products_bp.route('/delete/<int:id>', methods=['POST'])
def delete_product(id):
    """Delete product (hard delete since no orders reference it directly)"""
    product = Product.query.get_or_404(id)
    
    # Check if any variant is used in orders
    has_orders = ProductVariant.query.join(OrderItem).filter(
        ProductVariant.product_id == id
    ).first()
    
    if has_orders:
        flash('Cannot delete product with existing orders!', 'danger')
        return redirect(url_for('products.list_products'))
    
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('products.list_products'))

# Import OrderItem here to avoid circular imports
from models import OrderItem
