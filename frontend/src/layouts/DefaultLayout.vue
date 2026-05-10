<template>
  <div class="bg-[#F3F4F6] min-h-screen flex flex-col font-sans">
    <!-- BEGIN: MainHeader -->
    <header class="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          
          <!-- Left: Logo and Brand Name -->
          <div class="flex items-center flex-shrink-0 cursor-pointer" @click="$router.push('/')">
            <div class="w-8 h-8 bg-[#0066CC] rounded-md flex items-center justify-center mr-3">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path>
              </svg>
            </div>
            <span class="text-xl font-bold text-gray-900 tracking-tight">InterviewEcho</span>
          </div>

          <!-- Center: Primary Navigation -->
          <nav class="hidden md:flex space-x-8">
            <router-link 
              to="/" 
              class="nav-link px-1 pt-1 text-sm font-medium transition-colors"
              :class="[$route.name === 'Home' ? 'text-[#0066CC] border-b-2 border-[#0066CC] font-semibold' : 'text-gray-500 hover:text-[#0066CC]']"
            >
              首页
            </router-link>
            <router-link 
              to="/dashboard" 
              class="nav-link px-1 pt-1 text-sm font-medium transition-colors"
              :class="[$route.name === 'Dashboard' ? 'text-[#0066CC] border-b-2 border-[#0066CC] font-semibold' : 'text-gray-500 hover:text-[#0066CC]']"
            >
              模拟面试大厅
            </router-link>
            <a 
              href="javascript:void(0)" 
              @click="handleComingSoon"
              class="nav-link px-1 pt-1 text-sm font-medium text-gray-500 hover:text-[#0066CC] transition-colors"
            >
              题库练习
            </a>
            <router-link 
              to="/profile" 
              class="nav-link px-1 pt-1 text-sm font-medium transition-colors"
              :class="[$route.name === 'Profile' ? 'text-[#0066CC] border-b-2 border-[#0066CC] font-semibold' : 'text-gray-500 hover:text-[#0066CC]']"
            >
              面试历史与分析
            </router-link>
          </nav>

          <!-- Right: Notifications and User Profile -->
          <div class="flex items-center space-x-4">
            <!-- Notification Bell -->
            <button aria-label="Notifications" class="p-2 rounded-full text-gray-400 hover:text-[#0066CC] focus:outline-none transition-colors">
              <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path>
              </svg>
            </button>
            
            <!-- Element Plus User Avatar Dropdown -->
            <el-dropdown trigger="click">
              <div class="flex items-center cursor-pointer outline-none">
                <img alt="User Profile" class="h-8 w-8 rounded-full border border-gray-200" src="https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png" />
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item>个人中心</el-dropdown-item>
                  <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>

        </div>
      </div>
    </header>
    <!-- END: MainHeader -->

    <!-- BEGIN: MainContent -->
    <main class="flex-grow flex items-start justify-center p-6 sm:p-10 lg:p-12">
      <div class="w-full max-w-7xl mx-auto">
        <!-- 路由出口，渲染具体的页面内容 -->
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
    <!-- END: MainContent -->

    <!-- BEGIN: Footer -->
    <footer class="bg-white border-t border-gray-200 py-6 mt-auto">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center text-sm text-gray-500">
        <div class="mb-4 md:mb-0">
          © 2026 InterviewEcho. 面向计算机相关学生的AI模拟面试平台.
        </div>
        <div class="flex space-x-6">
          <a class="hover:text-[#0066CC] transition-colors cursor-pointer">隐私政策</a>
          <a class="hover:text-[#0066CC] transition-colors cursor-pointer">服务条款</a>
          <a class="hover:text-[#0066CC] transition-colors cursor-pointer">帮助中心</a>
        </div>
      </div>
    </footer>
    <!-- END: Footer -->
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()
const router = useRouter()

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

// 给后端同学的注释：这里是“题库练习”的占位点击事件，后续若要开发，将 a 标签改为 router-link 即可
const handleComingSoon = () => {
  ElMessage.info('题库练习功能开发中，敬请期待！')
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.font-sans {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

.nav-link {
  transition: all 0.2s ease-in-out;
  color: #6b7280;
}
.nav-link:hover {
  color: #0066CC;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>