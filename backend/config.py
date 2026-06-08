import urllib.parse

# =====================================================================
# 🎛️ 环境切换总开关
# 填 "local"       -> 运行本地数据库 (可选择 MySQL 或 SQLite)
# 填 "production"  -> 运行 AWS 云端数据库
# =====================================================================
RUNNING_ENV = "production"  # 👈 想连云端时，只需要把这里改成 "production"

# --- 1. AWS 云端数据库配置 ---
CLOUD_USER = "admin"
CLOUD_PASSWORD = "TravelStay123!"  # 你的密码
CLOUD_HOST = "travelstay-db-subnet-group.couwaczgmvhi.us-east-1.rds.amazonaws.com"
CLOUD_PORT = "3306"
CLOUD_NAME = "travelstay"
CLOUD_SAFE_PWD = urllib.parse.quote_plus(CLOUD_PASSWORD)

# --- 2. 本地数据库配置 (以本地 MySQL 为例，如果用 SQLite 见下方) ---
LOCAL_USER = "root"
LOCAL_PASSWORD = "your_local_password"
LOCAL_HOST = "127.0.0.1"
LOCAL_PORT = "3306"
LOCAL_NAME = "travelstay"
LOCAL_SAFE_PWD = urllib.parse.quote_plus(LOCAL_PASSWORD)

# --- 3. 动态判断并生成最终的连接字符串 ---
if RUNNING_ENV == "production":
    print("🚀 [System Notification] Connecting to AWS Cloud Database...")
    DATABASE_URL = f"mysql+pymysql://{CLOUD_USER}:{CLOUD_SAFE_PWD}@{CLOUD_HOST}:{CLOUD_PORT}/{CLOUD_NAME}"
    connect_args = {}
else:
    print("💻 [System Notification] Connecting to LOCAL Database...")

    DATABASE_URL = "sqlite:///./travelstay.db"
    connect_args = {"check_same_thread": False}