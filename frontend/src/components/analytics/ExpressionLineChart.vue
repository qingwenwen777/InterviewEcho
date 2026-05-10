<template>
  <div ref="chartRef" class="w-full h-full min-h-[220px]"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  }
})

const chartRef = ref(null)
let chartInstance = null

const initChart = () => {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

const updateChart = () => {
  if (!chartInstance) return

  const xData = props.data.map((item, index) => `第 ${index + 1} 题`)
  const yData = props.data.map(item => item.wpm)

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderWidth: 1,
      borderColor: '#E5E7EB',
      shadowBlur: 10,
      textStyle: { color: '#374151' },
      formatter: (params) => {
        const p = params[0]
        return `<div class="font-bold mb-1 text-gray-700">${p.name}</div>
                <div class="text-sm">语速: <span class="text-[#0066CC] font-black">${p.value}</span> wpm</div>`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '5%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: xData,
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisLabel: { color: '#6B7280', margin: 15 }
    },
    yAxis: {
      type: 'value',
      min: (value) => Math.max(0, Math.floor(value.min - 20)),
      max: (value) => Math.ceil(value.max + 20),
      splitLine: { lineStyle: { type: 'dashed', color: '#F3F4F6' } },
      axisLabel: { color: '#9CA3AF' }
    },
    series: [
      {
        name: '语速 WPM',
        type: 'line',
        data: yData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        itemStyle: {
          color: '#0066CC',
          borderColor: '#fff',
          borderWidth: 2
        },
        lineStyle: {
          width: 3,
          color: '#0066CC'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0, 102, 204, 0.3)' },
            { offset: 1, color: 'rgba(0, 102, 204, 0.0)' }
          ])
        },
        markArea: {
          itemStyle: {
            color: 'rgba(0, 102, 204, 0.06)'
          },
          label: {
            position: 'insideTopRight',
            color: '#0066CC',
            fontSize: 10,
            fontWeight: 'bold'
          },
          data: [
            [
              { name: '最优区间 (180-240)', yAxis: 180 },
              { yAxis: 240 }
            ]
          ]
        }
      }
    ]
  }

  chartInstance.setOption(option)
}

watch(() => props.data, () => {
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