from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.sql.selectable import Select

# 1. two db link
PRIMARY_DB_URL = "mysql+pymysql://admin:TravelStay123!@travelstay-db-subnet-group.couwaczgmvhi.us-east-1.rds.amazonaws.com:3306/travelstay"
REPLICA_DB_URL = "mysql+pymysql://admin:TravelStay123!@travelstay-db-replica1.couwaczgmvhi.us-east-1.rds.amazonaws.com:3306/travelstay"

# 2. two db Engine
primary_engine = create_engine(PRIMARY_DB_URL, pool_pre_ping=True)
replica_engine = create_engine(REPLICA_DB_URL, pool_pre_ping=True)

Base = declarative_base()


# 3. 核心：自定义 RoutingSession 实现智能分流
class RoutingSession(Session):
    def get_bind(self, mapper=None, clause=None, **kw):
        if self._flushing:
            return primary_engine
        if isinstance(clause, Select):
            return replica_engine
        return primary_engine


# 4. 用刚才自定义的 RoutingSession 生成 SessionLocal
SessionLocal = sessionmaker(class_=RoutingSession, autocommit=False, autoflush=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()