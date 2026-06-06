from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class HotelTable(Base):
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    image_url = Column(String(500), nullable=True)

    # Relationship to rooms
    rooms = relationship("RoomTable", back_populates="hotel")


class RoomTable(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"))
    type_name = Column(String(255), nullable=False)  # e.g., "Deluxe Single Room"
    price = Column(Integer, nullable=False)
    remaining = Column(Integer, default=0)  # Inventory

    hotel = relationship("HotelTable", back_populates="rooms")


class BookingTable(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), unique=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"))
    room_type = Column(String(255), nullable=False)
    customer_name = Column(String(255), nullable=False)
    quantity = Column(Integer, default=1)
    email = Column(String(255), nullable=False)
    passport = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Inverse relationship to access hotel info easily
    hotel = relationship("HotelTable")