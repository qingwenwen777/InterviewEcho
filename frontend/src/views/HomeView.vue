<template>
  <div class="w-full pb-12" data-purpose="home-page-main-content">
    
    <!-- BEGIN: HeroSection -->
    <section class="relative py-16 px-4 overflow-hidden bg-transparent rounded-2xl mb-8" data-purpose="hero-section">
      <!-- 极简网格背景 -->
      <div class="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full opacity-5 pointer-events-none">
        <svg class="w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 100">
          <defs>
            <pattern height="10" id="grid" patternUnits="userSpaceOnUse" width="10">
              <path d="M 10 0 L 0 0 0 10" fill="none" stroke="currentColor" stroke-width="0.5"></path>
            </pattern>
          </defs>
          <rect fill="url(#grid)" height="100" width="100"></rect>
        </svg>
      </div>
      <div class="max-w-5xl mx-auto text-center relative z-10 pt-10">
        <h1 class="text-5xl md:text-6xl font-extrabold text-slate-900 tracking-tight mb-6">
          AI赋能，真实模拟，<span class="text-[#0066CC]">拿下面试</span>
        </h1>
        <p class="text-xl text-slate-600 mb-10 max-w-2xl mx-auto leading-relaxed">
          InterviewEcho为您提供最真实的AI模拟面试体验，精准分析您的每一项能力，助您斩获心仪Offer。
        </p>
        <div class="flex justify-center gap-4">
          <button 
            @click="startNow"
            class="px-8 py-4 bg-[#0066CC] hover:bg-[#0052a3] text-white font-semibold rounded-lg shadow-lg shadow-blue-200 transition-all duration-300 transform hover:-translate-y-1 active:scale-95"
          >
            立即开始面试
          </button>
        </div>
        
        <!-- Trust Badges -->
        <div class="mt-20 flex flex-wrap justify-center gap-10 text-slate-400 grayscale opacity-70">
          <div class="flex items-center gap-2">
            <span class="text-sm font-bold tracking-widest uppercase">Real-time Feedback</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-sm font-bold tracking-widest uppercase">Expert Evaluation</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-sm font-bold tracking-widest uppercase">Career Growth</span>
          </div>
        </div>
      </div>
    </section>
    <!-- END: HeroSection -->

  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const startNow = () => {
  router.push('/dashboard')
}
</script>

<style scoped>
svg { display: block; }
</style>