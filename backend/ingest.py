import os
import json
from database import db

DATA_DIR = r"D:\dodgeAI\dataset\sap-o2c-data"

def handle_business_partners(record):
    db.query("""
        INSERT INTO customers (id, name, category, group_code) VALUES (%s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name, category=EXCLUDED.category, group_code=EXCLUDED.group_code;
    """, (record.get("businessPartner"), record.get("businessPartnerFullName"), record.get("businessPartnerCategory"), record.get("businessPartnerGrouping")))

def handle_business_partner_addresses(record):
    db.query("""
        INSERT INTO customers (id, city, country, street) VALUES (%s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET city=EXCLUDED.city, country=EXCLUDED.country, street=EXCLUDED.street;
    """, (record.get("businessPartner"), record.get("cityName"), record.get("country"), record.get("streetName")))

def handle_customer_company_assignments(record):
    # FIXED: Check for 'customer' key first, fallback to 'businessPartner'
    cust_id = record.get("customer") or record.get("businessPartner")
    if not cust_id: return # Skip if somehow both are missing
    
    db.query("""
        INSERT INTO customers (id, companyCode) VALUES (%s, %s)
        ON CONFLICT (id) DO UPDATE SET companyCode=EXCLUDED.companyCode;
    """, (cust_id, record.get("companyCode")))

def handle_customer_sales_area_assignments(record):
    # FIXED: Check for 'customer' key first, fallback to 'businessPartner'
    cust_id = record.get("customer") or record.get("businessPartner")
    if not cust_id: return # Skip if somehow both are missing
    
    db.query("""
        INSERT INTO customers (id, salesOrg, distChannel) VALUES (%s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET salesOrg=EXCLUDED.salesOrg, distChannel=EXCLUDED.distChannel;
    """, (cust_id, record.get("salesOrganization"), record.get("distributionChannel")))

def handle_products(record):
    db.query("""
        INSERT INTO products (id, type, group_code, unit) VALUES (%s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET type=EXCLUDED.type, group_code=EXCLUDED.group_code, unit=EXCLUDED.unit;
    """, (record.get("product"), record.get("productType"), record.get("productGroup"), record.get("baseUnit")))

def handle_product_descriptions(record):
    db.query("""
        INSERT INTO products (id, description, language) VALUES (%s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET description=EXCLUDED.description, language=EXCLUDED.language;
    """, (record.get("product"), record.get("productDescription"), record.get("language")))

def handle_plants(record):
    db.query("""
        INSERT INTO plants (id, name, country) VALUES (%s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name, country=EXCLUDED.country;
    """, (record.get("plant"), record.get("plantName"), record.get("country")))

def handle_product_plants(record):
    db.query("""
        INSERT INTO product_plants (prod_id, plant_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;
    """, (record.get("product"), record.get("plant")))

def handle_product_storage_locations(record):
    db.query("""
        INSERT INTO product_storage (prod_id, plant_id, location) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;
    """, (record.get("product"), record.get("plant"), record.get("storageLocation")))

def handle_sales_order_headers(record):
    db.query("""
        INSERT INTO orders (id, date, amount, currency, type, cust_id) VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET date=EXCLUDED.date, amount=EXCLUDED.amount, currency=EXCLUDED.currency, type=EXCLUDED.type, cust_id=EXCLUDED.cust_id;
    """, (record.get("salesOrder"), record.get("creationDate"), record.get("totalNetAmount"), record.get("transactionCurrency"), record.get("salesOrderType"), record.get("soldToParty")))

def handle_sales_order_items(record):
    db.query("""
        INSERT INTO order_items (order_id, prod_id, qty, amount, item_id) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;
    """, (record.get("salesOrder"), record.get("material"), record.get("requestedQuantity"), record.get("netAmount"), record.get("salesOrderItem")))

def handle_sales_order_schedule_lines(record):
    db.query("""
        INSERT INTO orders (id, confirmedDeliveryDate) VALUES (%s, %s)
        ON CONFLICT (id) DO UPDATE SET confirmedDeliveryDate=EXCLUDED.confirmedDeliveryDate;
    """, (record.get("salesOrder"), record.get("confirmedDeliveryDate")))

def handle_outbound_delivery_headers(record):
    db.query("""
        INSERT INTO deliveries (id, deliveryDate, actualDate, shippingPoint) VALUES (%s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET deliveryDate=EXCLUDED.deliveryDate, actualDate=EXCLUDED.actualDate, shippingPoint=EXCLUDED.shippingPoint;
    """, (record.get("deliveryDocument"), record.get("deliveryDate"), record.get("actualGoodsMovementDate"), record.get("shippingPoint")))

def handle_outbound_delivery_items(record):
    db.query("""
        INSERT INTO delivery_items (del_id, order_id, prod_id, plant_id) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING;
    """, (record.get("deliveryDocument"), record.get("referenceSdDocument"), record.get("material"), record.get("plant")))

def handle_billing_document_headers(record):
    db.query("""
        INSERT INTO invoices (id, date, amount, currency, type) VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET date=EXCLUDED.date, amount=EXCLUDED.amount, currency=EXCLUDED.currency, type=EXCLUDED.type;
    """, (record.get("billingDocument"), record.get("creationDate"), record.get("totalNetAmount"), record.get("transactionCurrency"), record.get("billingDocumentType")))

def handle_billing_document_items(record):
    db.query("""
        INSERT INTO invoice_items (inv_id, ref_id, prod_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;
    """, (record.get("billingDocument"), record.get("referenceSdDocument"), record.get("material")))

def handle_billing_document_cancellations(record):
    db.query("""
        INSERT INTO invoices (id, cancelled, cancellationDate) VALUES (%s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET cancelled=EXCLUDED.cancelled, cancellationDate=EXCLUDED.cancellationDate;
    """, (record.get("billingDocument"), True, record.get("creationDate")))

def handle_journal_entry_items_accounts_receivable(record):
    db.query("""
        INSERT INTO journal_entries (id, date, amount, currency, account, ref_id) VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET date=EXCLUDED.date, amount=EXCLUDED.amount, currency=EXCLUDED.currency, account=EXCLUDED.account, ref_id=EXCLUDED.ref_id;
    """, (record.get("accountingDocument"), record.get("postingDate"), record.get("amountInTransactionCurrency"), record.get("transactionCurrency"), record.get("glAccount"), record.get("referenceDocument")))

def handle_payments_accounts_receivable(record):
    db.query("""
        INSERT INTO payments (id, amount, date, currency, ref_id) VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET amount=EXCLUDED.amount, date=EXCLUDED.date, currency=EXCLUDED.currency, ref_id=EXCLUDED.ref_id;
    """, (record.get("clearingAccountingDocument"), record.get("amountInTransactionCurrency"), record.get("clearingDate"), record.get("transactionCurrency"), record.get("invoiceReference")))


HANDLERS = {
    "business_partners": handle_business_partners,
    "business_partner_addresses": handle_business_partner_addresses,
    "customer_company_assignments": handle_customer_company_assignments,
    "customer_sales_area_assignments": handle_customer_sales_area_assignments,
    "products": handle_products,
    "product_descriptions": handle_product_descriptions,
    "plants": handle_plants,
    "product_plants": handle_product_plants,
    "product_storage_locations": handle_product_storage_locations,
    "sales_order_headers": handle_sales_order_headers,
    "sales_order_items": handle_sales_order_items,
    "sales_order_schedule_lines": handle_sales_order_schedule_lines,
    "outbound_delivery_headers": handle_outbound_delivery_headers,
    "outbound_delivery_items": handle_outbound_delivery_items,
    "billing_document_headers": handle_billing_document_headers,
    "billing_document_items": handle_billing_document_items,
    "billing_document_cancellations": handle_billing_document_cancellations,
    "journal_entry_items_accounts_receivable": handle_journal_entry_items_accounts_receivable,
    "payments_accounts_receivable": handle_payments_accounts_receivable,
}

INGEST_ORDER = list(HANDLERS.keys())

def create_tables():
    print("📌 Creating PostgreSQL Tables...")
    tables = [
        "CREATE TABLE IF NOT EXISTS customers (id TEXT PRIMARY KEY, name TEXT, category TEXT, group_code TEXT, city TEXT, country TEXT, street TEXT, companyCode TEXT, salesOrg TEXT, distChannel TEXT);",
        "CREATE TABLE IF NOT EXISTS products (id TEXT PRIMARY KEY, type TEXT, group_code TEXT, unit TEXT, description TEXT, language TEXT);",
        "CREATE TABLE IF NOT EXISTS plants (id TEXT PRIMARY KEY, name TEXT, country TEXT);",
        "CREATE TABLE IF NOT EXISTS product_plants (prod_id TEXT, plant_id TEXT, UNIQUE(prod_id, plant_id));",
        "CREATE TABLE IF NOT EXISTS product_storage (prod_id TEXT, plant_id TEXT, location TEXT, UNIQUE(prod_id, plant_id, location));",
        "CREATE TABLE IF NOT EXISTS orders (id TEXT PRIMARY KEY, date TEXT, amount TEXT, currency TEXT, type TEXT, cust_id TEXT, confirmedDeliveryDate TEXT);",
        "CREATE TABLE IF NOT EXISTS order_items (order_id TEXT, prod_id TEXT, qty TEXT, amount TEXT, item_id TEXT, UNIQUE(order_id, prod_id, item_id));",
        "CREATE TABLE IF NOT EXISTS deliveries (id TEXT PRIMARY KEY, deliveryDate TEXT, actualDate TEXT, shippingPoint TEXT);",
        "CREATE TABLE IF NOT EXISTS delivery_items (del_id TEXT, order_id TEXT, prod_id TEXT, plant_id TEXT, UNIQUE(del_id, order_id, prod_id));",
        "CREATE TABLE IF NOT EXISTS invoices (id TEXT PRIMARY KEY, date TEXT, amount TEXT, currency TEXT, type TEXT, cancelled BOOLEAN, cancellationDate TEXT);",
        "CREATE TABLE IF NOT EXISTS invoice_items (inv_id TEXT, ref_id TEXT, prod_id TEXT, UNIQUE(inv_id, ref_id, prod_id));",
        "CREATE TABLE IF NOT EXISTS journal_entries (id TEXT PRIMARY KEY, date TEXT, amount TEXT, currency TEXT, account TEXT, ref_id TEXT);",
        "CREATE TABLE IF NOT EXISTS payments (id TEXT PRIMARY KEY, amount TEXT, date TEXT, currency TEXT, ref_id TEXT);"
    ]
    for sql in tables:
        db.query(sql)
    print("✅ Tables ready.\n")

def ingest_folder(folder_name, folder_path):
    handler = HANDLERS.get(folder_name)
    ingested, errors = 0, 0
    for file in sorted(os.listdir(folder_path)):
        if not file.endswith(".jsonl"): continue
        file_path = os.path.join(folder_path, file)
        
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                # --- SPEED CAP: Remove 
                if ingested >= 150:
                    break


                line = line.strip()
                if not line: continue
                try:
                    record = json.loads(line)
                    handler(record)
                    ingested += 1
                except Exception as e:
                    errors += 1
    return ingested, errors

def ingest_data():
    if not os.path.exists(DATA_DIR):
        print(f"❌ Dataset folder not found: {DATA_DIR}")
        return

    print("🔌 Testing Postgres connection...")
    if not db.test_connection():
        return
    print("✅ Postgres connected.\n")

    create_tables()

    total_ingested = 0
    for folder_name in INGEST_ORDER:
        folder_path = os.path.join(DATA_DIR, folder_name)
        if os.path.exists(folder_path):
            print(f"📂 {folder_name}")
            ingested, errors = ingest_folder(folder_name, folder_path)
            total_ingested += ingested
            print(f"   → ✅ {ingested} records  ❌ {errors} errors")

    print(f"\n✅ INGESTION COMPLETE! Total records: {total_ingested}")

if __name__ == "__main__":
    ingest_data()