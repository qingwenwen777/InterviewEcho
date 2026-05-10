<template>
  <div ref="chartRef" class="w-full h-full min-h-[300px]"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  history: {
    type: Array,
    default: () => []
  },
  filterRole: {
    type: String,
    default: 'All'
  },
  filterDifficulty: {
    type: String,
    default: 'All'
  }
})

const chartRef = ref(null)
let chartInstance = null

const NESTED_COLORS = {
  'Java后端开发工程师': { '简单': '#93C5FD', '中等': '#3B82F6', '困难': '#1D4ED8' },
  'Web前端开发工程师': { '简单': '#94A3B8', '中等': '#475569', '困难': '#1E293B' },
  'Python算法工程师': { '简单': '#A5B4FC', '中等': '#6366F1', '困难': '#312E81' }
}

const DEFAULT_COLOR = '#0066CC'

const initChart = () => {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

const updateChart = () => {
  if (!chartInstance) return

  const sortedHistory = [...props.history].sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
  
  const uniqueDates = Array.from(new Set(sortedHistory.map(item => {
    const d = new Date(item.created_at)
    return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  })))

  let series = []
  
  // 多维筛选组装逻辑
  if (props.filterRole === 'All' && props.filterDifficulty === 'All') {
    const roles = ['Java后端开发工程师', 'Web前端开发工程师', 'Python算法工程师']
    const difficulties = ['简单', '中等', '困难']
    
    roles.forEach(role => {
      difficulties.forEach(diff => {
        const roleDiffData = sortedHistory.filter(item => item.role === role && item.difficulty === diff)
        if (roleDiffData.length > 0) {
          series.push({
            name: `${role}-${diff}`,
            type: 'line',
            data: uniqueDates.map(dateStr => {
              const matching = roleDiffData.find(item => {
                const d = new Date(item.created_at)
                return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}` === dateStr
              })
              return matching ? { value: matching.total_score, difficulty: matching.difficulty } : null
            }),
            smooth: true,
            connectNulls: true,
            itemStyle: { color: NESTED_COLORS[role]?.[diff] || DEFAULT_COLOR }
          })
        }
      })
    })
  } else if (props.filterRole !== 'All' && props.filterDifficulty === 'All') {
    const difficulties = ['简单', '中等', '困难']
    const roleData = sortedHistory.filter(item => item.role === props.filterRole)
    series = difficulties.map(diff => ({
      name: diff,
      type: 'line',
      data: uniqueDates.map(dateStr => {
        const matching = roleData.find(item => {
          const d = new Date(item.created_at)
          return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}` === dateStr && item.difficulty === diff
        })
        return matching ? { value: matching.total_score, difficulty: matching.difficulty } : null
      }),
      smooth: true,
      connectNulls: true,
      itemStyle: { color: NESTED_COLORS[props.filterRole]?.[diff] || DEFAULT_COLOR }
    }))
  } else if (props.filterDifficulty !== 'All' && props.filterRole === 'All') {
    const roles = ['Java后端开发工程师', 'Web前端开发工程师', 'Python算法工程师']
    const diffData = sortedHistory.filter(item => item.difficulty === props.filterDifficulty)
    series = roles.map(role => ({
      name: role,
      type: 'line',
      data: uniqueDates.map(dateStr => {
        const matching = diffData.find(item => {
          const d = new Date(item.created_at)
          return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}` === dateStr && item.role === role
        })
        return matching ? { value: matching.total_score, difficulty: matching.difficulty } : null
      }),
      smooth: true,
      connectNulls: true,
      itemStyle: { color: NESTED_COLORS[role]?.[props.filterDifficulty] || DEFAULT_COLOR }
    }))
  } else {
    const filteredData = sortedHistory.filter(item => item.role === props.filterRole && item.difficulty === props.filterDifficulty)
    const baseColor = DEFAULT_COLOR
    series = [{
      name: `${props.filterRole} (${props.filterDifficulty})`,
      type: 'line',
      data: uniqueDates.map(dateStr => {
        const matching = filteredData.find(item => {
          const d = new Date(item.created_at)
          return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}` === dateStr
        })
        return matching ? { value: matching.total_score, difficulty: matching.difficulty } : null
      }),
      smooth: true,
      connectNulls: true,
      itemStyle: { 
        color: baseColor,
        borderColor: '#fff',
        borderWidth: 2
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(0, 102, 204, 0.2)' },
          { offset: 1, color: 'rgba(0, 102, 204, 0)' }
        ])
      }
    }]
  }

  const option = {
    legend: {
      show: true,
      top: 0,
      icon: 'circle',
      textStyle: { color: '#6B7280', fontSize: 12 }
    },
    tooltip: {
      trigger: 'axis'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: uniqueDates,
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisTick: { show: false },
      axisLabel: { color: '#6B7280' }
    },
    yAxis: {
      type: 'value',
      min: 60,
      max: 100,
      splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } },
      axisLine: { show: false },
      axisLabel: { color: '#6B7280' }
    },
    series: series.map(s => ({
      ...s,
      symbolSize: 8,
      lineStyle: { width: 3 }
    }))
  }

  chartInstance.setOption(option, true)
}

watch(() => [props.history, props.filterRole, props.filterDifficulty], () => {
  updateChart()
}, { deep: true })

onMounted(() => {
  initChart()
  window.addEventListener('resize', () => chartInstance?.resize())
})

onUnmounted(() => {
  chartInstance?.dispose()
})
</script>