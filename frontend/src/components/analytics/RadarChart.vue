<template>
  <div ref="chartRef" class="w-full h-full min-h-[300px]"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  stats: {
    type: Object,
    default: null
  },
  indicators: {
    type: Array,
    default: () => [
      { name: '技术正确性', max: 100 },
      { name: '知识深度', max: 100 },
      { name: '逻辑严谨性', max: 100 },
      { name: '岗位匹配度', max: 100 },
      { name: '沟通表达', max: 100 }
    ]
  },
  dataValues: {
    type: Array,
    default: () => []
  },
  seriesName: {
    type: String,
    default: '能力评估雷达图'
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

  let finalData = props.dataValues
  if (!props.dataValues || props.dataValues.length === 0) {
    if (props.stats) {
      finalData = [
        props.stats.technical_depth || 0,
        props.stats.problem_solving || 0,
        props.stats.communication || 0,
        props.stats.business_scenario || 0,
        ((props.stats.technical_depth + props.stats.business_scenario + props.stats.problem_solving + props.stats.communication) / 4) || 0
      ]
    } else {
      finalData = [0, 0, 0, 0, 0]
    }
  }

  const option = {
    color: ['#0066CC'],
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderWidth: 1,
      borderColor: '#E5E7EB',
      shadowBlur: 10,
      shadowColor: 'rgba(0, 0, 0, 0.05)',
      textStyle: { color: '#374151' }
    },
    radar: {
      indicator: props.indicators,
      shape: 'polygon',
      splitNumber: 5,
      axisName: {
        color: '#4B5563',
        fontWeight: 'bold',
        fontSize: 12
      },
      splitArea: {
        areaStyle: {
          color: [
            'rgba(0, 102, 204, 0.02)',
            'rgba(0, 102, 204, 0.05)',
            'rgba(0, 102, 204, 0.08)',
            'rgba(0, 102, 204, 0.12)',
            'rgba(0, 102, 204, 0.18)'
          ]
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(0, 102, 204, 0.2)'
        }
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(0, 102, 204, 0.3)'
        }
      }
    },
    series: [
      {
        name: props.seriesName,
        type: 'radar',
        data: [
          {
            value: finalData,
            name: props.seriesName
          }
        ],
        symbolSize: 6,
        areaStyle: {
          color: 'rgba(0, 102, 204, 0.3)'
        },
        lineStyle: {
          width: 2,
          color: '#0066CC'
        },
        itemStyle: {
          color: '#0066CC',
          borderColor: '#fff',
          borderWidth: 2
        }
      }
    ]
  }
  
  chartInstance.setOption(option)
}

watch(() => [props.stats, props.dataValues], () => {
  updateChart()
}, { deep: true })

watch(() => props.indicators, () => {
  updateChart()
}, { deep: true })

const handleResize = () => {
  chartInstance?.resize()
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})
</script>