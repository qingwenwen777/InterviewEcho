import axios from 'axios'

const configuredApiBaseURL = import.meta.env.VITE_API_URL
const apiBaseURL =
  import.meta.env.PROD && configuredApiBaseURL?.includes('localhost:8000')
    ? '/api'
    : configuredApiBaseURL || '/api'

const api = axios.create({
  baseURL: apiBaseURL,
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
    return Promise.reject(error)
  },
)

export default api
