<template>
  <!-- 外层容器：占满屏幕、深色背景、隐藏系统默认滚动条 -->
  <div class="bg-[#121212] text-gray-300 h-screen w-screen overflow-hidden font-sans flex flex-col">
    
    <!-- BEGIN: TopBar -->
    <header class="h-10 border-b border-[#333333] bg-[#121212] flex items-center justify-between px-4 z-50 shrink-0 shadow-sm">
      
      <!-- Left Section: Job Position Tag -->
      <div class="flex items-center space-x-3">
        <div class="flex items-center space-x-2">
          <!-- 呼吸灯动效，暗示面试正在进行中 -->
          <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
          <span class="text-xs font-medium tracking-wide uppercase text-gray-400">{{ role || 'AI模拟面试中' }}</span>
        </div>
      </div>
      
      <!-- Center Section: Timer -->
      <div class="flex items-center justify-center">
        <span class="text-sm font-mono font-bold text-white tracking-widest bg-gray-800 px-3 py-0.5 rounded border border-[#333333]">
          {{ formattedTime }}
        </span>
      </div>
      
      <!-- Right Section: Actions -->
      <div class="flex items-center">
        <button 
          @click="$emit('end-interview')"
          class="bg-red-600 hover:bg-red-700 text-white text-xs font-bold px-4 py-1 rounded transition-colors duration-200 uppercase tracking-tight shadow-md"
        >
          结束面试
        </button>
      </div>

    </header>
    <!-- END: TopBar -->

    <!-- BEGIN: MainContent -->
    <main class="flex-1 w-full overflow-hidden flex">
      <!-- 渲染具体的面试房间内容 -->
      <slot />
    </main>
    <!-- END: MainContent -->
    
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  role: {
    type: String,
    default: ''
  }
})
const emit = defineEmits(['end-interview'])

// --- 倒计时核心逻辑 ---
const timeLeft = ref(45 * 60) // 45分钟转换为秒
let timer = null

const formattedTime = computed(() => {
  const m = Math.floor(timeLeft.value / 60).toString().padStart(2, '0')
  const s = (timeLeft.value % 60).toString().padStart(2, '0')
  return `${m}:${s}`
})

onMounted(() => {
  timer = setInterval(() => {
    if (timeLeft.value > 0) {
      timeLeft.value--
    } else {
      // 时间归零时，自动触发交卷
      clearInterval(timer)
      emit('end-interview')
    }
  }, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.font-sans {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

:deep(::-webkit-scrollbar) {
  width: 6px;
  height: 6px;
}
:deep(::-webkit-scrollbar-track) {
  background: #121212;
}
:deep(::-webkit-scrollbar-thumb) {
  background: #333333;
  border-radius: 3px;
}
:deep(::-webkit-scrollbar-thumb:hover) {
  background: #444444;
}
</style>