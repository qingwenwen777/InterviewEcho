<template>
  <el-dialog
    v-model="visible"
    :title="`开始 ${roleName} 面试`"
    width="550px"
    class="custom-clean-dialog"
    :show-close="false"
    destroy-on-close
  >
    <div class="space-y-8 py-2">
      <!-- Difficulty Selection -->
      <div>
        <label class="block text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">选择面试难度</label>
        <div class="grid grid-cols-3 gap-4">
          <button
            v-for="d in ['简单', '中等', '困难']"
            :key="d"
            @click="difficulty = d"
            :class="[
              'py-3 rounded-lg font-bold transition-colors border',
              difficulty === d
                ? 'bg-[#E6F0FA] border-[#0066CC] text-[#0066CC]'
                : 'bg-white border-gray-200 text-gray-600 hover:border-[#0066CC]'
            ]"
          >
            {{ d }}
          </button>
        </div>
      </div>

      <!-- Rounds Selection -->
      <div>
        <label class="block text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2 flex justify-between">
          面试轮次 (不含开场)
          <span class="text-[#0066CC]">{{ totalRounds }} 轮</span>
        </label>
        <div class="px-2">
          <el-slider 
            v-model="totalRounds" 
            :min="2" 
            :max="10" 
            :step="1"
            :marks="{ 2: '短', 6: '中', 10: '长' }"
          />
        </div>
      </div>

      <!-- Knowledge Points Selection -->
      <div>
        <label class="block text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">重点考察领域 (多选)</label>
        <div v-if="loading" class="flex items-center justify-center py-6">
          <el-icon class="is-loading text-[#0066CC] text-2xl"><Loading /></el-icon>
        </div>
        <div v-else-if="sections.length === 0" class="text-sm text-gray-400 py-2">
          该岗位暂无可选考察方向，面试官将按全流程进行。
        </div>
        <div v-else class="flex flex-wrap gap-3">
          <label
            v-for="s in sections"
            :key="s"
            class="cursor-pointer"
            @click="toggleSection(s)"
          >
            <span
              :class="[
                'px-4 py-2 rounded-lg border text-sm transition-all select-none block',
                selectedSections.includes(s)
                  ? 'bg-[#0066CC] text-white border-[#0066CC]'
                  : 'bg-white border-gray-200 text-gray-700 hover:border-[#0066CC]'
              ]"
            >
              {{ s }}
            </span>
          </label>
        </div>
      </div>

      <!-- GitHub Repo Deep Dive (v3) -->
      <div>
        <label class="block text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2 flex justify-between items-center">
          <span>项目深挖 GitHub 仓库 (可选)</span>
          <span class="text-xs text-gray-400 normal-case tracking-normal">AI 将针对你的真实项目定制提问</span>
        </label>

        <div class="space-y-2">
          <div
            v-for="(repo, idx) in repoSlots"
            :key="idx"
            class="flex items-center gap-2"
          >
            <input
              v-model="repoSlots[idx].url"
              type="text"
              placeholder="https://github.com/username/repo"
              class="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-[#0066CC] transition-colors disabled:bg-gray-50"
              :disabled="repoSlots[idx].analyzing || !!repoSlots[idx].summary"
            />
            <button
              v-if="!repoSlots[idx].summary"
              @click="analyzeRepoSlot(idx)"
              :disabled="!repoSlots[idx].url || repoSlots[idx].analyzing"
              class="px-3 py-2 text-sm rounded-lg border border-[#0066CC] text-[#0066CC] hover:bg-[#E6F0FA] transition-colors disabled:border-gray-200 disabled:text-gray-400 disabled:hover:bg-white whitespace-nowrap"
            >
              <span v-if="repoSlots[idx].analyzing">分析中...</span>
              <span v-else>分析</span>
            </button>
            <button
              v-else
              @click="clearRepoSlot(idx)"
              class="px-3 py-2 text-sm rounded-lg border border-gray-200 text-gray-500 hover:border-red-300 hover:text-red-500 transition-colors whitespace-nowrap"
            >
              移除
            </button>
          </div>

          <!-- 摘要预览卡片 -->
          <div
            v-for="(repo, idx) in repoSlots"
            :key="'s-' + idx"
            v-show="repo.summary"
            class="bg-[#E6F0FA]/40 border border-[#0066CC]/20 rounded-lg px-3 py-2 text-xs text-gray-700"
          >
            <div class="font-semibold text-[#0066CC] mb-0.5">
              ✓ {{ repo.summary?.full_name }}
              <span class="text-gray-500 font-normal">· {{ repo.summary?.main_language }} · ⭐ {{ repo.summary?.stars }}</span>
            </div>
            <div class="text-gray-600 line-clamp-2">{{ repo.summary?.description || '（无描述）' }}</div>
          </div>

          <!-- 错误提示 -->
          <div
            v-for="(repo, idx) in repoSlots"
            :key="'e-' + idx"
            v-show="repo.error"
            class="text-xs text-red-500"
          >
            {{ repo.error }}
          </div>

          <button
            v-if="repoSlots.length < 3"
            @click="addRepoSlot"
            class="w-full py-2 text-xs text-gray-500 border border-dashed border-gray-200 rounded-lg hover:border-[#0066CC] hover:text-[#0066CC] transition-colors"
          >
            + 添加仓库 ({{ repoSlots.length }}/3)
          </button>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex gap-4 pt-2">
        <el-button @click="visible = false" class="!px-6 !border-gray-200 !text-gray-600 hover:!bg-gray-50">取消</el-button>
        <button 
          @click="handleConfirm" 
          class="flex-1 bg-[#0066CC] hover:bg-blue-700 text-white font-bold py-2.5 px-4 rounded transition-colors active:scale-[0.98]"
        >
          确认配置并进入房间
        </button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import api from '@/api'

const props = defineProps({
  roleName: String,
  roleKey: String
})

const emit = defineEmits(['confirm'])

const visible = ref(false)
const difficulty = ref('中等')
const totalRounds = ref(6)
const sections = ref([])
const selectedSections = ref([])
const loading = ref(false)

// v3: GitHub 项目深挖（最多 3 个）
const repoSlots = ref([
  { url: '', analyzing: false, summary: null, error: '' }
])

const open = async (roleKey) => {
  visible.value = true
  loading.value = true
  selectedSections.value = []
  // 每次打开都重置 repo 输入
  repoSlots.value = [{ url: '', analyzing: false, summary: null, error: '' }]

  const targetKey = roleKey || props.roleKey
  if (!targetKey) {
    loading.value = false
    return
  }

  try {
    const { data } = await api.get(`/interview/roles/${targetKey}/sections`)
    sections.value = data
  } catch (err) {
    console.error('Failed to fetch sections:', err)
  } finally {
    loading.value = false
  }
}

const toggleSection = (s) => {
  const idx = selectedSections.value.indexOf(s)
  if (idx > -1) {
    selectedSections.value.splice(idx, 1)
  } else {
    selectedSections.value.push(s)
  }
}

const addRepoSlot = () => {
  if (repoSlots.value.length < 3) {
    repoSlots.value.push({ url: '', analyzing: false, summary: null, error: '' })
  }
}

const clearRepoSlot = (idx) => {
  repoSlots.value[idx] = { url: '', analyzing: false, summary: null, error: '' }
}

const analyzeRepoSlot = async (idx) => {
  const slot = repoSlots.value[idx]
  if (!slot.url) return
  slot.analyzing = true
  slot.error = ''
  slot.summary = null
  try {
    const { data } = await api.post('/interview/repo/analyze', { url: slot.url }, { timeout: 15000 })
    slot.summary = data
  } catch (err) {
    slot.error = err.response?.data?.detail || err.message || '分析失败'
  } finally {
    slot.analyzing = false
  }
}

const handleConfirm = () => {
  // 收集所有非空 URL（不要求必须先点"分析"，后端会再次抓取兜底）
  // 但如果分析过且失败了，就跳过这条，避免明知失败还提交
  const repo_urls = repoSlots.value
    .filter(s => s.url && s.url.trim() && !s.error)
    .map(s => s.url.trim())

  emit('confirm', {
    difficulty: difficulty.value,
    knowledge_points: selectedSections.value,
    total_rounds: totalRounds.value,
    repo_urls
  })
  visible.value = false
}

defineExpose({ open })
</script>

<style>
.custom-clean-dialog {
  border-radius: 12px !important;
}

.custom-clean-dialog .el-dialog__header {
  border-bottom: 1px solid #F3F4F6;
  margin-right: 0;
  padding-bottom: 16px;
}

.custom-clean-dialog .el-dialog__title {
  font-weight: bold;
  color: #1F2937;
  font-size: 1.25rem;
}
</style>