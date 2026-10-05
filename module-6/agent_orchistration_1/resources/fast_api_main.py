
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="Customer API",
    description="Simple FastAPI application for learning",
    version="1.0.0"
)


# Request model
class Customer(BaseModel):
    customer_id: str
    customer_name: str
    email: str
    city: str | None = None
    state: str | None = None


# Temporary in-memory database
customers = []


@app.get("/")
def home():
    return {
        "message": "FastAPI server is running"
    }


@app.get("/customers")
def get_customers():
    return {
        "success": True,
        "data": customers
    }


@app.get("/customers/{customer_id}")
def get_customer(customer_id: str):

    for customer in customers:
        if customer["customer_id"] == customer_id:
            return {
                "success": True,
                "data": customer
            }

    return {
        "success": False,
        "message": "Customer not found"
    }


@app.post("/customers")
def create_customer(customer: Customer):

    customers.append(customer.model_dump())

    return {
        "success": True,
        "message": "Customer created successfully",
        "data": customer
    }


@app.put("/customers/{customer_id}")
def update_customer(customer_id: str, customer: Customer):

    for index, existing_customer in enumerate(customers):

        if existing_customer["customer_id"] == customer_id:

            customers[index] = customer.model_dump()

            return {
                "success": True,
                "message": "Customer updated successfully",
                "data": customers[index]
            }

    return {
        "success": False,
        "message": "Customer not found"
    }


@app.delete("/customers/{customer_id}")
def delete_customer(customer_id: str):

    for index, customer in enumerate(customers):

        if customer["customer_id"] == customer_id:

            deleted_customer = customers.pop(index)

            return {
                "success": True,
                "message": "Customer deleted successfully",
                "data": deleted_customer
            }

    return {
        "success": False,
        "message": "Customer not found"
    }

if __name__ == "__main__":
    # Import uvicorn server
    import uvicorn

    # Run the FastAPI application
    # host="0.0.0.0" makes it accessible from other machines
    # port=8000 is the default HTTP port for the API
    uvicorn.run(
        app,  # FastAPI application instance
        host="127.0.0.1",  # Listen on all network interfaces
        port=8000,  # Port number
        log_level="info"  # Uvicorn log level
    )