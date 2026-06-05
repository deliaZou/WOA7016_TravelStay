from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
import random
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, joinedload
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import DateTime
from datetime import datetime
from sqlalchemy import or_

app = FastAPI(title="TravelStay Backend API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 允许所有来源，生产环境建议缩窄范围
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. SQLite 配置 ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./travelstay.db" # 数据会存放在当前目录的这个文件里
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. 定义数据库模型 (ORM) ---
# --- 数据库模型 ---

class HotelTable(Base):
    __tablename__ = "hotels"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    location = Column(String)
    image_url = Column(String)
    # 建立关联：方便查询酒店时直接带出房间
    rooms = relationship("RoomTable", back_populates="hotel")

class RoomTable(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id")) # 外键关联
    type_name = Column(String)  # 例如：豪华单人房
    price = Column(Integer)
    remaining = Column(Integer) # 剩余数量
    
    hotel = relationship("HotelTable", back_populates="rooms")


class BookingTable(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"))  # 保持外键
    room_type = Column(String)
    customer_name = Column(String)

    # 新增以下三个字段：
    quantity = Column(Integer, default=1)  # 预订房间数量
    email = Column(String)  # 客户邮箱
    passport = Column(String)  # 护照号
    created_at = Column(DateTime, default=datetime.now)

    # 可选：建立反向关联，方便订单直接.hotel.name拿到酒店名
    hotel = relationship("HotelTable")

# --- 3. 初始化数据库（创建表并注入 Demo 数据） ---
Base.metadata.create_all(bind=engine)

def init_db():
    db = SessionLocal()
    if not db.query(HotelTable).first():
        # 1. 创建酒店
        new_hotel = HotelTable(
            name="半岛度假酒店", 
            location="三亚", 
            image_url="https://via.placeholder.com/300"
        )
        db.add(new_hotel)
        db.commit() # 先提交酒店以获取 ID
        
        # 2. 创建该酒店的房间
        rooms = [
            RoomTable(hotel_id=new_hotel.id, type_name="单人房", price=1299, remaining=5),
            RoomTable(hotel_id=new_hotel.id, type_name="双人房", price=2199, remaining=2),
            RoomTable(hotel_id=new_hotel.id, type_name="总统套房", price=8888, remaining=0) # 售罄测试
        ]
        db.add_all(rooms)
        db.commit()
    db.close()


# --- 架构师定义：数据库端点 (通常通过环境变量注入) ---
# 对应架构中的 RDS Master (写)
RDS_MASTER_URL = "travelstay-master.xyz.us-east-1.rds.amazonaws.com"
# 对应架构中的 RDS Read Replica (读)
RDS_REPLICA_URL = "travelstay-replica.xyz.us-east-1.rds.amazonaws.com"

# --- 数据模型 ---
class RoomType(BaseModel):
    # type: str
    # price: int
    # remaining: int
    model_config = ConfigDict(from_attributes=True)

    type: str = Field(validation_alias="type_name", serialization_alias="type")
    price: int
    remaining: int

    # class Config:
    #     from_attributes = True

class Hotel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str
    # 同理，从数据库的 'image_url' 读取，发给前端时变成 'imageUrl'
    imageUrl: str = Field(validation_alias="image_url", serialization_alias="imageUrl")
    rooms: List[RoomType]
    # id: int
    # name: str
    # location: str
    # imageUrl: str
    # rooms: List[RoomType]
    #
    # class Config:
    #     from_attributes = True

class OrderCreate(BaseModel):
    hotelId: int
    roomType: str
    customerName: str
    quantity: int      # 新增：预订数量
    email: str         # 新增：邮箱
    passport: str      # 新增：护照

# --- API 接口实现 ---

@app.get("/api/hotels", response_model=List[Hotel])
async def get_hotels():
    """
    【读操作】获取酒店列表
    架构师提示：此请求应分流至 RDS Read Replica 以优化性能。
    """
    # db = SessionLocal()
    # # hotels = db.query(HotelTable).all()
    # hotels = db.query(HotelTable).options(joinedload(HotelTable.rooms)).all()
    # # 转换为前端需要的格式
    # result = []
    # for h in hotels:
    #     result.append({
    #         "id": h.id,
    #         "name": h.name,
    #         "location": h.location,
    #         "imageUrl": h.image_url,
    #         "rooms": [{"type": "豪华单人房", "price": 1299, "remaining": 5}] # 简易 Demo
    #     })
    # db.close()
    # return result
    db = SessionLocal()
    try:
        # 使用 joinedload 强制一次性把关联的 rooms 查出来
        hotels = db.query(HotelTable).options(joinedload(HotelTable.rooms)).all()
        print(f"第一个酒店的房间数量: {hotels}") # 看看控制台输出了几
        return hotels
    finally:
        db.close()

@app.post("/api/bookings")
async def create_booking(order: OrderCreate):
    """
    【写操作】提交预订订单
    架构师提示：涉及金额和库存更新，必须连接 RDS Master 确保数据强一致性。
    """
    db = SessionLocal()
    try:
        # 输入基本校验
        if order.quantity <= 0:
            raise HTTPException(status_code=400, detail="预订数量必须大于 0")
        if not order.customerName.strip():
            raise HTTPException(status_code=400, detail="客户姓名不能为空")

        # 查询对应酒店和房型的库存
        room = db.query(RoomTable).filter(
            RoomTable.hotel_id == order.hotelId,
            RoomTable.type_name == order.roomType
        ).first()

        if not room:
            raise HTTPException(status_code=404, detail="未找到该房型信息")

        # 核心逻辑：校验用户买的数量是否超过剩余库存
        if room.remaining < order.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"库存不足！当前房型仅剩 {room.remaining} 间，无法预订 {order.quantity} 间。"
            )

        # 【扣减库存】：减去用户购买的具体数量
        room.remaining -= order.quantity

        # 【生成订单】：带上完整的表单数据
        generated_id = f"TS{random.randint(1000, 9999)}"
        new_booking = BookingTable(
            order_id=generated_id,
            hotel_id=order.hotelId,
            room_type=order.roomType,
            customer_name=order.customerName,
            quantity=order.quantity,  # 写入数量
            email=order.email,  # 写入邮箱
            passport=order.passport  # 写入护照
        )
        db.add(new_booking)
        db.commit()

        return {
            "status": "success",
            "order_id": generated_id,
            "message": "预订成功"
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="服务器内部错误")
    finally:
        db.close()

@app.get("/api/orders/search")
async def search_order(query: str):
    """
    【读操作】搜索订单
    架构师提示：查询历史数据，连接 Read Replica。
    """
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="请输入搜索关键词")

    db = SessionLocal()
    try:
        search_filter = f"%{query.strip()}%"

        # 使用 joinedload(BookingTable.hotel) 连表查出酒店真实信息
        orders_db = db.query(BookingTable).options(joinedload(BookingTable.hotel)).filter(
            or_(
                BookingTable.order_id.ilike(search_filter),
                BookingTable.customer_name.ilike(search_filter)
            )
        ).all()

        results = []
        for order in orders_db:
            # 安全反查酒店名称：如果有关联的酒店就拿真实名字，没有就兜底显示
            hotel_name = order.hotel.name if order.hotel else "未知酒店"

            results.append({
                "order_id": order.order_id,
                "hotel": hotel_name,  # 这里已经是动态从数据库查到的真实酒店名了！
                "customer": order.customer_name,
                "quantity": order.quantity,
                "status": "Confirmed"
            })

        return results
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    # 在 8000 端口启动
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)