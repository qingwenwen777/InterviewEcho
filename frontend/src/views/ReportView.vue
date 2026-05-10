<template>
  <div class="bg-transparent w-full">
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 min-h-[600px] w-full p-8 md:p-12 max-w-7xl mx-auto mt-6 mb-12">
      
      <!-- 头部信息 -->
      <div class="mb-8 border-b border-gray-200 pb-6 flex justify-between items-end">
        <div>
          <h1 class="text-3xl font-extrabold text-gray-900 tracking-tight">面试评估报告</h1>
          <p class="text-gray-500 mt-2 text-sm" v-if="report">
            岗位：{{ report.role }} | 评估时间：{{ formatDateTime(report.created_at) }} | 综合得分：<span class="text-[#0066CC] font-bold">{{ Number(report.total_score || 0).toFixed(1) }}</span>
          </p>
        </div>
        <div class="flex items-center gap-3 print-hide">
          <button
            @click="exportPdf"
            class="text-sm font-medium text-white bg-[#0066CC] hover:bg-blue-700 px-4 py-2 rounded-lg transition-colors cursor-pointer"
          >
            导出 PDF
          </button>
          <button
            @click="router.push('/profile')"
            class="text-sm font-medium text-[#0066CC] hover:underline decoration-2 underline-offset-4 cursor-pointer"
          >
            返回历史大盘
          </button>
        </div>
      </div>

      <div v-if="report" class="space-y-12">
        <!-- 主体区域：左右分栏 -->
        <div class="flex flex-col md:flex-row gap-10">
          
          <!-- 左侧：雷达图能力可视化 (5/12) -->
          <div class="w-full md:w-5/12 flex flex-col items-center">
            <h3 class="text-lg font-bold text-gray-800 mb-4 self-start">多维度能力图谱</h3>
            <div class="w-full h-[350px] bg-gray-50 rounded-lg p-4 border border-gray-100 flex items-center justify-center">
              <RadarChart :stats="{
                technical_depth: report.content_score,
                communication: report.expression_score,
                business_scenario: report.business_scenario_score,
                problem_solving: report.problem_solving_score
              }" />
            </div>
          </div>

          <!-- 右侧：文字评价与建议 (7/12) -->
          <div class="w-full md:w-7/12 space-y-6">
            
            <!-- 核心优势 -->
            <div>
              <h3 class="text-lg font-bold text-gray-800 mb-3 flex items-center">
                <span class="w-1.5 h-5 bg-green-500 rounded-full mr-2"></span>
                核心优势
              </h3>
              <div class="bg-green-50/50 p-4 rounded-lg border border-green-100">
                <ul class="list-disc list-inside text-gray-600 text-sm leading-relaxed space-y-2 ml-1">
                  <li v-for="(highlight, idx) in parsedReportData.highlights" :key="idx">{{ highlight }}</li>
                </ul>
              </div>
            </div>

            <!-- 改进建议 -->
            <div>
              <h3 class="text-lg font-bold text-gray-800 mb-3 flex items-center">
                <span class="w-1.5 h-5 bg-orange-500 rounded-full mr-2"></span>
                待提升项
              </h3>
              <div class="bg-orange-50/50 p-4 rounded-lg border border-orange-100">
                <ul class="list-disc list-inside text-gray-600 text-sm leading-relaxed space-y-2 ml-1">
                  <li v-for="(weakness, idx) in parsedReportData.weaknesses" :key="idx">{{ weakness }}</li>
                </ul>
              </div>
            </div>

            <!-- 提升建议 -->
            <div>
              <h3 class="text-lg font-bold text-gray-800 mb-3 flex items-center">
                <span class="w-1.5 h-5 bg-[#0066CC] rounded-full mr-2"></span>
                提升建议
              </h3>
              <div class="bg-blue-50/50 p-4 rounded-lg border border-blue-100">
                <p class="text-gray-600 text-sm leading-relaxed whitespace-pre-wrap ml-1">
                  {{ report.recommendations || report.improvement_suggestions || parsedReportData.recommendations || '暂无具体建议，请继续保持练习。' }}
                </p>
              </div>
            </div>

          </div>
        </div>

        <!-- 🌟 V2: 表达能力深度诊断 🌟 -->
        <div v-if="report.expression_metrics" class="pt-10 border-t border-gray-200">
          <div class="mb-8">
            <h1 class="text-2xl font-extrabold text-gray-900 tracking-tight">表达沟通专项分析</h1>
            <p class="text-gray-500 mt-2 text-sm">基于您的语音与语义特征生成的深度声学诊断报告</p>
          </div>

          <div class="flex flex-col md:flex-row gap-10">
            <!-- 左侧：表达图表可视化 (5/12) -->
            <div class="w-full md:w-5/12 flex flex-col items-center">
              <h3 class="text-lg font-bold text-gray-800 mb-4 self-start">表达综合雷达</h3>
              <div class="w-full h-[250px] bg-gray-50 rounded-lg p-4 border border-gray-100 flex items-center justify-center mb-6">
                <RadarChart 
                  :indicators="[
                    { name: '语速节奏', max: 100 },
                    { name: '语义清晰度', max: 100 },
                    { name: '用词自信度', max: 100 }
                  ]"
                  :dataValues="[report.speech_rate_score || 0, report.clarity_score || 0, report.confidence_score || 0]"
                  seriesName="表达能力诊断"
                />
              </div>
              
              <h3 class="text-lg font-bold text-gray-800 mb-4 self-start">语速波动曲线 (wpm)</h3>
              <div class="w-full h-[220px] bg-gray-50 rounded-lg p-2 border border-gray-100">
                <ExpressionLineChart :data="report.expression_metrics.per_message" />
              </div>
            </div>

            <!-- 右侧：文字评价与口头禅分析 (7/12) -->
            <div class="w-full md:w-7/12 space-y-6">
              <!-- 口头禅监控 -->
              <div>
                <h3 class="text-lg font-bold text-gray-800 mb-3 flex items-center">
                  <span class="w-1.5 h-5 bg-rose-500 rounded-full mr-2"></span>
                  习惯填充词监控
                </h3>
                <div class="bg-rose-50/30 p-4 rounded-lg border border-rose-100 min-h-[5rem] flex items-center">
                  <div v-if="report.expression_metrics.metrics_summary.top_filler_words && report.expression_metrics.metrics_summary.top_filler_words.length > 0" class="flex flex-wrap gap-2">
                    <span 
                      v-for="(filler, index) in report.expression_metrics.metrics_summary.top_filler_words" 
                      :key="index"
                      class="rounded px-2.5 py-1 bg-white border border-rose-200 text-rose-700 font-medium shadow-sm"
                      :style="{ fontSize: `${0.8 + filler.count * 0.05}rem` }"
                    >
                      {{ filler.word }} <span class="text-xs text-rose-400 ml-1">x{{ filler.count }}</span>
                    </span>
                  </div>
                  <div v-else class="text-sm text-emerald-600 font-medium w-full text-center">
                    表现极佳，未检测到高频无意义口头禅！
                  </div>
                </div>
              </div>

              <!-- 语速建议 -->
              <div>
                <h3 class="text-lg font-bold text-gray-800 mb-3 flex items-center">
                  <span class="w-1.5 h-5 bg-blue-400 rounded-full mr-2"></span>
                  语速节奏评价
                </h3>
                <div class="bg-blue-50/50 p-4 rounded-lg border border-blue-100">
                  <p class="text-gray-600 text-sm leading-relaxed ml-1">
                    {{ report.expression_metrics.feedback.speech_rate }}
                  </p>
                </div>
              </div>

              <!-- 清晰度建议 -->
              <div>
                <h3 class="text-lg font-bold text-gray-800 mb-3 flex items-center">
                  <span class="w-1.5 h-5 bg-blue-500 rounded-full mr-2"></span>
                  逻辑清晰度评价
                </h3>
                <div class="bg-blue-50/50 p-4 rounded-lg border border-blue-100">
                  <p class="text-gray-600 text-sm leading-relaxed ml-1">
                    {{ report.expression_metrics.feedback.clarity }}
                  </p>
                </div>
              </div>

              <!-- 自信度建议 -->
              <div>
                <h3 class="text-lg font-bold text-gray-800 mb-3 flex items-center">
                  <span class="w-1.5 h-5 bg-[#0066CC] rounded-full mr-2"></span>
                  专业自信度评价
                </h3>
                <div class="bg-blue-50/50 p-4 rounded-lg border border-blue-100">
                  <p class="text-gray-600 text-sm leading-relaxed ml-1">
                    {{ report.expression_metrics.feedback.confidence }}
                  </p>
                </div>
              </div>

            </div>
          </div>
        </div>
        <!-- 🌟 V2 End 🌟 -->

        <!-- 🔮 V3: GitHub 项目深挖专项 🔮 -->
        <div v-if="report.repo_context && report.repo_context.length > 0" class="pt-10 border-t border-gray-200">
          <div class="mb-8">
            <h1 class="text-2xl font-extrabold text-gray-900 tracking-tight">GitHub 项目深挖专项</h1>
            <p class="text-gray-500 mt-2 text-sm">基于您提供的真实项目代码，AI 定制的深度追问分析</p>
          </div>

          <div class="space-y-8">
            <!-- 项目信息卡片（每个 repo 一个） -->
            <div
              v-for="(repo, rIdx) in report.repo_context"
              :key="'repo-' + rIdx"
              class="bg-[#E6F0FA]/40 border border-[#0066CC]/20 rounded-xl p-6"
            >
              <!-- Repo 头部 -->
              <div class="flex items-start justify-between mb-4 pb-4 border-b border-[#0066CC]/15">
                <div class="flex-1">
                  <div class="flex items-center gap-3 mb-2">
                    <span class="w-1.5 h-5 bg-[#0066CC] rounded-full"></span>
                    <h3 class="text-lg font-bold text-gray-800">
                      <a :href="repo.url" target="_blank" class="hover:text-[#0066CC] transition-colors">
                        {{ repo.full_name }}
                      </a>
                    </h3>
                  </div>
                  <p class="text-sm text-gray-600 ml-4">{{ repo.description || '（无项目描述）' }}</p>
                </div>
                <div class="flex flex-col items-end gap-1 text-xs text-gray-500 shrink-0 ml-4">
                  <span class="px-2 py-0.5 rounded-full bg-white border border-[#0066CC]/30 text-[#0066CC] font-medium">
                    {{ repo.main_language || '未知语言' }}
                  </span>
                  <span class="text-gray-400">⭐ {{ repo.stars || 0 }}</span>
                </div>
              </div>

              <!-- 技术栈关键词 -->
              <div v-if="repo.tech_keywords && repo.tech_keywords.length" class="mb-4">
                <div class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">检测到的技术栈</div>
                <div class="flex flex-wrap gap-1.5">
                  <span
                    v-for="kw in repo.tech_keywords.slice(0, 10)"
                    :key="kw"
                    class="px-2 py-0.5 text-xs rounded bg-white border border-gray-200 text-gray-600"
                  >
                    {{ kw }}
                  </span>
                </div>
              </div>

              <!-- 分析到的代码文件 -->
              <div v-if="repo.key_files && repo.key_files.length" class="mb-4">
                <div class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">AI 深度分析的代码文件</div>
                <div class="flex flex-wrap gap-1.5">
                  <span
                    v-for="kf in repo.key_files"
                    :key="kf.path"
                    class="px-2 py-0.5 text-xs rounded bg-[#E6F0FA] border border-[#0066CC]/30 text-[#0066CC] font-mono"
                  >
                    {{ kf.path }}
                  </span>
                </div>
              </div>

              <!-- 针对本项目的定制问题 -->
              <div v-if="customQuestionsForRepo(repo).length > 0" class="mt-4">
                <div class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">AI 针对此项目生成的深挖问题</div>
                <div class="space-y-3">
                  <div
                    v-for="(q, qIdx) in customQuestionsForRepo(repo)"
                    :key="'q-' + qIdx"
                    class="bg-white/70 border border-[#0066CC]/15 rounded-lg p-4"
                  >
                    <div class="flex items-start gap-3">
                      <span class="shrink-0 w-6 h-6 rounded-full bg-[#0066CC] text-white text-xs flex items-center justify-center font-bold mt-0.5">
                        {{ qIdx + 1 }}
                      </span>
                      <div class="flex-1 min-w-0">
                        <p class="text-sm text-gray-800 leading-relaxed">{{ q.question }}</p>
                        <div v-if="q.tech_focus" class="mt-2 flex items-center gap-2">
                          <span class="text-xs text-gray-400">考察焦点：</span>
                          <span class="text-xs px-2 py-0.5 rounded bg-[#E6F0FA] text-[#0066CC] border border-[#0066CC]/20">
                            {{ q.tech_focus }}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <!-- 🔮 V3 End 🔮 -->

        <!-- V4: 能力提升计划（赛题 3)4)a） -->
        <div v-if="report.study_plan" class="pt-10 border-t border-gray-200">
          <div class="mb-8">
            <h1 class="text-2xl font-extrabold text-gray-900 tracking-tight">能力提升计划</h1>
            <p class="text-gray-500 mt-2 text-sm">基于评估结果为您定制的分周学习路径与资源推荐</p>
          </div>

          <!-- 薄弱领域诊断 -->
          <div v-if="report.study_plan.weak_areas && report.study_plan.weak_areas.length" class="mb-8">
            <h3 class="text-lg font-bold text-gray-800 mb-3 flex items-center">
              <span class="w-1.5 h-5 bg-orange-500 rounded-full mr-2"></span>
              薄弱领域诊断
            </h3>
            <div class="space-y-3">
              <div
                v-for="(wa, idx) in report.study_plan.weak_areas"
                :key="'wa-' + idx"
                class="bg-orange-50/40 border border-orange-100 rounded-lg p-4 flex items-start gap-3"
              >
                <span
                  :class="[
                    'shrink-0 text-xs font-bold px-2 py-0.5 rounded border mt-0.5',
                    wa.severity === '高' ? 'bg-red-50 text-red-600 border-red-200' :
                      wa.severity === '中' ? 'bg-orange-50 text-orange-600 border-orange-200' :
                        'bg-gray-50 text-gray-600 border-gray-200'
                  ]"
                >{{ wa.severity || '中' }}</span>
                <div class="flex-1 min-w-0">
                  <div class="font-semibold text-gray-800 text-sm mb-1">{{ wa.area }}</div>
                  <p class="text-sm text-gray-600 leading-relaxed">{{ wa.diagnosis }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- 分周计划 -->
          <div v-if="report.study_plan.plan && report.study_plan.plan.length" class="mb-8">
            <h3 class="text-lg font-bold text-gray-800 mb-3 flex items-center">
              <span class="w-1.5 h-5 bg-[#0066CC] rounded-full mr-2"></span>
              分周学习计划
            </h3>
            <div class="space-y-4">
              <div
                v-for="(w, idx) in report.study_plan.plan"
                :key="'wk-' + idx"
                class="bg-[#E6F0FA]/40 border border-[#0066CC]/20 rounded-xl p-5"
              >
                <div class="flex items-center gap-3 mb-3 pb-3 border-b border-[#0066CC]/15">
                  <span class="shrink-0 w-10 h-10 rounded-full bg-[#0066CC] text-white text-sm flex items-center justify-center font-bold">
                    W{{ w.week || idx + 1 }}
                  </span>
                  <div class="flex-1">
                    <div class="font-bold text-gray-800">{{ w.focus || `第 ${w.week || idx + 1} 周` }}</div>
                  </div>
                </div>

                <!-- 任务清单 -->
                <div v-if="w.tasks && w.tasks.length" class="mb-3">
                  <div class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">本周任务</div>
                  <ul class="space-y-1.5 ml-1">
                    <li
                      v-for="(task, tIdx) in w.tasks"
                      :key="'task-' + tIdx"
                      class="text-sm text-gray-700 leading-relaxed flex items-start gap-2"
                    >
                      <span class="shrink-0 mt-1.5 w-1.5 h-1.5 rounded-full bg-[#0066CC]"></span>
                      <span class="flex-1">{{ task }}</span>
                    </li>
                  </ul>
                </div>

                <!-- 资源推荐 -->
                <div v-if="w.resources && w.resources.length">
                  <div class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">推荐资源</div>
                  <div class="flex flex-wrap gap-2">
                    <span
                      v-for="(r, rIdx) in w.resources"
                      :key="'r-' + rIdx"
                      class="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs bg-white border border-[#0066CC]/30 rounded text-gray-700"
                    >
                      <span class="text-[#0066CC] font-semibold uppercase">{{ resourceTypeLabel(r.type) }}</span>
                      <span class="text-gray-800">{{ r.title }}</span>
                      <span v-if="r.note" class="text-gray-400">· {{ r.note }}</span>
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 快速收益 -->
          <div v-if="report.study_plan.quick_wins && report.study_plan.quick_wins.length">
            <h3 class="text-lg font-bold text-gray-800 mb-3 flex items-center">
              <span class="w-1.5 h-5 bg-green-500 rounded-full mr-2"></span>
              本周快速收益
            </h3>
            <div class="bg-green-50/40 border border-green-100 rounded-lg p-4">
              <ul class="space-y-2 ml-1">
                <li
                  v-for="(qw, idx) in report.study_plan.quick_wins"
                  :key="'qw-' + idx"
                  class="text-sm text-gray-700 leading-relaxed flex items-start gap-2"
                >
                  <span class="shrink-0 mt-1.5 w-1.5 h-1.5 rounded-full bg-green-500"></span>
                  <span class="flex-1">{{ qw }}</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
        <!-- V4 End -->

      </div>
      
      <!-- 加载占位 -->
      <div v-else class="text-center text-gray-500 py-20 flex flex-col items-center justify-center">
        <svg class="w-10 h-10 text-gray-300 mb-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
        <span>正在为您加载专业评估报告...</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api'
import { ElMessage } from 'element-plus'
import RadarChart from '@/components/analytics/RadarChart.vue'
import ExpressionLineChart from '@/components/analytics/ExpressionLineChart.vue'

const route = useRoute()
const router = useRouter()
const report = ref(null)
const loading = ref(false)

onMounted(async () => {
  if (history.state && history.state.evaluation) {
    report.value = history.state.evaluation
    return
  }

  const evalId = route.params.id
  if (evalId) {
    loading.value = true
    try {
      const { data } = await api.get(`/interview/${evalId}/evaluation`)
      report.value = data
    } catch (err) {
      ElMessage.error('无法加载评估报告')
      router.push('/dashboard')
    } finally {
      loading.value = false
    }
  }
})

const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

// v3: 按 repo 过滤定制问题（每个 repo 只显示自己的问题）
const customQuestionsForRepo = (repo) => {
  if (!report.value?.custom_questions || !repo?.full_name) return []
  return report.value.custom_questions.filter(q => q.repo === repo.full_name)
}

// 导出 PDF：触发浏览器打印对话框，用户可"另存为 PDF"
const exportPdf = () => {
  // 提示使用习惯：快捷键 Ctrl+P，打印窗口"目标"选 "另存为 PDF"
  window.print()
}

// v4: 学习计划资源类型中文映射
const resourceTypeLabel = (type) => {
  const map = {
    book: '书籍',
    article: '文章',
    video: '视频',
    course: '课程',
    blog: '博客',
    doc: '文档',
    paper: '论文'
  }
  return map[type?.toLowerCase()] || (type || '资源')
}

const parsedReportData = computed(() => {
  if (!report.value) return { highlights: [], weaknesses: [], recommendations: '' }

  if (report.value.report_json) {
    try {
      const data = typeof report.value.report_json === 'string'
        ? JSON.parse(report.value.report_json)
        : report.value.report_json
      return {
        highlights: data.highlights || data.strengths || [],
        weaknesses: data.weaknesses || [],
        recommendations: data.recommendations || data.improvement_suggestions || ''
      }
    } catch (e) {
      return { highlights: ['评估数据解析异常'], weaknesses: [], recommendations: '' }
    }
  }

  return {
    highlights: report.value.highlights || report.value.strengths || [],
    weaknesses: report.value.weaknesses || [],
    recommendations: report.value.recommendations || report.value.improvement_suggestions || ''
  }
})
</script>

<style>
/* 打印 / PDF 导出专用样式 */
@media print {

  /* 1. 强制 A4 纸张 + 合理边距 */
  @page {
    size: A4;
    margin: 12mm 10mm;
  }

  /* 2. 重置全局背景 + 颜色，让背景色能打印出来 */
  html,
  body {
    background: white !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    color-adjust: exact !important;
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
  }

  /* 3. 隐藏所有不该出现在 PDF 里的元素 */
  .print-hide,
  .el-header,
  .el-aside,
  nav,
  aside,
  header,
  button,
  .el-button {
    display: none !important;
  }

  /* 4. 重置外层卡片：去阴影/边框/圆角，占满纸宽 */
  .bg-white,
  .bg-transparent {
    box-shadow: none !important;
    border: none !important;
    border-radius: 0 !important;
    max-width: 100% !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    min-height: auto !important;
  }

  /* 5. 把所有 md:flex-row 强制改成纵向（一列），避免 PDF 上左右挤一团 */
  .flex.md\:flex-row,
  .flex-col.md\:flex-row {
    flex-direction: column !important;
    gap: 16px !important;
  }

  /* 6. 把所有 md:w-5/12 / md:w-7/12 改成 100% */
  .md\:w-5\/12,
  .md\:w-7\/12,
  [class*="md:w-"] {
    width: 100% !important;
  }

  /* 7. 缩小图表容器高度 */
  .h-\[600px\] {
    height: auto !important;
    min-height: 0 !important;
  }

  .h-\[350px\] {
    height: 240px !important;
  }

  .h-\[250px\] {
    height: 180px !important;
  }

  .h-\[220px\] {
    height: 160px !important;
  }

  /* 8. 避免标题/卡片被分页切断 */
  h1,
  h2,
  h3 {
    page-break-after: avoid !important;
    break-after: avoid !important;
  }

  .rounded-xl,
  .rounded-lg,
  .border {
    page-break-inside: avoid !important;
    break-inside: avoid !important;
  }

  /* 9. 大模块顶部加一点空间 */
  .pt-10 {
    padding-top: 16px !important;
  }

  /* 10. 字体压缩一点，节省纸张 */
  body,
  p,
  li,
  span {
    font-size: 12px !important;
    line-height: 1.5 !important;
  }

  h1 {
    font-size: 22px !important;
  }

  h2 {
    font-size: 18px !important;
  }

  h3 {
    font-size: 14px !important;
  }

  .text-3xl {
    font-size: 22px !important;
  }

  .text-2xl {
    font-size: 18px !important;
  }

  .text-lg {
    font-size: 14px !important;
  }

  .text-sm {
    font-size: 12px !important;
  }

  .text-xs {
    font-size: 11px !important;
  }

  /* 11. 链接颜色保留（不要变黑） */
  a {
    color: #0066CC !important;
    text-decoration: none !important;
  }
}
</style>
