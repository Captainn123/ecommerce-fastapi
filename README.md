# E-Commerce Backend API (FastAPI)

A robust, production-ready RESTful API built for a modern E-Commerce platform. This project serves as a comprehensive backend demonstrating enterprise-level architecture, security, and business logic.

## 🚀 Tech Stack
* **Framework:** FastAPI (Python)
* **Database:** SQLite (Development) / Ready for PostgreSQL
* **ORM:** SQLAlchemy
* **Authentication:** JSON Web Tokens (JWT) & bcrypt hashing
* **Validation:** Pydantic

## 🎯 Key Features
* **Role-Based Access Control (RBAC):** Secure endpoints distinguishing between `admin` (can manage inventory) and `customer` (can place orders).
* **Secure Authentication:** Implementation of OAuth2 password flow with JWT tokens. Passwords are securely hashed using `bcrypt` (bypassing deprecated passlib dependencies).
* **Complex Transaction Logic:** Order processing automatically verifies product existence, validates sufficient stock, deducts inventory, and calculates total pricing securely on the server side.
* **Asynchronous Processing:** Utilizes FastAPI `BackgroundTasks` to process order confirmation emails outside the main request thread, ensuring lightning-fast API response times.
* **Secrets Management:** Fully integrated with `python-dotenv` to ensure API keys and database URLs are never exposed in the source code.

## ⚙️ How to Run Locally

1. **Clone the repository**
2. **Create a virtual environment:** `python -m venv venv`
3. **Activate the environment:** `.\venv\Scripts\activate` (Windows)
4. **Install dependencies:** `pip install -r requirements.txt`
5. **Set up Environment Variables:** Create a `.env` file and add your `SECRET_KEY` and `DATABASE_URL`.
6. **Run the server:** `uvicorn main:app --reload`
7. **View Documentation:** Open `http://127.0.0.1:8000/docs` to interact with the auto-generated Swagger UI.