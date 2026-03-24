import os
from fastapi import FastAPI, HTTPException
from groq import Groq
from database import db
from models import ChatRequest
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# THE ULTIMATE SCHEMA CONTEXT
# We explicitly tell the AI about ALL tables and how to query them simply
SCHEMA_CONTEXT = """
You are a PostgreSQL expert for a SAP Order-to-Cash system.
Respond ONLY with raw SQL. No markdown. No explanations.

TABLES:
- customers (id, name, city)
- orders (id, date, amount, cust_id)
- order_items (order_id, prod_id, qty)
- products (id, type, description)
- product_plants (prod_id, plant_id)
- deliveries (id, deliveryDate, shippingPoint) -- shippingPoint acts as plant_id
- delivery_items (del_id, order_id, prod_id)
- invoice_items (inv_id, ref_id) -- ref_id links to order_id OR del_id
- journal_entries (id, date, amount, ref_id) -- ref_id links to inv_id

QUERY RULES:
1. SIMPLE LISTS: If a user asks for a simple list (e.g., "list all products", "give me plant ids", "give me list of customer id"), do NOT do a complex join. Just query the table directly:
   - "list of customer id" -> SELECT id FROM customers;
   - "show products" -> SELECT id, type FROM products;
   - "show plants" -> SELECT DISTINCT plant_id FROM product_plants;

2. TRACING FLOW (CRITICAL): If a user asks to "trace", "find the flow", or mentions a specific document ID, you MUST return a WIDE JOIN of the entire process so the UI can draw the connections.
   
   EXAMPLE TRACE SQL:
   SELECT 
     c.name as customer_name, 
     o.id as order_id, 
     oi.prod_id as product_id,
     di.del_id as delivery_id, 
     ii.inv_id as invoice_id, 
     je.id as journal_id
   FROM orders o
   JOIN customers c ON o.cust_id = c.id
   LEFT JOIN order_items oi ON o.id = oi.order_id
   LEFT JOIN delivery_items di ON o.id = di.order_id
   LEFT JOIN invoice_items ii ON (o.id = ii.ref_id OR di.del_id = ii.ref_id)
   LEFT JOIN journal_entries je ON ii.inv_id = je.ref_id
   WHERE o.id = '740530' OR ii.inv_id = '91150187' OR je.id = '9400635958';

3. GUARDRAILS: If the query is not about SAP/Orders/Customers/Products/Plants, return: GUARDRAIL_VIOLATION.
"""

@app.get("/initial-graph")
async def get_initial_graph():
    try:
        all_data = []

        # Query 1: Customer → Order (core chain)
        q1 = """
            SELECT c.name as customer_name, o.id as order_id
            FROM orders o JOIN customers c ON o.cust_id = c.id
            LIMIT 30
        """
        all_data.extend(db.query(q1))

        # Query 2: Order → Order Item → Product
        q2 = """
            SELECT o.id as order_id, oi.prod_id as product_id, p.type as product_type
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            LEFT JOIN products p ON p.id = oi.prod_id
            LIMIT 40
        """
        all_data.extend(db.query(q2))

        # Query 3: Order → Delivery Item → Delivery → Plant
        q3 = """
            SELECT o.id as order_id, di.del_id as delivery_id, d.shippingPoint as plant_id
            FROM delivery_items di
            JOIN orders o ON o.id = di.order_id
            JOIN deliveries d ON d.id = di.del_id
            LIMIT 40
        """
        all_data.extend(db.query(q3))

        # Query 4: Delivery → Invoice
        q4 = """
            SELECT di.del_id as delivery_id, ii.inv_id as invoice_id
            FROM invoice_items ii
            JOIN delivery_items di ON di.del_id = ii.ref_id
            LIMIT 40
        """
        all_data.extend(db.query(q4))

        # Query 5: Invoice → Journal Entry
        q5 = """
            SELECT ii.inv_id as invoice_id, je.id as journal_id
            FROM journal_entries je
            JOIN invoice_items ii ON ii.inv_id = je.ref_id
            LIMIT 40
        """
        all_data.extend(db.query(q5))

        # Query 6: Invoice → Payment
        q6 = """
            SELECT ii.inv_id as invoice_id, p.id as payment_id
            FROM payments p
            JOIN invoice_items ii ON ii.inv_id = p.ref_id
            LIMIT 40
        """
        all_data.extend(db.query(q6))

        # Query 7: Product → Plant (via product_plants)
        q7 = """
            SELECT pp.prod_id as product_id, pp.plant_id as plant_id
            FROM product_plants pp
            LIMIT 40
        """
        all_data.extend(db.query(q7))

        return {"data": all_data}
    except Exception as e:
        print(f"initial-graph error: {e}")
        return {"data": []}

@app.post("/query")
async def handle_query(request: ChatRequest):
    try:
        # 1. AI writes the SQL
        sql_response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": SCHEMA_CONTEXT},
                {"role": "user", "content": request.message} 
            ],
            temperature=0
        )
        
        generated_sql = sql_response.choices[0].message.content.strip()
        generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()

        if "GUARDRAIL_VIOLATION" in generated_sql:
            return {
                "query": None, "data": [],
                "explanation": "This system is designed to answer questions related to the provided dataset only."
            }

        print(f"DEBUG SQL: {generated_sql}") # Keep this for debugging

        # 2. Execute SQL
        raw_results = db.query(generated_sql)
        
        # Guard clause: if the database returns an empty list
        if not raw_results:
             return {
                 "query": generated_sql,
                 "data": [],
                 "explanation": "**No Results Found**\n---\nI could not find any records matching your request in the current dataset."
             }

        # 3. Explain
        explanation = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": """
                    You are a SAP Dashboard Assistant. 
                    FORMATTING RULES:
                    1. Use a Bold Heading for the summary.
                    2. Use a '---' horizontal rule.
                    3. Simple 2 - 3 lines answer
                """},
                {"role": "user", "content": f"User asked: {request.message} \n Data found: {raw_results}"}
            ]
        )

        return {
            "query": generated_sql,
            "data": raw_results,
            "explanation": explanation.choices[0].message.content
        }
    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))