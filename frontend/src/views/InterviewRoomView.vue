<template>
  <!-- 使用原版的深色沉浸式 Layout 作为外层容器，并通过 @end-interview 触发后端的真正结束逻辑 -->
  <InterviewLayout :role="role" @end-interview="endInterview">
    
    <!-- 内部容器：根据 isDarkMode 动态切换全局背景 -->
    <div class="flex flex-col h-full w-full overflow-hidden transition-colors duration-500" :class="isDarkMode ? 'bg-[#121212]' : 'bg-[#F3F4F6]'">
      
      <!-- Chat Area -->
      <div class="flex-grow p-6 md:p-10 overflow-y-auto space-y-6 relative transition-colors duration-500" :class="isDarkMode ? 'bg-[#121212]' : 'bg-[#F3F4F6]'" ref="chatArea">
        
        <!-- 主题切换悬浮按钮 -->
        <div class="absolute top-4 right-4 z-10">
          <button 
            @click="isDarkMode = !isDarkMode"
            :class="isDarkMode ? 'bg-[#1E1E1E] text-gray-400 border-[#333333] hover:text-white' : 'bg-white text-gray-500 border-gray-200 hover:text-[#0066CC]'"
            class="px-3 py-1.5 rounded-full text-xs font-bold border shadow-sm transition-all flex items-center gap-1.5"
          >
            <el-icon><Sunny v-if="isDarkMode" /><Moon v-else /></el-icon>
            {{ isDarkMode ? '浅色模式' : '深色沉浸' }}
          </button>
        </div>
        
        <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full text-gray-500">
          <el-icon class="is-loading text-4xl mb-4 text-[#0066CC]"><component :is="Loading" /></el-icon>
          <p class="text-sm font-medium tracking-wide">正在为您协调面试官，请稍候...</p>
        </div>

        <!-- 使用 ChatBubble 并传递主题状态 -->
        <div v-for="(msg, index) in messages" :key="index" class="w-full flex">
          <ChatBubble 
            :role="msg.sender === 'user' ? 'candidate' : 'interviewer'" 
            :content="msg.content" 
            :theme="isDarkMode ? 'dark' : 'light'"
          />
        </div>

        <!-- Thinking Indicator -->
        <div v-if="sending" class="w-full flex">
           <ChatBubble role="interviewer" status="typing" content="" :theme="isDarkMode ? 'dark' : 'light'" />
        </div>
      </div>

      <!-- Input Area -->
      <div class="p-4 md:px-10 border-t transition-colors duration-500" :class="isDarkMode ? 'bg-[#1E1E1E] border-[#333333]' : 'bg-white border-gray-200'">
        
        <div v-if="isRecording" class="flex items-center gap-2 mb-2 px-2 py-1 text-red-400 rounded animate-pulse">
          <div class="w-2 h-2 bg-red-500 rounded-full"></div>
          <span class="text-xs font-bold uppercase tracking-wider">正在录音中...</span>
        </div>
        <div v-if="isTranscribing" class="flex items-center gap-2 mb-2 px-2 py-1 text-[#0066CC] rounded animate-pulse">
          <el-icon class="is-loading"><component :is="Loading" /></el-icon>
          <span class="text-xs font-bold uppercase tracking-wider">AI 正在精准转录您的语音...</span>
        </div>
        
        <textarea
          v-model="inputMsg"
          rows="3"
          placeholder="请输入您的回答，或点击麦克风开始语音输入..."
          :class="isDarkMode ? 'bg-[#2A2A2A] text-gray-200 border-[#444444] focus:border-[#0066CC]' : 'bg-gray-50 text-gray-800 border-gray-200 focus:border-[#0066CC]'"
          class="w-full rounded-lg p-4 text-sm focus:outline-none resize-none transition-colors duration-300 shadow-inner"
          @keydown.enter.prevent="sendMessage"
          :disabled="sending || ending"
        ></textarea>
        
        <div class="flex justify-between items-center mt-3">
          <button 
            @click="toggleRecording"
            :disabled="sending || ending"
            :class="[
              'w-11 h-11 rounded-full flex items-center justify-center transition-all',
              isRecording 
                ? 'bg-red-500/20 text-red-500 border border-red-500/50 animate-pulse shadow-lg shadow-red-500/20' 
                : (isDarkMode ? 'bg-[#2A2A2A] text-gray-400 hover:text-white border border-[#444444]' : 'bg-gray-100 text-gray-500 hover:text-[#0066CC] border border-gray-200')
            ]"
          >
            <el-icon class="text-xl"><Microphone /></el-icon>
          </button>
          
          <button 
            @click="sendMessage" 
            :disabled="(!(inputMsg || '').trim() && !isRecording) || isTranscribing || ending"
            :class="[
              'px-8 py-2.5 rounded-lg text-sm font-bold transition-all shadow-md active:scale-95',
              (!(inputMsg || '').trim() && !isRecording) || isTranscribing || ending || sending
                ? (isDarkMode ? 'bg-[#2A2A2A] text-gray-600 cursor-not-allowed shadow-none' : 'bg-gray-100 text-gray-400 cursor-not-allowed shadow-none')
                : 'bg-[#0066CC] hover:bg-blue-700 text-white'
            ]"
          >
            {{ sending ? '发送中...' : '发送 (Enter)' }}
          </button>
        </div>

      </div>
    </div>
  </InterviewLayout>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading, Microphone, Sunny, Moon } from '@element-plus/icons-vue'
import api from '@/api'
import ChatBubble from '@/components/business/ChatBubble.vue'
import InterviewLayout from '@/layouts/InterviewLayout.vue'

// 核心主题状态：默认为深色暗黑风
const isDarkMode = ref(true)

const route = useRoute()
const router = useRouter()
const role = ref(route.params.role)

const interviewId = ref(null)
const messages = ref([])
const inputMsg = ref('')
const chatArea = ref(null)

const sending = ref(false)
const ending = ref(false)
const isRecording = ref(false)
const isTranscribing = ref(false)
let mediaRecorder = null
let audioChunks = []

const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder = new MediaRecorder(stream)
    audioChunks = []

    mediaRecorder.ondataavailable = (event) => {
      audioChunks.push(event.data)
    }

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })
      await uploadVoice(audioBlob)
      stream.getTracks().forEach(track => track.stop())
    }

    mediaRecorder.start()
    isRecording.value = true
    ElMessage.info('正在录音，请说话...')
  } catch (err) {
    console.error('Failed to start recording:', err)
    ElMessage.error('无法访问麦克风，请检查权限设置')
  }
}

const stopRecording = () => {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop()
    isRecording.value = false
  }
}

const uploadVoice = async (blob) => {
  isTranscribing.value = true
  sending.value = true
  
  const formData = new FormData()
  formData.append('file', blob, 'voice.webm')

  try {
    const { data } = await api.post(`/interview/${interviewId.value}/voice`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 180000 
    })
    
    messages.value.push({ sender: 'user', content: data.transcription })
    messages.value.push({ sender: 'ai', content: data.ai_message.content })
    
    if (data.ai_message.is_final) {
      ElMessage.warning('面试已达到建议轮数，正在为您生成评估报告...')
      setTimeout(() => { endInterview() }, 2500)
    }
  } catch (err) {
    console.error('Voice upload failed:', err)
    ElMessage.error(`语音转录或回复失败: ${err.response?.data?.detail || err.message}`)
  } finally {
    isTranscribing.value = false
    sending.value = false
    scrollToBottom()
  }
}

const toggleRecording = async () => {
  if (isRecording.value) {
    stopRecording()
  } else {
    await startRecording()
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatArea.value) {
      chatArea.value.scrollTop = chatArea.value.scrollHeight
    }
  })
}

onMounted(async () => {
  const idFromQuery = route.query.interviewId
  if (idFromQuery) {
    interviewId.value = parseInt(idFromQuery)
    try {
      const { data } = await api.get(`/interview/${interviewId.value}/messages`)
      messages.value = data
      scrollToBottom()
    } catch (err) {
      console.error('Fetch messages error:', err)
      messages.value.push({ sender: 'ai', content: `你好，我是你的${role.value}面试官。准备好了吗？我们将针对性地展开面试。` })
    }
    return
  }

  try {
    const { data } = await api.post('/interview/start', { role: role.value })
    interviewId.value = data.id
    messages.value.push({ sender: 'ai', content: `你好，我是你的${role.value}面试官。我们马上开始面试，请先做个简单的自我介绍。` })
  } catch (err) {
    console.error('Start interview error:', err)
    ElMessage.error(`无法启动面试室: ${err.response?.data?.detail || err.message}`)
    router.push('/dashboard')
  }
})

const sendMessage = async () => {
  // 停止录音后，mediaRecorder.onstop会自动接管后续的上传和发送流程
  if (isRecording.value) {
    stopRecording()
    return
  }

  if (!(inputMsg.value || '').trim() || sending.value) return
  
  const content = inputMsg.value
  messages.value.push({ sender: 'user', content })
  inputMsg.value = ''
  sending.value = true
  scrollToBottom()

  try {
    const { data } = await api.post(`/interview/${interviewId.value}/message`, { content })
    messages.value.push({ sender: 'ai', content: data.content })
    
    if (data.is_final) {
      ElMessage.warning('面试已达到建议轮数，正在为您生成评估报告...')
      setTimeout(() => { endInterview() }, 2500)
    }
  } catch (err) {
    console.error('Send message error:', err)
    ElMessage.error(`消息发送失败: ${err.response?.data?.detail || err.message}`)
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

// 接收来自InterviewLayout组件的结束事件
const endInterview = async () => {
  ending.value = true
  ElMessage.info('正在为整场面试进行深度评估，这可能需要几十秒，请勿关闭页面...')
  try {
    // LLM 评估通常 15-60s，单独覆盖全局 10s 超时，避免误报失败
    const { data } = await api.post(`/interview/${interviewId.value}/end`, null, { timeout: 180000 })
    ElMessage.success('面试结束，报告已生成！')
    
    router.push({
      name: 'Report',
      params: { id: interviewId.value },
      state: { evaluation: data.evaluation }
    })
  } catch (err) {
    console.error('End interview error:', err)
    ElMessage.error(`生成评估报告失败: ${err.response?.data?.detail || err.message}`)
    ending.value = false
  }
}
</script>