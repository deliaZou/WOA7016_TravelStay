from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# 1. two db link
PRIMARY_DB_URL = "mysql+pymysql://admin:TravelStay123!@travelstay-db.couwaczgmvhi.us-east-1.rds.amazonaws.com:3306/travelstay"
REPLICA_DB_URL = "mysql+pymysql://admin:TravelStay123!@travelstay-db-replica.couwaczgmvhi.us-east-1.rds.amazonaws.com:3306/travelstay"

# 2. two db Engine
primary_engine = create_engine(PRIMARY_DB_URL, pool_pre_ping=True)
replica_engine = create_engine(REPLICA_DB_URL, pool_pre_ping=True)

Base = declarative_base()


# 3. 核心：自定义 RoutingSession 实现智能分流
class RoutingSession(Session):
    def get_bind(self, mapper=None, clause=None, **kw):
        """
        每次执行 SQL 时，SQLAlchemy 都会调用这个方法来决定用哪个引擎
        """
        # 如果是编译好的 SQL 语句，且是以 SELECT 开头的，走只读副本
        if self._flushing:
            return primary_engine

        if clause is not None and hasattr(clause, "is_select") and clause.is_select:
            return replica_engine

        # 其余所有操作（INSERT, UPDATE, DELETE 等）全部走主库
        return primary_engine


# 4. 用刚才自定义的 RoutingSession 生成 SessionLocal
SessionLocal = sessionmaker(class_=RoutingSession, autocommit=False, autoflush=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()