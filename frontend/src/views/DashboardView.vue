<template>
  <div class="w-full pb-12" data-purpose="dashboard-main-content">

    <!-- 全屏 Loading 遮罩：启动面试时显示（包含 GitHub 抓取 + LLM 生成问题耗时） -->
    <div
      v-if="starting"
      class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/40 backdrop-blur-sm"
    >
      <div class="bg-white rounded-2xl shadow-2xl px-10 py-8 max-w-md text-center">
        <svg class="animate-spin mx-auto h-12 w-12 text-[#0066CC] mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
        </svg>
        <h3 class="text-lg font-bold text-gray-800 mb-2">{{ startingTitle }}</h3>
        <p class="text-sm text-gray-500 leading-relaxed">{{ startingHint }}</p>
      </div>
    </div>

    <!-- BEGIN: JobSelectionSection -->
    <section id="job-selection" class="py-6 px-4 max-w-7xl mx-auto" data-purpose="job-selection-grid">
      <div class="text-center mb-12">
        <h2 class="text-3xl font-bold text-slate-800 mb-4">选择您的目标职位</h2>
        <p class="text-slate-500">针对性模拟面试，覆盖核心技术栈，助您做好万全准备</p>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div 
          v-for="role in roles" 
          :key="role.id"
          @click="startInterview(role)"
          class="group relative bg-white p-8 rounded-2xl border border-slate-200 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl hover:border-[#0066CC] cursor-pointer" 
        >
          <div class="w-14 h-14 bg-blue-50 text-[#0066CC] rounded-xl flex items-center justify-center mb-6 group-hover:bg-[#0066CC] group-hover:text-white transition-colors duration-300">
            <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path>
            </svg>
          </div>
          <h3 class="text-xl font-bold text-slate-800 mb-3">{{ role.name }}</h3>
          <p class="text-slate-600 leading-relaxed mb-6 h-12 overflow-hidden text-sm">
            {{ role.desc }}
          </p>
          <div class="flex items-center text-sm font-semibold text-[#0066CC]">
            进入模拟 <svg class="h-4 w-4 ml-1 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M9 5l7 7-7 7" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path></svg>
          </div>
        </div>
      </div>
    </section>
    <!-- END: JobSelectionSection -->

    <!-- 面试参数设置弹窗 -->
    <InterviewSettingsDialog 
      ref="settingsDialogRef" 
      :role-name="selectedRole?.name" 
      :role-key="selectedRole?.key"
      @confirm="onSettingsConfirm"
    />

    <!-- W4.4.3 中断恢复弹窗 -->
    <ResumeDialog 
      ref="resumeDialogRef" 
      @resume="handleExecuteResume"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'
import InterviewSettingsDialog from '@/components/business/InterviewSettingsDialog.vue'
import ResumeDialog from '@/components/business/ResumeDialog.vue'

const router = useRouter()
const roles = ref([])
const settingsDialogRef = ref(null)
const resumeDialogRef = ref(null)
const selectedRole = ref(null)
const starting = ref(false)
const startingTitle = ref('正在准备面试')
const startingHint = ref('请稍候...')

onMounted(async () => {
  // 1. 获取岗位
  api.get('/interview/roles')
    .then(res => { roles.value = res.data })
    .catch(err => console.error('Failed to fetch roles:', err))

  // 2. 探测中断（【核心修复】将 Mock 拦截下放到组件内，确保不污染全局环境）
  api.get('/interview/incomplete')
    .then(res => {
      if (res.data?.has_incomplete) {
        resumeDialogRef.value.open(res.data.interview)
      }
    })
    .catch((err) => {
      // 拦截 404 (未实现) 或 网络错误，注入假数据
      if (err.response?.status === 404 || !err.response) {
        console.log('【Mock API】组件内拦截到 /incomplete 请求，注入模拟数据')
        resumeDialogRef.value.open({
          id: 999,
          role: 'Java后端开发工程师 (Mock)',
          start_time: new Date().toISOString()
        })
      }
    })
})

const handleExecuteResume = (interviewId) => {
  router.push({ name: 'InterviewRoom', params: { role: 'Resume' }, query: { interviewId } })
}

const startInterview = (role) => {
  selectedRole.value = role
  settingsDialogRef.value.open(role.key)
}

const onSettingsConfirm = async (settings) => {
  // 完美恢复：若包含 GitHub 项目，后端需要抓取 + LLM 生成问题，延时到 180s
  const hasRepos = (settings.repo_urls || []).length > 0
  const timeout = hasRepos ? 180000 : 30000

  // 显示 loading 遮罩，避免用户误以为"退回主页"
  starting.value = true
  if (hasRepos) {
    startingTitle.value = '正在分析您的 GitHub 项目'
    startingHint.value = 'AI 教练正在抓取项目代码并定制面试问题，大约 30-60 秒，请勿关闭页面...'
  } else {
    startingTitle.value = '正在准备面试房间'
    startingHint.value = '请稍候...'
  }

  try {
    const { data } = await api.post('/interview/start', {
      role: selectedRole.value.name,
      ...settings
    }, { timeout })
    router.push({
      name: 'InterviewRoom',
      params: { role: selectedRole.value.name },
      query: { interviewId: data.id }
    })
  } catch (err) {
    console.error('Failed to start interview:', err)
    alert('面试启动失败：' + (err.response?.data?.detail || err.message))
  } finally {
    starting.value = false
  }
}
</script>

<style scoped>
svg { display: block; }
</style>