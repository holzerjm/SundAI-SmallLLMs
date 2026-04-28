"""The task all three experiments share: text-to-SQL over a fixed schema.

Replace this with whatever task you actually care about. Keep the same shape:
- SCHEMA / SYSTEM constants
- TASKS list with {question, expected_keywords / expected_query / grader}
- run(client, model, question) -> response string
- grade(question, response) -> (bool, reason)
"""
import re
import sqlite3


SCHEMA = """
CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, country TEXT);
CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, amount REAL, ordered_at DATE);
"""


SYSTEM = f"""You translate natural-language questions into SQLite queries.

Schema:
{SCHEMA}

Rules:
- Output ONLY the SQL query, no explanation, no code fences.
- Use SQLite syntax.
- Always alias aggregated columns clearly.
"""


# Each task: question + executable validation. The reference query is just used
# by the grader to compute the "correct" output set; the model never sees it.
TASKS = [
    {
        "id": "avg_order_per_customer_2024",
        "question": "What is the average order amount per customer in 2024? Include the customer name.",
        "reference_sql": """
            SELECT c.name, AVG(o.amount) AS avg_amount
            FROM customers c JOIN orders o ON c.id = o.customer_id
            WHERE strftime('%Y', o.ordered_at) = '2024'
            GROUP BY c.id, c.name
        """,
    },
    {
        "id": "top_country_by_revenue",
        "question": "Which country has the highest total revenue?",
        "reference_sql": """
            SELECT c.country, SUM(o.amount) AS total
            FROM customers c JOIN orders o ON c.id = o.customer_id
            GROUP BY c.country
            ORDER BY total DESC
            LIMIT 1
        """,
    },
    {
        "id": "customers_with_no_orders",
        "question": "List the names of customers who have not placed any orders.",
        "reference_sql": """
            SELECT c.name FROM customers c
            LEFT JOIN orders o ON c.id = o.customer_id
            WHERE o.id IS NULL
        """,
    },
    {
        "id": "monthly_revenue_2024",
        "question": "What is the total revenue per month in 2024?",
        "reference_sql": """
            SELECT strftime('%Y-%m', ordered_at) AS month, SUM(amount) AS total
            FROM orders
            WHERE strftime('%Y', ordered_at) = '2024'
            GROUP BY month
            ORDER BY month
        """,
    },
]


def fixture_db() -> sqlite3.Connection:
    """In-memory DB with sample rows. Used by the grader."""
    db = sqlite3.connect(":memory:")
    db.executescript(SCHEMA)
    db.executemany("INSERT INTO customers VALUES (?,?,?)", [
        (1, "Ada", "UK"), (2, "Grace", "US"), (3, "Linus", "FI"), (4, "Margaret", "US"),
    ])
    db.executemany("INSERT INTO orders VALUES (?,?,?,?)", [
        (1, 1, 100.0, "2024-01-15"), (2, 1, 200.0, "2024-03-02"),
        (3, 2, 50.0, "2024-02-20"), (4, 2, 75.0, "2023-12-30"),
        (5, 3, 300.0, "2024-06-11"),
    ])
    return db


def extract_sql(text: str) -> str:
    """Strip code fences and stray prose."""
    text = text.strip()
    m = re.search(r"```(?:sql)?\s*\n?(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return text


def run(client, model: str, question: str) -> str:
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]
    from client import chat
    return chat(client, model, msgs, temperature=0.0)


def grade(task: dict, response: str) -> tuple[bool, str]:
    """Run both queries on the fixture DB and compare result sets."""
    sql = extract_sql(response)
    db = fixture_db()
    try:
        actual = sorted(db.execute(sql).fetchall())
    except sqlite3.Error as e:
        return False, f"sql failed: {e}"
    expected = sorted(db.execute(task["reference_sql"]).fetchall())
    if actual != expected:
        return False, f"got {actual}, expected {expected}"
    return True, "ok"
