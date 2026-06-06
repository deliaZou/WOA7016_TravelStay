from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL, connect_args
from models import Base, HotelTable, RoomTable

# Create engine for AWS RDS MySQL
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True if "mysql" in DATABASE_URL else False # 只有MySQL需要心跳检测
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Automatically creates all tables on AWS RDS and injects English mock data.
    """
    # 1. Trigger SQLAlchemy to auto-create missing tables on AWS
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 2. Inject initial data if the database is empty
        if not db.query(HotelTable).first():
            # Create a demo hotel with English values
            new_hotel = HotelTable(
                name="The Peninsula Resort",
                location="Sanya",
                image_url="https://via.placeholder.com/300"
            )
            db.add(new_hotel)
            db.commit()  # Commit to generate the auto-increment ID

            # Create room inventory for this hotel
            rooms = [
                RoomTable(hotel_id=new_hotel.id, type_name="Single Room", price=1299, remaining=5),
                RoomTable(hotel_id=new_hotel.id, type_name="Double Room", price=2199, remaining=2),
                RoomTable(hotel_id=new_hotel.id, type_name="Presidential Suite", price=8888, remaining=0)
            ]
            db.add_all(rooms)
            db.commit()
            print("Successfully initialized AWS RDS with English mock data!")
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        db.close()