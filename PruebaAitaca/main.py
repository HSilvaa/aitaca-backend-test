"""
Abrir pgAdmin4 y conectarte al servidor

Abrir la terminal de python y poner: uvicorn main:app --reload

Cargar en el navegador la pagina http://127.0.0.1:8000

@app.post("/products", response_model=dict)
curl -X POST http://127.0.0.1:8000/products -H "Content-Type: application/json" -d "{\"name\": \"Producto de prueba\", \"description\": \"Este es un producto de prueba\", \"price\": 10.99, \"quantity\": 100}"

@app.get("/products", response_model=List[dict])
curl -X GET "http://127.0.0.1:8000/products?skip=0&limit=10"

@app.get("/products/{product_id}", response_model=dict)
-X GET "http://127.0.0.1:8000/products/3"

@app.put("/products/{product_id}", response_model=dict)
curl -X PUT "http://127.0.0.1:8000/products/6" -H "Content-Type: application/json" -H "accept: application/json" -d "{\"name\": \"Updated Product Name\"}"

@app.delete("/products/{product_id}", response_model=dict)
curl -X DELETE "http://127.0.0.1:8000/products/3"
"""


from typing import List

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime, func
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Product Model
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Método to_dict para convertir la instancia a un diccionario
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "quantity": self.quantity
        }

# Create database tables
Base.metadata.create_all(bind=engine)

# FastAPI instance
app = FastAPI()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create a Product
@app.post("/products", response_model=dict)
def create_product(product: dict, db: Session = Depends(get_db)):
    # Crear el nuevo producto
    new_product = Product(**product)
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    # Devolver como diccionario
    return {
        "id": new_product.id,
        "name": new_product.name,
        "description": new_product.description,
        "price": new_product.price,
        "quantity": new_product.quantity,
        "created_at": new_product.created_at
    }


# Get All Products with Pagination
@app.get("/products", response_model=List[dict])
def get_products(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    # Consulta los productos desde la base de datos
    products = db.query(Product).offset(skip).limit(limit).all()
    # Convierte cada producto a un diccionario usando el método `to_dict`
    return [product.to_dict() for product in products]


# Get a Product by ID
@app.get("/products/{product_id}", response_model=dict)
def get_product_by_id(product_id: int, db: Session = Depends(get_db)):
    # Busca el producto
    product = db.query(Product).filter(Product.id == product_id).first()

    # Si no encuentra el producto, lanza un error 404
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Devuelve el producto como diccionario
    return product.to_dict()


# Update a Product
@app.put("/products/{product_id}", response_model=dict)
def update_product(product_id: int, updated_data: dict, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for key, value in updated_data.items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product.to_dict()  # Usa el método to_dict()



# Delete a Product
@app.delete("/products/{product_id}", response_model=dict)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}
