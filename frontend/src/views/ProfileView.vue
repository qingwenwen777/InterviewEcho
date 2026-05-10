<template>
  <div class="max-w-7xl mx-auto px-4 py-8 space-y-6">
    <div class="mb-4">
      <h2 class="text-2xl font-bold text-slate-800">个人能力分析大盘</h2>
    </div>

    <!-- StatsGrid -->
    <section class="grid grid-cols-1 md:grid-cols-3 gap-6" data-purpose="top-stats-row">
      <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex items-center justify-between" data-purpose="stat-card">
        <div>
          <p class="text-sm font-medium text-slate-500 uppercase tracking-wider">总面试次数</p>
          <h3 class="text-3xl font-bold text-slate-900 mt-1">{{ history.length }}</h3>
        </div>
        <div class="p-3 bg-blue-50 rounded-lg">
          <svg class="h-8 w-8 text-[#0066CC]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
        </div>
      </div>
      <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex items-center justify-between" data-purpose="stat-card">
        <div>
          <p class="text-sm font-medium text-slate-500 uppercase tracking-wider">平均综合得分</p>
          <h3 class="text-3xl font-bold text-slate-900 mt-1">{{ averageScore }}</h3>
        </div>
        <div class="p-3 bg-blue-50 rounded-lg">
          <svg class="h-8 w-8 text-[#0066CC]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
        </div>
      </div>
      <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex items-center justify-between" data-purpose="stat-card">
        <div>
          <p class="text-sm font-medium text-slate-500 uppercase tracking-wider">当前优胜岗位</p>
          <h3 class="text-lg font-bold text-slate-900 mt-1">{{ topRole }}</h3>
        </div>
        <div class="p-3 bg-blue-50 rounded-lg">
          <svg class="h-8 w-8 text-[#0066CC]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path></svg>
        </div>
      </div>
    </section>

    <!-- ChartSection -->
    <section class="bg-white p-6 rounded-xl shadow-sm border border-slate-100" data-purpose="middle-chart-section">
      <div class="flex items-center justify-between mb-6 border-b border-slate-100 pb-4">
        <h2 class="text-lg font-bold text-slate-800 flex items-center">
          <span class="w-1.5 h-5 bg-[#0066CC] rounded-full mr-2"></span>
          近期能力成长曲线
        </h2>
        <div class="flex gap-3">
          <select v-model="filterRole" class="border border-slate-200 text-sm rounded-md px-3 py-1.5 text-slate-600 focus:outline-none focus:border-[#0066CC]">
            <option value="All">全部岗位</option>
            <option v-for="role in availableRoles" :key="role" :value="role">{{ role }}</option>
          </select>
          <select v-model="filterDifficulty" class="border border-slate-200 text-sm rounded-md px-3 py-1.5 text-slate-600 focus:outline-none focus:border-[#0066CC]">
            <option value="All">全部难度</option>
            <option value="简单">简单</option>
            <option value="中等">中等</option>
            <option value="困难">困难</option>
          </select>
        </div>
      </div>

      <div v-if="history.length === 0" class="h-64 flex items-center justify-center bg-slate-50 rounded-lg border border-dashed border-slate-200">
        <p class="text-slate-400 font-medium">暂无数据，请先完成一次模拟面试</p>
      </div>
      <div v-else class="h-80 w-full rounded-lg bg-white" data-purpose="chart-container">
        <LineChart :history="history" :filter-role="filterRole" :filter-difficulty="filterDifficulty" />
      </div>
    </section>

    <!-- History Table -->
    <section class="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden" data-purpose="bottom-history-section" id="interview-history-table">
      <div class="px-6 py-4 border-b border-slate-100">
        <h2 class="text-lg font-bold text-slate-800">面试历史记录</h2>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-slate-50">
              <th class="px-6 py-3 text-xs font-semibold text-slate-500 uppercase">日期</th>
              <th class="px-6 py-3 text-xs font-semibold text-slate-500 uppercase">目标岗位</th>
              <th class="px-6 py-3 text-xs font-semibold text-slate-500 uppercase">难度</th>
              <th class="px-6 py-3 text-xs font-semibold text-slate-500 uppercase">最终得分</th>
              <th class="px-6 py-3 text-xs font-semibold text-slate-500 uppercase text-right">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="item in filteredHistory" :key="item.id" class="hover:bg-slate-50 transition-colors">
              <td class="px-6 py-4 text-sm text-slate-600">{{ formatDateTime(item.created_at) }}</td>
              <td class="px-6 py-4 text-sm font-medium text-slate-900">{{ item.role }}</td>
              <td class="px-6 py-4">
                <span :class="['px-2.5 py-0.5 rounded-full text-xs font-medium border', getDifficultyClass(item.difficulty)]">
                  {{ item.difficulty }}
                </span>
              </td>
              <td class="px-6 py-4 text-sm font-bold text-slate-900">{{ item.total_score.toFixed(1) }}</td>
              <td class="px-6 py-4 text-right">
                <button 
                  @click="router.push({ name: 'Report', params: { id: item.id } })"
                  class="text-[#0066CC] text-sm font-semibold hover:underline decoration-2 underline-offset-4 cursor-pointer"
                >
                  查看评估报告
                </button>
              </td>
            </tr>
            <tr v-if="filteredHistory.length === 0">
              <td colspan="5" class="px-6 py-10 text-center text-slate-400">暂无符合条件的历史记录哦～</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'
import LineChart from '@/components/analytics/LineChart.vue'

const router = useRouter()
const history = ref([])
const filterRole = ref('All')
const filterDifficulty = ref('All')

onMounted(async () => {
  try {
    const { data } = await api.get('/interview/history')
    history.value = data
  } catch (err) {
    console.error('Failed to fetch history:', err)
  }
})

const availableRoles = computed(() => {
  const rs = new Set(history.value.map(h => h.role))
  return Array.from(rs)
})

const filteredHistory = computed(() => {
  return history.value.filter(h => {
    const roleMatch = filterRole.value === 'All' || h.role === filterRole.value
    const diffMatch = filterDifficulty.value === 'All' || h.difficulty === filterDifficulty.value
    return roleMatch && diffMatch
  })
})

const averageScore = computed(() => {
  if (history.value.length === 0) return 0
  const sum = history.value.reduce((acc, curr) => acc + curr.total_score, 0)
  return (sum / history.value.length).toFixed(1)
})

const topRole = computed(() => {
  if (history.value.length === 0) return '暂无'
  return history.value[0].role
})

const getDifficultyClass = (diff) => {
  if (diff === '简单') return 'bg-green-50 text-green-700 border-green-100'
  if (diff === '中等') return 'bg-amber-50 text-amber-700 border-amber-100'
  if (diff === '困难') return 'bg-red-50 text-red-700 border-red-100'
  return 'bg-slate-50 text-slate-700 border-slate-200'
}

const formatDateTime = (dateStr) => {
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
svg { display: block; }
</style>