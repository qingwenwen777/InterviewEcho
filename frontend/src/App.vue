<template>
  <div id="app">
    <!-- 如果当前路由设置为隐藏布局（如登录页、面试房间），则直接渲染纯净页面 -->
    <template v-if="$route.meta.hideLayout">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </template>
    
    <!-- 否则 -->
    <template v-else>
      <DefaultLayout />
    </template>
  </div>
</template>

<script setup>
import DefaultLayout from '@/layouts/DefaultLayout.vue'
</script>

<style>
/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>