<template>
  <div :class="['flex w-full space-y-1', isInterviewer ? 'flex-col items-start' : 'flex-col items-end']">
    <!-- 角色名称 -->
    <div :class="['text-[10px] font-bold uppercase tracking-widest', nameColorClass]">
      {{ isInterviewer ? '面试官' : '候选人 (你)' }}
    </div>

    <!-- 气泡内容区 -->
    <div v-if="status === 'typing'" :class="[bubbleClasses, 'italic']">
      <span class="animate-pulse">{{ isInterviewer ? '正在分析并生成反馈...' : '正在输入或语音收音中...' }}</span>
    </div>
    <div v-else :class="bubbleClasses">
      {{ content }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // 角色类型：'interviewer' (面试官) | 'candidate' (候选人)
  role: {
    type: String,
    required: true
  },
  // 聊天文本内容
  content: {
    type: String,
    default: ''
  },
  // 状态：'done' (已完成) | 'typing' (正在输入/录音中)
  status: {
    type: String,
    default: 'done'
  },
  // 当前主题：'dark' | 'light'
  theme: {
    type: String,
    default: 'dark'
  }
})

// 判断当前是否是面试官发出的消息
const isInterviewer = computed(() => props.role === 'interviewer')

const nameColorClass = computed(() => {
  if (props.theme === 'dark') {
    return isInterviewer.value ? 'text-[#0066CC]' : 'text-gray-500'
  } else {
    return isInterviewer.value ? 'text-[#0066CC]' : 'text-gray-400'
  }
})

// 动态计算气泡的 Tailwind 样式类
const bubbleClasses = computed(() => {
  const baseClasses = 'text-sm leading-relaxed p-4 inline-block border max-w-[85%] break-words shadow-sm'
  
  if (props.theme === 'dark') {
    if (isInterviewer.value) {
      // 深色模式 - 面试官 (深灰)
      return `${baseClasses} text-gray-300 bg-[#1E1E1E] rounded-2xl rounded-tl-sm border-[#333333]`
    } else {
      // 深色模式 - 候选人 (幽灵蓝)
      return `${baseClasses} text-gray-300 bg-[#0066CC]/20 rounded-2xl rounded-tr-sm border-[#0066CC]/30`
    }
  } else {
    if (isInterviewer.value) {
      // 浅色模式 - 面试官 (白底)
      return `${baseClasses} text-gray-800 bg-white rounded-2xl rounded-tl-sm border-gray-200`
    } else {
      // 浅色模式 - 候选人 (品牌蓝)
      return `${baseClasses} text-white bg-[#0066CC] rounded-2xl rounded-tr-sm border-[#0052a3]`
    }
  }
})
</script>

<style scoped>
</style>