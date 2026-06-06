from pydantic import BaseModel, ConfigDict, Field
from typing import List

class RoomTypeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type: str = Field(validation_alias="type_name", serialization_alias="type")
    price: int
    remaining: int


class HotelSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str
    imageUrl: str = Field(validation_alias="image_url", serialization_alias="imageUrl")
    rooms: List[RoomTypeSchema]


class OrderCreateSchema(BaseModel):
    hotelId: int
    roomType: str
    customerName: str
    quantity: int
    email: str
    passport: str