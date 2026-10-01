from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import List
from fastapi import HTTPException
import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import BackgroundTasks
import time

import models, schemas
from database import engine, SessionLocal

import os
from dotenv import load_dotenv

# Load the secrets from the .env file
load_dotenv()

# --- SECURITY UTILS ---
# Now it grabs the secret securely from your computer, not the code!
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="E-Commerce Capstone API")

# Dependency: This opens a database connection for a request, then safely closes it
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {"message": "Server is running! Welcome to the E-Commerce API."}

# --- NEW PRODUCT ENDPOINTS ---

# --- SECURITY UTILS ---
SECRET_KEY = "my_super_secret_capstone_key" # In real apps, this goes in a secure .env file
ALGORITHM = "HS256"

# This tells FastAPI where our login route is, so Swagger UI can use it!
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_bytes.decode('utf-8')

# NEW: Function to check if a typed password matches the database hash
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# NEW: Function to create the digital VIP wristband (Token)
def create_access_token(data: dict):
    to_encode = data.copy()
    # Token expires in 30 minutes for security
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# NEW: The "Bouncer" that protects our routes
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials - Please log in",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 1. Crack open the token using our secret key
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 2. Extract the user_id we hid inside it during login
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
            
    except jwt.InvalidTokenError: # If the token is fake or expired
        raise credentials_exception
    
    # 3. Find the user in the database
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception
        
    return user
# NEW Bouncer: Checks if the logged-in user is an Admin
def get_admin_user(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403, # 403 Forbidden means "I know who you are, but you aren't allowed here"
            detail="Not enough privileges. Admins only."
        )
    return current_user

# --- USER ENDPOINTS ---
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. Find the user by email (FastAPI forms use 'username', but we map it to our email)
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    
    # 2. Check if user exists AND password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    # 3. Generate the token! We store the user's ID inside the token.
    access_token = create_access_token(data={"user_id": user.id})
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Check if the email is already registered
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Hash the password
    hashed_password = get_password_hash(user.password)

    # 3. Create the database model (using the hashed password, NOT the raw one)
    new_user = models.User(email=user.email, hashed_password=hashed_password, role=user.role)
    
    # 4. Save to database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

def send_order_confirmation_email(email: str, order_id: int):
    # We use time.sleep(3) to simulate a slow email server taking 3 seconds
    time.sleep(3)
    print(f"\n✅ EMAIL ALERT: Order #{order_id} confirmation successfully sent to {email}!\n")
# --- ORDER ENDPOINTS ---

@app.post("/orders/", response_model=schemas.OrderResponse)
def create_order(
    order_req: schemas.OrderCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)): # <-- THIS IS THE MAGIC!):
    # Because of `current_user`, FastAPI will NOT let anyone reach this line of code 
    # unless they are logged in with a valid token.
    
    # Create the empty Order using the SECURE current_user.id
    new_order = models.Order(user_id=current_user.id, total_price=0.0)
    db.add(new_order)
    db.commit() 
    db.refresh(new_order)

    total_price = 0.0


    # 3. Loop through every item the user wants to buy
    for item in order_req.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} not found")
        
        # Check stock!
        if product.stock_quantity < item.quantity:
            raise HTTPException(status_code=400, detail=f"Not enough stock for {product.name}")

        # Deduct the stock from inventory
        product.stock_quantity -= item.quantity
        
        # Calculate the cost for this specific item
        item_cost = product.price * item.quantity
        total_price += item_cost

        # Create the OrderItem and link it to our Order
        order_item = models.OrderItem(
            order_id=new_order.id,
            product_id=product.id,
            quantity=item.quantity
        )
        db.add(order_item)

    # 4. Update the final total price and save everything
    new_order.total_price = total_price
    db.commit()
    db.refresh(new_order)
    background_tasks.add_task(send_order_confirmation_email, current_user.email, new_order.id)

    return new_order

@app.get("/orders/", response_model=List[schemas.OrderResponse])
def get_my_orders(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user) # Bouncer protects this too!
):
    # Fetch ONLY the orders that belong to the logged-in user
    user_orders = db.query(models.Order).filter(models.Order.user_id == current_user.id).all()
    return user_orders


# 1. POST Endpoint to create a new product
@app.post("/products/", response_model=schemas.ProductResponse)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db),
     admin_user: models.User = Depends(get_admin_user)):
    # Convert schema to a database model
    db_product = models.Product(**product.model_dump())
    
    # Save it to the database
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    return db_product

# 2. GET Endpoint to list all products
@app.get("/products/", response_model=List[schemas.ProductResponse])
def read_products(db: Session = Depends(get_db)):
    # Fetch all products from the database
    products = db.query(models.Product).all()
    return products