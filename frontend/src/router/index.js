import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

import HomeView from '@/views/HomeView.vue'
import LoginView from '@/views/LoginView.vue'
import DashboardView from '@/views/DashboardView.vue'
import InterviewRoomView from '@/views/InterviewRoomView.vue'
import ReportView from '@/views/ReportView.vue'
import ProfileView from '@/views/ProfileView.vue'

const routes = [
  { 
    path: '/', 
    name: 'Home', 
    component: HomeView 
  },
  { 
    path: '/login', 
    name: 'Login', 
    component: LoginView, 
    meta: { hideLayout: true } 
  },
  { 
    path: '/dashboard', 
    name: 'Dashboard', 
    component: DashboardView, 
    meta: { requiresAuth: true } 
  },
  { 
    path: '/profile', 
    name: 'Profile', 
    component: ProfileView, 
    meta: { requiresAuth: true } 
  },
  { 
    path: '/interview/:role', 
    name: 'InterviewRoom', 
    component: InterviewRoomView, 
    meta: { requiresAuth: true, hideLayout: true } 
  },
  { 
    path: '/report/:id', 
    name: 'Report', 
    component: ReportView, 
    meta: { requiresAuth: true } 
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})

export default router