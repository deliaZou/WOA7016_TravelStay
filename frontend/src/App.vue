<template>
  <div class="travelstay-container">
    <header>
      <h1>TravelStay 豪华酒店预订系统</h1>
      <p class="tagline">Security-First | Luxury Experience</p>
      <div class="header-actions">
        <button class="btn-search-trigger" @click="showSearchModal = true">🔍 查找我的订单</button>
      </div>
    </header>

    <div v-if="loading" class="loading">加载中...</div>
    
    <div v-else class="hotel-grid">
      <div v-for="hotel in hotels" :key="hotel.id" class="hotel-card">
        <img :src="hotel.imageUrl" @click="zoomImage(hotel.imageUrl)" alt="Hotel Image" class="hotel-img" />
        
        <div class="hotel-info">
          <h2>{{ hotel.name }}</h2>
          <p class="location">{{ hotel.location }}</p>
          
          <div class="room-types">
            <h3>房型选择：</h3>
            <ul>
              <li v-for="room in hotel.rooms" :key="room.type" class="room-item">
                <span>{{ room.type }} - ￥{{ room.price }}</span>
                
                <button 
                  :disabled="room.remaining <= 0" 
                  @click="openBookingModal(hotel, room)"
                  :class="{ 'btn-disabled': room.remaining <= 0 }"
                >
                  {{ room.remaining > 0 ? '立即预订' : '已售罄' }}
                </button>
                <span class="stock-label">仅剩 {{ room.remaining }} 间</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showModal" class="modal">
      <div class="modal-content">
        <h2>确认预订: {{ selectedHotel?.name }}</h2>
        <p>房型: {{ selectedRoom?.type }}</p>
        <input v-model.number="number" type="number" placeholder="预定数量" />
        <input v-model="customerName" placeholder="客户姓名" />
        <input v-model="email" placeholder="客户邮箱" />
        <input v-model="passport" placeholder="护照号" />
        <div class="actions">
          <button @click="submitBooking">提交订单</button>
          <button @click="showModal = false">取消</button>
        </div>
      </div>
    </div>

    <div v-if="showSearchModal" class="modal">
      <div class="modal-content">
        <h2>订单查询</h2>
        <div class="search-box">
          <input v-model="searchQuery" placeholder="请输入订单号或姓名" />
          <button @click="handleSearch">SEARCH</button>
        </div>
        <div v-if="searchResult" class="result-area">
          <p><strong>status:</strong> comfirmed</p>
          <p><strong>hotel:</strong> {{ searchResult.hotel }}</p>
          <p><strong>customer name:</strong> {{ searchResult.customer }}</p>
          <p><strong>order ID:</strong> {{ searchResult.order_id }}</p>
          <p><strong>room count:</strong> {{ searchResult.quantity }}</p>
        </div>
        <button class="close-btn" @click="showSearchModal = false">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

// 1. 统一 API 地址
const API_BASE_URL = 'http://127.0.0.1:8000/api';

// 2. 基础状态控制
const hotels = ref([]);
const loading = ref(true);
const showModal = ref(false);
const showSearchModal = ref(false);

// 3. 预定表单数据绑定的响应式变量
const selectedHotel = ref(null);
const selectedRoom = ref(null);
const number = ref(1);
const customerName = ref('');
const email = ref('');
const passport = ref('');

// 4. 搜索功能变量
const searchQuery = ref('');
const searchResult = ref(null);

// 获取酒店列表
const fetchHotels = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/hotels`);
    hotels.value = response.data;
    loading.value = false;
  } catch (error) {
    console.error("获取酒店失败:", error);
    loading.value = false;
  }
};

// 打开预定弹窗
const openBookingModal = (hotel, room) => {
  selectedHotel.value = hotel;
  selectedRoom.value = room;
  showModal.value = true;
};

// 提交订单功能
const submitBooking = async () => {
  // 核心修改：使用 .trim() 替换 .strip
  if (!customerName.value || !customerName.value.trim() || !email.value || !email.value.trim()) {
    return alert("请完善客户姓名与邮箱");
  }

  try {
    const response = await axios.post(`${API_BASE_URL}/bookings`, {
      customerName: customerName.value,
      email: email.value,
      passport: passport.value,
      quantity: parseInt(number.value), // 修复：对应后端的 quantity 字段
      hotelId: selectedHotel.value.id,
      roomType: selectedRoom.value.type
    });

    if (response.data.status === 'success') {
      alert(`预订成功！单号：${response.data.order_id}`);

      // 自动刷新页面最新库存
      fetchHotels();

      // 关闭弹窗并重置表单变量
      showModal.value = false;
      customerName.value = '';
      email.value = '';
      passport.value = '';
      number.value = 1;
    }
  } catch (err) {
    alert(err.response?.data?.detail || "下单失败，请检查网络");
  }
};

// 搜索功能逻辑（修复：已移出外部，大括号完全闭合）
const handleSearch = async () => {
  // 核心修改：使用 .trim() 替换 .strip
  if (!searchQuery.value || !searchQuery.value.trim()) {
    return alert("请输入查询内容");
  }

  try {
    const response = await axios.get(`${API_BASE_URL}/orders/search`, {
      params: { query: searchQuery.value.trim() }
    });

    if (response.data && response.data.length > 0) {
      searchResult.value = response.data[0];
    } else {
      alert("未找到相关订单");
      searchResult.value = null;
    }
  } catch (error) {
    alert("搜索发生错误");
    searchResult.value = null;
  }
};

const zoomImage = (url) => {
  window.open(url, '_blank');
};

onMounted(fetchHotels);
</script>

<style scoped>
.btn-search-trigger { background: #f39c12; color: white; border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer; }
.travelstay-container { padding: 20px; font-family: sans-serif; }
.hotel-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
.hotel-card { border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }
.hotel-img { width: 100%; height: 200px; object-fit: cover; cursor: pointer; }
.hotel-info { padding: 15px; }
.room-item { margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
.btn-disabled { background-color: #ccc; cursor: not-allowed; }
.stock-label { font-size: 0.8em; color: #666; }
.modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 999; }
.modal-content { background: white; padding: 30px; border-radius: 10px; width: 300px; }
.search-box { margin-bottom: 15px; display: flex; gap: 5px; }
.result-area { background: #f9f9f9; padding: 10px; border-radius: 5px; margin-bottom: 15px; text-align: left; }
.close-btn { margin-top: 10px; width: 100%; }
</style>