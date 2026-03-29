from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from models import db, Order, OrderItem, Customer, ProductVariant, Product, OrderStatus, PaymentStatus, OrderType
from datetime import datetime
from sqlalchemy import or_

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')

@orders_bp.route('/')
def order_list():
    """List all active orders with filtering and search"""
    status_filter = request.args.get('status', '')
    search_query = request.args.get('search', '')
    
    # Base query - exclude soft deleted orders
    query = Order.query.filter_by(is_deleted=False)
    
    # Apply filters
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if search_query:
        # Search by Order ID or Customer Name
        query = query.join(Customer).filter(
            or_(
                Order.id.like(f'%{search_query}%'),
                Customer.name.ilike(f'%{search_query}%')
            )
        )
    
    orders = query.order_by(Order.order_date.desc()).all()
    return render_template('orders/order_list.html', 
                         orders=orders, 
                         statuses=OrderStatus,
                         current_status=status_filter,
                         search_query=search_query)

@orders_bp.route('/create', methods=['GET', 'POST'])
def create_order():
    """Create a new order with dynamic items"""
    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        order_type = request.form.get('order_type')
        items_data = request.form.get('items_data')  # JSON string from frontend
        
        if not customer_id or not items_data:
            flash('Customer and at least one item are required.', 'error')
            return redirect(url_for('orders.create_order'))
        
        import json
        try:
            items = json.loads(items_data)
        except:
            flash('Invalid item data.', 'error')
            return redirect(url_for('orders.create_order'))
        
        if not items:
            flash('At least one item is required.', 'error')
            return redirect(url_for('orders.create_order'))
        
        # Create Order
        order = Order(
            customer_id=customer_id,
            order_type=OrderType(order_type),
            order_date=datetime.utcnow(),
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.UNPAID
        )
        
        total_amount = 0
        seen_variants = set()
        
        for item in items:
            variant_id = item.get('variant_id')
            quantity = int(item.get('quantity', 0))
            price = float(item.get('price', 0))
            
            if quantity <= 0:
                continue
                
            # Prevent duplicate variants
            if variant_id in seen_variants:
                continue
            seen_variants.add(variant_id)
            
            variant = ProductVariant.query.get(variant_id)
            if not variant:
                continue
            
            subtotal = quantity * price
            total_amount += subtotal
            
            order_item = OrderItem(
                order=order,
                variant=variant,
                quantity=quantity,
                price_at_time=price,
                subtotal=subtotal
            )
            db.session.add(order_item)
        
        order.total_amount = total_amount
        db.session.add(order)
        db.session.commit()
        
        flash(f'Order #{order.id} created successfully!', 'success')
        return redirect(url_for('orders.order_view', order_id=order.id))
    
    # GET request - show form
    customers = Customer.query.order_by(Customer.name).all()
    products = Product.query.filter_by().all()
    return render_template('orders/order_form.html', 
                         customers=customers, 
                         products=products,
                         order_types=OrderType)

@orders_bp.route('/<int:order_id>')
def order_view(order_id):
    """View order details"""
    order = Order.query.get_or_404(order_id)
    return render_template('orders/order_view.html', order=order)

@orders_bp.route('/<int:order_id>/edit', methods=['GET', 'POST'])
def edit_order(order_id):
    """Edit order - only allowed if status is PENDING"""
    order = Order.query.get_or_404(order_id)
    
    if order.status != OrderStatus.PENDING:
        flash('Cannot edit order: Order is already in production.', 'error')
        return redirect(url_for('orders.order_view', order_id=order.id))
    
    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        order_type = request.form.get('order_type')
        items_data = request.form.get('items_data')
        
        import json
        try:
            items = json.loads(items_data)
        except:
            flash('Invalid item data.', 'error')
            return redirect(url_for('orders.edit_order', order_id=order.id))
        
        # Update order basics
        order.customer_id = customer_id
        order.order_type = OrderType(order_type)
        
        # Remove existing items
        for item in order.items:
            db.session.delete(item)
        
        total_amount = 0
        seen_variants = set()
        
        for item in items:
            variant_id = item.get('variant_id')
            quantity = int(item.get('quantity', 0))
            price = float(item.get('price', 0))
            
            if quantity <= 0:
                continue
                
            # Prevent duplicate variants
            if variant_id in seen_variants:
                continue
            seen_variants.add(variant_id)
            
            variant = ProductVariant.query.get(variant_id)
            if not variant:
                continue
            
            subtotal = quantity * price
            total_amount += subtotal
            
            order_item = OrderItem(
                order=order,
                variant=variant,
                quantity=quantity,
                price_at_time=price,
                subtotal=subtotal
            )
            db.session.add(order_item)
        
        order.total_amount = total_amount
        db.session.commit()
        
        flash(f'Order #{order.id} updated successfully!', 'success')
        return redirect(url_for('orders.order_view', order_id=order.id))
    
    # GET request - prepare form data
    customers = Customer.query.order_by(Customer.name).all()
    products = Product.query.all()
    
    # Serialize existing items for the form
    existing_items = []
    for item in order.items:
        existing_items.append({
            'variant_id': item.product_variant_id,
            'product_name': item.variant.product.name,
            'weight_label': item.variant.weight_label,
            'quantity': item.quantity,
            'price': float(item.price_at_time),
            'subtotal': float(item.subtotal)
        })
    
    return render_template('orders/order_form.html',
                         customers=customers,
                         products=products,
                         order_types=OrderType,
                         order=order,
                         existing_items=existing_items)

@orders_bp.route('/<int:order_id>/delete', methods=['POST'])
def delete_order(order_id):
    """Soft delete an order"""
    order = Order.query.get_or_404(order_id)
    
    if order.status not in [OrderStatus.PENDING, OrderStatus.READY]:
        flash('Can only delete Pending or Ready orders.', 'error')
        return redirect(url_for('orders.order_list'))
    
    reason = request.form.get('delete_reason')
    note = request.form.get('delete_note')
    
    order.soft_delete(reason=reason, note=note)
    db.session.commit()
    
    flash(f'Order #{order.id} moved to trash.', 'warning')
    return redirect(url_for('orders.order_list'))

@orders_bp.route('/<int:order_id>/status', methods=['POST'])
def update_status(order_id):
    """Update order status"""
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    
    if new_status in [s.value for s in OrderStatus]:
        order.status = OrderStatus(new_status)
        db.session.commit()
        flash(f'Order #{order.id} status updated to {new_status}.', 'success')
    else:
        flash('Invalid status.', 'error')
    
    return redirect(url_for('orders.order_view', order_id=order.id))

@orders_bp.route('/<int:order_id>/payment', methods=['POST'])
def update_payment(order_id):
    """Update payment status"""
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('payment_status')
    
    if new_status in [s.value for s in PaymentStatus]:
        order.payment_status = PaymentStatus(new_status)
        db.session.commit()
        flash(f'Order #{order.id} payment status updated.', 'success')
    else:
        flash('Invalid payment status.', 'error')
    
    return redirect(url_for('orders.order_view', order_id=order.id))

@orders_bp.route('/trash')
def order_trash():
    """View soft-deleted orders"""
    orders = Order.query.filter_by(is_deleted=True).order_by(Order.deleted_at.desc()).all()
    return render_template('orders/order_trash.html', orders=orders)

@orders_bp.route('/trash/<int:order_id>/restore', methods=['POST'])
def restore_order(order_id):
    """Restore a soft-deleted order"""
    order = Order.query.get_or_404(order_id)
    
    if not order.is_deleted:
        flash('Order is not deleted.', 'error')
        return redirect(url_for('orders.order_trash'))
    
    order.is_deleted = False
    order.deleted_at = None
    order.delete_reason = None
    order.delete_note = None
    db.session.commit()
    
    flash(f'Order #{order.id} restored successfully!', 'success')
    return redirect(url_for('orders.order_trash'))

# API Endpoints for AJAX
@orders_bp.route('/api/variants/<int:product_id>')
def get_variants(product_id):
    """Get variants for a product (API for AJAX)"""
    variants = ProductVariant.query.filter_by(product_id=product_id, is_active=True).all()
    
    # Serialize manually to avoid JSON errors
    result = []
    for v in variants:
        result.append({
            'id': v.id,
            'weight_label': v.weight_label,
            'retail_price': float(v.retail_price),
            'wholesale_price': float(v.wholesale_price)
        })
    
    return jsonify(result)

@orders_bp.route('/api/customers/search')
def search_customers():
    """Search customers by name or phone (API for AJAX)"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    customers = Customer.query.filter(
        or_(
            Customer.name.ilike(f'%{query}%'),
            Customer.phone.like(f'%{query}%')
        )
    ).limit(10).all()
    
    # Serialize manually
    result = []
    for c in customers:
        result.append({
            'id': c.id,
            'name': c.name,
            'phone': c.phone
        })
    
    return jsonify(result)
