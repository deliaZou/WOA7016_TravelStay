import random
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from database import SessionLocal, primary_engine
from models import HotelTable, RoomTable, BookingTable
from schemas import HotelSchema, OrderCreateSchema
from prometheus_fastapi_instrumentator import Instrumentator


app = FastAPI(title="TravelStay Enterprise Backend API")
# auto generate  /metrics interface
Instrumentator().instrument(app).expose(app)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/hotels", response_model=List[HotelSchema])
async def get_hotels():
    """
    [Read Operation] Retrieve list of hotels with room inventories.
    Architect Tip: This read request can be distributed to Read Replicas in production.
    """
    db = SessionLocal()
    db.bind = primary_engine
    try:
        hotels = db.query(HotelTable).options(joinedload(HotelTable.rooms)).all()
        return hotels
    finally:
        db.close()


@app.post("/api/bookings")
async def create_booking(order: OrderCreateSchema):
    """
    [Write Operation] Submit a hotel room reservation.
    Architect Tip: Involves inventory deduction, must connect to RDS Primary Instance.
    """
    db = SessionLocal()
    try:
        # Input basic validations
        if order.quantity <= 0:
            raise HTTPException(status_code=400, detail="Booking quantity must be greater than 0.")
        if not order.customerName.strip():
            raise HTTPException(status_code=400, detail="Customer name cannot be empty.")

        # Check room type inventory from AWS RDS
        room = db.query(RoomTable).filter(
            RoomTable.hotel_id == order.hotelId,
            RoomTable.type_name == order.roomType
        ).first()

        if not room:
            raise HTTPException(status_code=404, detail="Requested room type or hotel not found.")

        # Check if stock is sufficient
        if room.remaining < order.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Inbound stock insufficient! Only {room.remaining} available, requested {order.quantity}."
            )

        # Deduct inventory safely
        room.remaining -= order.quantity

        # Generate unique English order reference ID
        generated_id = f"TS{random.randint(1000, 9999)}"

        # Save record to cloud database
        new_booking = BookingTable(
            order_id=generated_id,
            hotel_id=order.hotelId,
            room_type=order.roomType,
            customer_name=order.customerName,
            quantity=order.quantity,
            email=order.email,
            passport=order.passport
        )
        db.add(new_booking)
        db.commit()

        return {
            "status": "success",
            "order_id": generated_id,
            "message": "Reservation created successfully."
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()


@app.get("/api/orders/search")
async def search_order(query: str):
    """
    [Read Operation] Search reservations by order ID or customer name.
    """
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Search query parameter cannot be empty.")

    db = SessionLocal()
    try:
        search_filter = f"%{query.strip()}%"

        # Eager load hotel records using joinedload
        orders_db = db.query(BookingTable).options(joinedload(BookingTable.hotel)).filter(
            or_(
                BookingTable.order_id.ilike(search_filter),
                BookingTable.customer_name.ilike(search_filter)
            )
        ).all()

        results = []
        for order in orders_db:
            hotel_name = order.hotel.name if order.hotel else "Unknown Hotel"

            results.append({
                "order_id": order.order_id,
                "hotel": hotel_name,
                "customer": order.customer_name,
                "quantity": order.quantity,
                "status": "Confirmed"
            })

        return results
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn

    # 1. Trigger the cloud migration & data seeding first
    # init_db()
    # 2. Fire up the Uvicorn local web server
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


# Instrumentator().instrument(app).expose(app)