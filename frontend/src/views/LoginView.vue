<template>
  <div class="flex items-center justify-center min-h-[90vh] bg-[#F9FAFB]">
    <div class="w-full max-w-md p-1">
      <div class="bg-white rounded-[2.5rem] shadow-2xl overflow-hidden border border-gray-100 p-10 relative">
        <!-- Decoration -->
        <div class="absolute -top-12 -right-12 w-40 h-40 bg-primary opacity-5 rounded-full"></div>
        <div class="absolute -bottom-12 -left-12 w-40 h-40 bg-secondary opacity-5 rounded-full"></div>

        <div class="relative z-10">
          <div class="text-center mb-10">
            <h1 class="text-3xl font-black text-gray-900 tracking-tight mb-2">
              {{ isRegister ? '创建新账号' : '欢迎回来' }}
            </h1>
            <p class="text-gray-400 font-medium">
              {{ isRegister ? '加入 InterviewEcho，开启您的 AI 面试之旅' : '模拟面试，从 InterviewEcho 开始' }}
            </p>
          </div>

          <el-form :model="form" :rules="rules" ref="formRef" label-position="top" class="custom-form">
            <el-form-item label="用户名" prop="username">
              <el-input 
                v-model="form.username" 
                placeholder="请输入您的用户名" 
                class="!rounded-2xl"
                size="large"
              ></el-input>
            </el-form-item>
            
            <el-form-item label="密码" prop="password">
              <el-input 
                v-model="form.password" 
                type="password" 
                placeholder="请输入密码" 
                show-password
                class="!rounded-2xl"
                size="large"
              ></el-input>
            </el-form-item>

            <div class="mt-10 space-y-4">
              <el-button 
                type="primary" 
                class="w-full !rounded-[1.2rem] !py-7 !text-lg !font-bold shadow-lg shadow-indigo-100 transition-all hover:scale-[1.02] active:scale-95" 
                @click="handleSubmit" 
                :loading="loading"
              >
                {{ isRegister ? '注 册' : '登 录' }}
              </el-button>
              
              <div class="text-center">
                <button 
                  type="button"
                  class="text-sm font-bold text-gray-400 hover:text-primary transition-colors flex items-center justify-center mx-auto"
                  @click="toggleMode"
                >
                  {{ isRegister ? '已有账号？立即登录' : '没有账号？创建新账号' }}
                </button>
              </div>
            </div>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import api from '@/api'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref(null)
const loading = ref(false)
const isRegister = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const toggleMode = () => {
  isRegister.value = !isRegister.value
  formRef.value?.resetFields()
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        if (isRegister.value) {
          await api.post('/auth/register', form)
          ElMessage.success('注册成功，请使用新账号登录')
          isRegister.value = false
        } else {
          const { data } = await api.post('/auth/login', form)
          authStore.login(data.access_token, { username: form.username })
          ElMessage.success('登录成功')
          router.push('/dashboard')
        }
      } catch (err) {
        ElMessage.error(err.response?.data?.detail || (isRegister.value ? '注册失败' : '登录失败'))
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.custom-form :deep(.el-form-item__label) {
  font-weight: 700;
  color: #374151;
  padding-bottom: 8px;
  font-size: 0.875rem;
}
.custom-form :deep(.el-input__wrapper) {
  border-radius: 12px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  padding: 4px 12px;
}
</style>
