from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from models import db, Order, OrderItem, Customer, Product, ProductVariant, OrderStatus, PaymentStatus, OrderType
from datetime import datetime

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/')
def list_orders():
    """List all active orders with filters"""
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')
    
    query = Order.query.filter_by(is_deleted=False)
    
    if status_filter:
        query = query.filter_by(status=getattr(OrderStatus, status_filter.upper()))
    
    if search:
        # Search by order ID or customer name
        try:
            order_id = int(search)
            query = query.filter(
                (Order.id == order_id) | 
                (Customer.name.ilike(f'%{search}%'))
            )
        except ValueError:
            query = query.join(Customer).filter(Customer.name.ilike(f'%{search}%'))
    
    orders = query.order_by(Order.order_date.desc()).all()
    
    return render_template('orders/list.html', 
                         orders=orders, 
                         status_filter=status_filter, 
                         search=search,
                         statuses=OrderStatus)

@orders_bp.route('/create', methods=['GET', 'POST'])
def create_order():
    """Create new order with dynamic items"""
    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        order_type = request.form.get('order_type')
        
        if not customer_id or not order_type:
            flash('Please select customer and order type', 'danger')
            return redirect(url_for('orders.create_order'))
        
        # Create order
        order = Order(
            customer_id=customer_id,
            order_type=getattr(OrderType, order_type.upper()),
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.UNPAID
        )
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Add items
        product_variant_ids = request.form.getlist('product_variant_id[]')
        quantities = request.form.getlist('quantity[]')
        prices = request.form.getlist('price[]')
        
        total_amount = 0.0
        
        for i in range(len(product_variant_ids)):
            if product_variant_ids[i] and quantities[i]:
                variant_id = int(product_variant_ids[i])
                qty = int(quantities[i])
                price = float(prices[i])
                subtotal = qty * price
                
                item = OrderItem(
                    order_id=order.id,
                    product_variant_id=variant_id,
                    quantity=qty,
                    price_at_time=price,
                    subtotal=subtotal
                )
                db.session.add(item)
                total_amount += subtotal
        
        order.total_amount = total_amount
        db.session.commit()
        
        flash('Order created successfully!', 'success')
        return redirect(url_for('orders.view_order', id=order.id))
    
    # GET request - show form
    customers = Customer.query.order_by(Customer.name).all()
    products = Product.query.all()
    
    return render_template('orders/form.html', 
                         customers=customers, 
                         products=products,
                         order=None)

@orders_bp.route('/<int:id>')
def view_order(id):
    """View order details"""
    order = Order.query.get_or_404(id)
    return render_template('orders/view.html', order=order)

@orders_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit_order(id):
    """Edit order - only allowed if status is PENDING"""
    order = Order.query.get_or_404(id)
    
    if order.status != OrderStatus.PENDING:
        flash('Cannot edit order! Order is already in production.', 'warning')
        return redirect(url_for('orders.view_order', id=id))
    
    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        order_type = request.form.get('order_type')
        
        order.customer_id = customer_id
        order.order_type = getattr(OrderType, order_type.upper())
        
        # Remove old items
        OrderItem.query.filter_by(order_id=order.id).delete()
        
        # Add new items
        product_variant_ids = request.form.getlist('product_variant_id[]')
        quantities = request.form.getlist('quantity[]')
        prices = request.form.getlist('price[]')
        
        total_amount = 0.0
        
        for i in range(len(product_variant_ids)):
            if product_variant_ids[i] and quantities[i]:
                variant_id = int(product_variant_ids[i])
                qty = int(quantities[i])
                price = float(prices[i])
                subtotal = qty * price
                
                item = OrderItem(
                    order_id=order.id,
                    product_variant_id=variant_id,
                    quantity=qty,
                    price_at_time=price,
                    subtotal=subtotal
                )
                db.session.add(item)
                total_amount += subtotal
        
        order.total_amount = total_amount
        db.session.commit()
        
        flash('Order updated successfully!', 'success')
        return redirect(url_for('orders.view_order', id=id))
    
    # GET request - show form
    customers = Customer.query.order_by(Customer.name).all()
    products = Product.query.all()
    
    return render_template('orders/form.html', 
                         customers=customers, 
                         products=products,
                         order=order)

@orders_bp.route('/<int:id>/delete', methods=['GET', 'POST'])
def delete_order(id):
    """Soft delete order with reason"""
    order = Order.query.get_or_404(id)
    
    if order.status not in [OrderStatus.PENDING, OrderStatus.READY]:
        flash('Can only delete Pending or Ready orders!', 'danger')
        return redirect(url_for('orders.list_orders'))
    
    if request.method == 'POST':
        reason = request.form.get('delete_reason')
        note = request.form.get('delete_note')
        
        order.soft_delete(reason, note)
        db.session.commit()
        
        flash('Order deleted successfully!', 'success')
        return redirect(url_for('orders.list_orders'))
    
    return render_template('orders/delete_confirm.html', order=order)

@orders_bp.route('/<int:id>/status', methods=['POST'])
def update_status(id):
    """Update order status"""
    order = Order.query.get_or_404(id)
    new_status = request.form.get('status')
    
    if new_status:
        order.status = getattr(OrderStatus, new_status.upper())
        db.session.commit()
        flash(f'Order status updated to {new_status}!', 'success')
    
    return redirect(url_for('orders.view_order', id=id))

@orders_bp.route('/<int:id>/payment', methods=['POST'])
def update_payment(id):
    """Update payment status"""
    order = Order.query.get_or_404(id)
    new_status = request.form.get('payment_status')
    
    if new_status:
        order.payment_status = getattr(PaymentStatus, new_status.upper())
        db.session.commit()
        flash(f'Payment status updated to {new_status}!', 'success')
    
    return redirect(url_for('orders.view_order', id=id))

@orders_bp.route('/trash')
def trash():
    """View soft-deleted orders"""
    orders = Order.query.filter_by(is_deleted=True).order_by(Order.deleted_at.desc()).all()
    return render_template('orders/trash.html', orders=orders)

@orders_bp.route('/<int:id>/restore', methods=['POST'])
def restore_order(id):
    """Restore soft-deleted order"""
    order = Order.query.get_or_404(id)
    
    if not order.is_deleted:
        flash('Order is not deleted!', 'danger')
        return redirect(url_for('orders.list_orders'))
    
    order.is_deleted = False
    order.deleted_at = None
    order.delete_reason = None
    order.delete_note = None
    
    db.session.commit()
    flash('Order restored successfully!', 'success')
    return redirect(url_for('orders.trash'))

# API endpoint for getting product variants (for AJAX)
@orders_bp.route('/api/variants/<int:product_id>')
def get_variants(product_id):
    """Get variants for a product"""
    order_type = request.args.get('order_type', 'retail')
    variants = ProductVariant.query.filter_by(product_id=product_id, is_active=True).all()
    
    result = []
    for v in variants:
        price = v.retail_price if order_type == 'retail' else v.wholesale_price
        result.append({
            'id': v.id,
            'weight_label': v.weight_label,
            'price': float(price)
        })
    
    return jsonify(result)
