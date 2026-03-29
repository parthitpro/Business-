from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from models import db, Customer, Order, OrderStatus
from datetime import datetime
import csv
import os

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/')
def list_customers():
    """List all customers with search"""
    search = request.args.get('search', '')
    
    query = Customer.query.filter_by()
    if search:
        query = query.filter(
            (Customer.name.ilike(f'%{search}%')) | 
            (Customer.phone.ilike(f'%{search}%'))
        )
    
    customers = query.order_by(Customer.name).all()
    return render_template('customers/list.html', customers=customers, search=search)

@customers_bp.route('/add', methods=['GET', 'POST'])
def add_customer():
    """Add new customer manually"""
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        # Check for duplicate phone
        existing = Customer.query.filter_by(phone=phone).first()
        if existing:
            flash('Customer with this phone number already exists!', 'danger')
            return redirect(url_for('customers.list_customers'))
        
        customer = Customer(name=name, phone=phone, address=address)
        db.session.add(customer)
        db.session.commit()
        
        flash('Customer added successfully!', 'success')
        return redirect(url_for('customers.list_customers'))
    
    return render_template('customers/form.html', customer=None)

@customers_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_customer(id):
    """Edit existing customer"""
    customer = Customer.query.get_or_404(id)
    
    if request.method == 'POST':
        customer.name = request.form.get('name')
        customer.phone = request.form.get('phone')
        customer.address = request.form.get('address')
        
        db.session.commit()
        flash('Customer updated successfully!', 'success')
        return redirect(url_for('customers.list_customers'))
    
    return render_template('customers/form.html', customer=customer)

@customers_bp.route('/import', methods=['GET', 'POST'])
def import_csv():
    """Import customers from CSV file"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        if file and file.filename.endswith('.csv'):
            # Save file temporarily
            upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, file.filename)
            file.save(filepath)
            
            # Parse CSV
            new_customers = []
            duplicates = []
            updates = []
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        name = row.get('Name', '').strip()
                        phone = row.get('Phone', '').strip()
                        address = row.get('Address', '').strip()
                        
                        if not name or not phone:
                            continue
                        
                        existing = Customer.query.filter_by(phone=phone).first()
                        if existing:
                            updates.append({'name': name, 'phone': phone, 'address': address, 'existing_id': existing.id})
                        else:
                            new_customers.append({'name': name, 'phone': phone, 'address': address})
                
                # Store in session for preview
                session['import_data'] = {
                    'new': new_customers,
                    'updates': updates,
                    'filepath': filepath
                }
                
                return render_template('customers/import_preview.html', 
                                     new_customers=new_customers, 
                                     updates=updates)
            
            except Exception as e:
                flash(f'Error parsing CSV: {str(e)}', 'danger')
                return redirect(request.url)
        else:
            flash('Please upload a valid CSV file', 'danger')
            return redirect(request.url)
    
    return render_template('customers/import.html')

@customers_bp.route('/import/confirm', methods=['POST'])
def confirm_import():
    """Confirm and save imported customers"""
    import_data = session.pop('import_data', None)
    
    if not import_data:
        flash('No import data found', 'danger')
        return redirect(url_for('customers.import_csv'))
    
    count_new = 0
    count_update = 0
    
    # Add new customers
    for cust in import_data['new']:
        customer = Customer(name=cust['name'], phone=cust['phone'], address=cust['address'])
        db.session.add(customer)
        count_new += 1
    
    # Update existing customers
    for cust in import_data['updates']:
        customer = Customer.query.get(cust['existing_id'])
        if customer:
            customer.name = cust['name']
            customer.address = cust['address']
            count_update += 1
    
    db.session.commit()
    
    # Clean up file
    if import_data.get('filepath') and os.path.exists(import_data['filepath']):
        os.remove(import_data['filepath'])
    
    flash(f'Import completed! {count_new} new customers added, {count_update} updated.', 'success')
    return redirect(url_for('customers.list_customers'))
