# Khakhra Business Management System

A complete offline Flask-based business management system for a Khakhra (food) business.

## 🚀 Features

### Section 1: Order Taking & Management
- **Dashboard**: Real-time stats (Today's Orders, Sales, Pending Manufacturing, Ready for Delivery)
- **Customer Management**: 
  - List, Add, Edit customers
  - CSV Import with duplicate detection and preview
  - Search by name/phone
- **Product Catalog**:
  - Products with multiple variants (weight/price)
  - Dynamic variant management
- **Order Management**:
  - Create orders with dynamic items
  - Retail/Wholesale pricing
  - Editable prices per order
  - Status workflow: Pending → Manufacturing → Ready → Delivered
  - Payment tracking: Unpaid/Paid
  - Soft delete with reason tracking
  - Trash view with restore capability

## 📁 Project Structure

```
khakhra_app/
├── app.py                 # Main application entry point
├── models.py              # SQLAlchemy database models
├── requirements.txt       # Python dependencies
├── khakhra.db            # SQLite database (auto-created)
├── uploads/              # CSV upload folder
├── blueprints/
│   ├── main.py           # Dashboard routes
│   ├── customers.py      # Customer management routes
│   ├── products.py       # Product catalog routes
│   └── orders.py         # Order management routes
├── templates/
│   ├── base.html         # Base template with navbar
│   ├── dashboard.html    # Dashboard view
│   ├── customers/
│   │   ├── list.html
│   │   ├── form.html
│   │   ├── import.html
│   │   └── import_preview.html
│   ├── products/
│   │   ├── list.html
│   │   └── form.html
│   └── orders/
│       ├── list.html
│       ├── form.html
│       ├── view.html
│       ├── delete_confirm.html
│       └── trash.html
└── static/
    ├── css/
    └── js/
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- pip

### Setup Steps

1. **Navigate to project directory**:
   ```bash
   cd khakhra_app
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Access the application**:
   Open your browser and go to: `http://localhost:5000`

## 🔧 Configuration

### Database
By default, the app uses SQLite (`khakhra.db`). To use MySQL:

1. Uncomment MySQL packages in `requirements.txt`:
   ```
   PyMySQL==1.1.0
   ```

2. Update `app.py` database URI:
   ```python
   app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://user:password@localhost/khakhra_business'
   ```

### Offline Mode
The application is designed to work completely offline:
- Bootstrap CSS/JS files should be placed in `static/css/` and `static/js/`
- CDN links are provided as fallback but are not required

To download Bootstrap for offline use:
```bash
# Download Bootstrap CSS
wget https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css -O static/css/bootstrap.min.css

# Download Bootstrap JS
wget https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js -O static/js/bootstrap.bundle.min.js
```

## 📋 Business Logic Implemented

1. **Price Override**: Prices can be overridden during order entry and are saved per order item
2. **Status Workflow**: Orders flow through: Pending → Manufacturing → Ready → Delivered
3. **Edit Lock**: Orders can only be edited when status is 'Pending'
4. **Soft Delete**: Deleted orders are marked with reason/note and can be restored
5. **CSV Import**: Google Contacts format supported with duplicate detection

## 🌐 Routes

| Route | Description |
|-------|-------------|
| `/` or `/dashboard` | Dashboard with stats |
| `/customers/` | List customers |
| `/customers/add` | Add customer |
| `/customers/edit/<id>` | Edit customer |
| `/customers/import` | Import CSV |
| `/products/` | List products |
| `/products/add` | Add product |
| `/products/edit/<id>` | Edit product |
| `/orders/` | List orders |
| `/orders/create` | Create order |
| `/orders/<id>` | View order |
| `/orders/<id>/edit` | Edit order (if pending) |
| `/orders/<id>/delete` | Soft delete order |
| `/orders/trash` | View deleted orders |
| `/orders/api/variants/<id>` | API: Get product variants |

## 📝 Sample Data

On first run, the database is seeded with:
- 3 Products (Plain, Masala, Jeera Khakhra)
- 3 Variants per product (200g, 500g, 1kg)
- 1 Sample customer

## 🔒 Security Features

- CSRF protection on all forms
- Input validation
- Soft delete prevents accidental data loss
- Status-based edit locking

## 📄 License

This project is for educational/business use.
