<template>
  <div class="travelstay-container">
    <header>
      <h1>TravelStay Luxury Hotel Booking</h1>
      <p class="tagline">Security-First | Luxury Experience</p>
      <div class="header-actions">
        <button class="btn-search-trigger" @click="showSearchModal = true">🔍 search my booking</button>
      </div>
    </header>

    <div v-if="loading" class="loading">loading...</div>
    
    <div v-else class="hotel-grid">
      <div v-for="hotel in hotels" :key="hotel.id" class="hotel-card">
        <img :src="hotel.imageUrl" @click="zoomImage(hotel.imageUrl)" alt="Hotel Image" class="hotel-img" />
        
        <div class="hotel-info">
          <h2>{{ hotel.name }}</h2>
          <p class="location">{{ hotel.location }}</p>
          
          <div class="room-types">
            <h3>Room Type：</h3>
            <ul>
              <li v-for="room in hotel.rooms" :key="room.type" class="room-item">
                <span>{{ room.type }} - $ {{ room.price }}</span>
                
                <button 
                  :disabled="room.remaining <= 0" 
                  @click="openBookingModal(hotel, room)"
                  :class="{ 'btn-disabled': room.remaining <= 0 }"
                >
                  {{ room.remaining > 0 ? 'order' : 'Sold out' }}
                </button>
                <span class="stock-label"> {{ room.remaining }} left</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showModal" class="modal">
      <div class="modal-content">
        <h2>comfirm: {{ selectedHotel?.name }}</h2>
        <p>room type: {{ selectedRoom?.type }}</p>
        <input v-model.number="number" type="number" placeholder="amount" />
        <input v-model="customerName" placeholder="name" />
        <input v-model="email" placeholder="email" />
        <input v-model="passport" placeholder="passport" />
        <div class="actions">
          <button @click="submitBooking">submit</button>
          <button @click="showModal = false">cancel</button>
        </div>
      </div>
    </div>

    <div v-if="showSearchModal" class="modal">
      <div class="modal-content">
        <h2>order search</h2>
        <div class="search-box">
          <input v-model="searchQuery" placeholder="please put in order ID" />
          <button @click="handleSearch">SEARCH</button>
        </div>
        <div v-if="searchResult" class="result-area">
          <p><strong>status:</strong> comfirmed</p>
          <p><strong>hotel:</strong> {{ searchResult.hotel }}</p>
          <p><strong>customer name:</strong> {{ searchResult.customer }}</p>
          <p><strong>order ID:</strong> {{ searchResult.order_id }}</p>
          <p><strong>room count:</strong> {{ searchResult.quantity }}</p>
        </div>
        <button class="close-btn" @click="showSearchModal = false">close</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { ElMessage } from 'element-plus'
import 'element-plus/dist/index.css'

// 1. 统一 API 地址
const API_BASE_URL = 'http://travelstay-alb-1359388780.us-east-1.elb.amazonaws.com/api';

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
    console.error("can't find hotels:", error);
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
    return ElMessage({
  message: 'please put in email and passport',
  type: 'error',        // 红色错误样式 (还可以是 'success', 'warning', 'info')
  plain: true,          // 朴素样式，更轻量
  grouping: true,       // 如果连续触发，会自动合并，防止满屏都是弹窗
  duration: 4000        // 4秒后自动消失
})
    // alert("please put in email and passport");
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
      ElMessage({
  message: `order succeed！order ID：${response.data.order_id}`,
  type: 'success',        // 红色错误样式 (还可以是 'success', 'warning', 'info')
  plain: true,          // 朴素样式，更轻量
  grouping: true,       // 如果连续触发，会自动合并，防止满屏都是弹窗
  duration: 4000        // 4秒后自动消失
})
      // alert(`order succeed！order ID：${response.data.order_id}`);

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
          ElMessage({
  message: err.response?.data?.detail || "order failed",
  type: 'error',        // 红色错误样式 (还可以是 'success', 'warning', 'info')
  plain: true,          // 朴素样式，更轻量
  grouping: true,       // 如果连续触发，会自动合并，防止满屏都是弹窗
  duration: 4000        // 4秒后自动消失
})
    // alert(err.response?.data?.detail || "order failed");
  }
};

// 搜索功能逻辑（修复：已移出外部，大括号完全闭合）
const handleSearch = async () => {
  // 核心修改：使用 .trim() 替换 .strip
  if (!searchQuery.value || !searchQuery.value.trim()) {
    return ElMessage({
  message: "please put in search information",
  type: 'error',        // 红色错误样式 (还可以是 'success', 'warning', 'info')
  plain: true,          // 朴素样式，更轻量
  grouping: true,       // 如果连续触发，会自动合并，防止满屏都是弹窗
  duration: 4000        // 4秒后自动消失
})
    // alert("please put in search information");
  }

  try {
    const response = await axios.get(`${API_BASE_URL}/orders/search`, {
      params: { query: searchQuery.value.trim() }
    });

    if (response.data && response.data.length > 0) {
      searchResult.value = response.data[0];
    } else {
      ElMessage({
  message: "can't find any",
  type: 'error',        // 红色错误样式 (还可以是 'success', 'warning', 'info')
  plain: true,          // 朴素样式，更轻量
  grouping: true,       // 如果连续触发，会自动合并，防止满屏都是弹窗
  duration: 4000        // 4秒后自动消失
})
      // alert("can't find any");
      searchResult.value = null;
    }
  } catch (error) {
    ElMessage({
  message: "something went wrong",
  type: 'error',        // 红色错误样式 (还可以是 'success', 'warning', 'info')
  plain: true,          // 朴素样式，更轻量
  grouping: true,       // 如果连续触发，会自动合并，防止满屏都是弹窗
  duration: 4000        // 4秒后自动消失
})
    // alert("something wrong");
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