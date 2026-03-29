from flask import Blueprint, render_template
from models import db, Order, Customer, OrderStatus
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/dashboard')
def dashboard():
    """Dashboard with stats and recent orders"""
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Stats calculations
    today_orders = Order.query.filter(
        Order.order_date >= today_start,
        Order.is_deleted == False
    ).count()
    
    today_sales = db.session.query(db.func.sum(Order.total_amount)).filter(
        Order.order_date >= today_start,
        Order.is_deleted == False
    ).scalar() or 0.00
    
    pending_manufacturing = Order.query.filter(
        Order.status == OrderStatus.MANUFACTURING,
        Order.is_deleted == False
    ).count()
    
    ready_for_delivery = Order.query.filter(
        Order.status == OrderStatus.READY,
        Order.is_deleted == False
    ).count()
    
    # Recent orders (last 5)
    recent_orders = Order.query.filter_by(is_deleted=False).order_by(
        Order.order_date.desc()
    ).limit(5).all()
    
    return render_template('dashboard.html',
                         today_orders=today_orders,
                         today_sales=today_sales,
                         pending_manufacturing=pending_manufacturing,
                         ready_for_delivery=ready_for_delivery,
                         recent_orders=recent_orders)
