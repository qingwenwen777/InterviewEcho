import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'
import { createPortal } from 'react-dom'
import CodeMirror from '@uiw/react-codemirror'
import { cpp } from '@codemirror/lang-cpp'
import { java } from '@codemirror/lang-java'
import { javascript } from '@codemirror/lang-javascript'
import { python } from '@codemirror/lang-python'
import { indentWithTab } from '@codemirror/commands'
import { indentUnit } from '@codemirror/language'
import { EditorView, keymap } from '@codemirror/view'
import {
  Navigate,
  NavLink,
  Outlet,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams,
  useSearchParams,
} from 'react-router-dom'
import * as echarts from 'echarts'
import {
  Activity,
  ArrowLeft,
  ArrowUp,
  AudioLines,
  BarChart3,
  Bot,
  BrainCircuit,
  CalendarClock,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Code2,
  Download,
  FileText,
  Gauge,
  Github,
  History,
  Home,
  LoaderCircle,
  LogIn,
  LogOut,
  MessageCircle,
  Mic,
  Moon,
  Play,
  Plus,
  Settings,
  Sparkles,
  Square,
  Sun,
  TimerReset,
  Trophy,
  UserRound,
  Volume2,
  VolumeX,
  X,
} from 'lucide-react'
import api from './api'

const FALLBACK_ROLES = [
  {
    id: 1,
    name: 'Java后端开发工程师',
    key: 'java-backend',
    desc: '围绕 JVM、并发、Spring、数据库与系统设计展开。',
  },
  {
    id: 2,
    name: 'Web前端开发工程师',
    key: 'web-frontend',
    desc: '聚焦 React/Vue、浏览器机制、性能优化与工程化。',
  },
  {
    id: 3,
    name: 'Python算法工程师',
    key: 'python-algorithm',
    desc: '覆盖数据结构、机器学习基础、模型调优与工程落地。',
  },
]

const DIFFICULTIES = ['简单', '中等', '困难']
const CODE_LANGUAGE_OPTIONS = [
  { value: 'python', label: 'Python' },
  { value: 'java', label: 'Java' },
  { value: 'cpp', label: 'C++' },
  { value: 'javascript', label: 'JavaScript' },
]
const CODE_EDITOR_EXTENSIONS = {
  python,
  java,
  cpp,
  javascript,
}
const CODE_EDITOR_THEME = EditorView.theme(
  {
    '&': {
      minHeight: '460px',
      backgroundColor: '#101010',
      color: '#f4f1e8',
      fontSize: '14px',
    },
    '.cm-content': {
      caretColor: '#fffdf7',
      padding: '18px 0',
    },
    '.cm-line': {
      padding: '0 18px',
      lineHeight: '1.66',
    },
    '.cm-scroller': {
      fontFamily: 'var(--mono)',
      overflow: 'auto',
    },
    '.cm-gutters': {
      backgroundColor: '#101010',
      borderRight: '1px solid rgba(255, 253, 247, 0.1)',
      color: 'rgba(255, 253, 247, 0.42)',
    },
    '.cm-activeLineGutter': {
      backgroundColor: 'rgba(255, 253, 247, 0.06)',
      color: '#fffdf7',
    },
    '.cm-activeLine': {
      backgroundColor: 'rgba(255, 253, 247, 0.035)',
    },
    '.cm-selectionBackground, &.cm-focused .cm-selectionBackground': {
      backgroundColor: 'rgba(232, 214, 166, 0.82)',
    },
    '.cm-selectionMatch': {
      backgroundColor: 'rgba(232, 214, 166, 0.24)',
      outline: '1px solid rgba(232, 214, 166, 0.42)',
    },
    '.cm-content ::selection': {
      backgroundColor: 'rgba(232, 214, 166, 0.92)',
      color: '#111',
    },
    '&.cm-focused': {
      outline: 'none',
    },
  },
  { dark: true },
)
const CODE_STATUS_TEXT = {
  Running: 'Running',
  Accepted: 'Accepted',
  'Wrong Answer': 'Wrong Answer',
  'Compile Error': 'Compile Error',
  'Runtime Error': 'Runtime Error',
  'Time Limit Exceeded': 'Time Limit Exceeded',
  'Judge Error': 'Judge Error',
}
const CODE_JUDGE_TIMEOUT_MS = 240000
const CODE_RESULT_SYNC_ATTEMPTS = 80
const CODE_RESULT_SYNC_INTERVAL_MS = 2000
const CODE_PAGE_SIZE = 20
const PROFILE_HISTORY_PAGE_SIZE = 8
const PROFILE_PROJECT_LIMIT = 8
const CODE_PENDING_STATUSES = new Set(['Running'])
const CODE_CLIENT_ERROR_RESULT = {
  index: 1,
  is_sample: false,
  passed: false,
  status: 'Judge Error',
  input: null,
  expected_output: null,
  actual_output: null,
  stderr: null,
  compile_output: null,
}
const wait = (ms) =>
  new Promise((resolve) => {
    window.setTimeout(resolve, ms)
  })
const INTERVIEW_AUTO_END_MIN_DELAY_MS = 4500
const INTERVIEW_AUTO_END_MAX_DELAY_MS = 8500
const VOICE_REPLY_POLL_INTERVAL_MS = 1000
const VOICE_REPLY_MAX_POLL_ATTEMPTS = 90
const VOICE_REPLY_MAX_POLL_FAILURES = 5
const TTS_SETTINGS_STORAGE_KEY = 'interviewecho-tts-settings'
const INTERVIEW_TTS_VOICES = [
  { id: 'mimo_default', label: '默认' },
  { id: '冰糖', label: '冰糖' },
  { id: '茉莉', label: '茉莉' },
  { id: '苏打', label: '苏打' },
  { id: '白桦', label: '白桦' },
  { id: 'Mia', label: 'Mia' },
  { id: 'Chloe', label: 'Chloe' },
  { id: 'Milo', label: 'Milo' },
  { id: 'Dean', label: 'Dean' },
]
const INTERVIEW_TTS_SPEEDS = [
  { id: 'slow', label: '慢速' },
  { id: 'normal', label: '标准' },
  { id: 'fast', label: '稍快' },
]
const INTERVIEW_TTS_STYLES = [
  { id: 'calm', label: '克制' },
  { id: 'warm', label: '温和' },
  { id: 'strict', label: '严谨' },
]
const DEFAULT_TTS_SETTINGS = {
  autoPlay: true,
  voice: 'mimo_default',
  speed: 'normal',
  style: 'calm',
}
function readStoredTtsSettings() {
  try {
    const saved = JSON.parse(localStorage.getItem(TTS_SETTINGS_STORAGE_KEY) || 'null')
    if (!saved || typeof saved !== 'object') return DEFAULT_TTS_SETTINGS
    return { ...DEFAULT_TTS_SETTINGS, ...saved }
  } catch {
    return DEFAULT_TTS_SETTINGS
  }
}

const isCodeFinalStatus = (status) => Boolean(status) && !CODE_PENDING_STATUSES.has(status)
const toCodeSubmissionResult = (detail) => ({
  submission_id: detail.id,
  status: detail.status,
  passed_count: detail.passed_count ?? 0,
  total_count: detail.total_count ?? 0,
  results: detail.results || [],
})
const SECTION_SKELETON_GROUPS = [
  { label: '基础技术', widths: [88, 112, 96, 132] },
  { label: '工程能力', widths: [150, 176, 102, 92] },
  { label: '软技能', widths: [98, 136, 112] },
]
const EVALUATION_POLL_INTERVAL_MS = 2500

function evaluationStatusText(status) {
  if (status === 'evaluating') return '评估报告正在生成，请稍等片刻。'
  if (status === 'evaluation_failed') return '评估报告生成失败，请稍后重试。'
  if (status === 'completed') return '评估报告已生成，正在加载。'
  return '正在检查评估报告状态。'
}

function isHistoryCompleted(item) {
  return !item?.status || item.status === 'completed'
}

function isHistoryGenerating(item) {
  return item?.status === 'evaluating'
}

function isHistoryFailed(item) {
  return item?.status === 'evaluation_failed'
}

function sectionGroupLabel(section) {
  if (/沟通|协作|冲突|应急|管理|排期|表达|复盘|软/.test(section)) return '软技能'
  if (/工程|工具|架构|落地|调优|优化|性能|安全|项目|实践|部署|测试|链|排查/.test(section)) return '工程能力'
  return '基础技术'
}

function groupInterviewSections(sections) {
  const groups = [
    { label: '基础技术', items: [] },
    { label: '工程能力', items: [] },
    { label: '软技能', items: [] },
  ]

  sections.forEach((section) => {
    const group = groups.find((item) => item.label === sectionGroupLabel(section)) || groups[0]
    group.items.push(section)
  })

  return groups.filter((group) => group.items.length)
}

function roundsTone(rounds) {
  const value = Number(rounds)
  if (value <= 4) return '短'
  if (value >= 8) return '深'
  return '标准'
}
const BRAND_WORDS = ['Interview', 'Improve', 'Insight', 'Iterate']
const ECHO_WORD = 'Echo'
let homeIntroHasPlayed = false

const AuthContext = createContext(null)
const ToastContext = createContext(null)

function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/interview/:role"
            element={
              <ProtectedRoute>
                <InterviewRoom />
              </ProtectedRoute>
            }
          />
          <Route element={<MainLayout />}>
            <Route index element={<HomePage />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <ProfilePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/account"
              element={
                <ProtectedRoute>
                  <AccountPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/code"
              element={
                <ProtectedRoute>
                  <CodePracticePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/code/problems/:problemId"
              element={
                <ProtectedRoute>
                  <CodeProblemPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/report/:id"
              element={
                <ProtectedRoute>
                  <ReportPage />
                </ProtectedRoute>
              }
            />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </ToastProvider>
    </AuthProvider>
  )
}

function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('token') || '')
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('user') || 'null')
    } catch {
      return null
    }
  })

  const login = useCallback((newToken, userData) => {
    setToken(newToken)
    setUser(userData)
    localStorage.setItem('token', newToken)
    localStorage.setItem('user', JSON.stringify(userData))
  }, [])

  const logout = useCallback(() => {
    setToken('')
    setUser(null)
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }, [])

  const value = useMemo(
    () => ({ token, user, isAuthenticated: Boolean(token), login, logout }),
    [token, user, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

function useAuth() {
  return useContext(AuthContext)
}

function ToastProvider({ children }) {
  const [items, setItems] = useState([])

  const push = useCallback((message, tone = 'info') => {
    const id = crypto.randomUUID?.() || `${Date.now()}-${Math.random()}`
    setItems((current) => [...current, { id, message, tone }])
    window.setTimeout(() => {
      setItems((current) => current.filter((item) => item.id !== id))
    }, 3600)
  }, [])

  return (
    <ToastContext.Provider value={push}>
      {children}
      <div className="toast-stack" aria-live="polite">
        {items.map((item) => (
          <div className={`toast ${item.tone}`} key={item.id}>
            <span className="toast-dot" />
            {item.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

function useToast() {
  return useContext(ToastContext)
}

function useDampedSnapScroll(ref) {
  useEffect(() => {
    const element = ref.current
    if (!element) return undefined
    let locked = false
    const getSections = () => Array.from(element.children).filter((child) => child.classList.contains('review-snap-section'))
    const onWheel = (event) => {
      const sections = getSections()
      if (sections.length < 2 || Math.abs(event.deltaY) < 28) return
      event.preventDefault()
      if (locked) return
      const currentTop = element.scrollTop
      const currentIndex = sections.reduce((nearest, section, index) => {
        const nearestDistance = Math.abs(sections[nearest].offsetTop - currentTop)
        const nextDistance = Math.abs(section.offsetTop - currentTop)
        return nextDistance < nearestDistance ? index : nearest
      }, 0)
      const nextIndex = Math.max(0, Math.min(sections.length - 1, currentIndex + (event.deltaY > 0 ? 1 : -1)))
      if (nextIndex === currentIndex) return
      locked = true
      element.scrollTo({ top: sections[nextIndex].offsetTop, behavior: 'smooth' })
      window.setTimeout(() => {
        locked = false
      }, 760)
    }
    element.addEventListener('wheel', onWheel, { passive: false })
    return () => element.removeEventListener('wheel', onWheel)
  }, [ref])
}

function ProtectedRoute({ children }) {
  const auth = useAuth()
  const location = useLocation()
  if (!auth.isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  }
  return children
}

function MainLayout() {
  const auth = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = () => {
    auth.logout()
    navigate('/')
  }

  return (
    <div className="app-shell">
      <header className="sidebar">
        <button className="brand nav-brand" onClick={() => navigate('/')} aria-label="InterviewEcho 首页">
          <span className="brand-mark">
            <BrandIcon />
          </span>
        </button>

        <nav className="nav-links" aria-label="主导航">
          <SideLink to="/" label="工作台" />
          <SideLink to="/dashboard" label="模拟面试" />
          <SideLink to="/code" label="代码练习" />
          <SideLink to="/profile" label="能力历史" />
        </nav>

        <div className="sidebar-user">
          {auth.isAuthenticated ? (
            <>
              <button className="user-chip" type="button" onClick={() => navigate('/account')} title="用户中心">
                <UserRound size={17} />
                <b>{auth.user?.username || '候选人'}</b>
              </button>
              <button className="button primary nav-cta" onClick={handleLogout} title="退出登录">
                退出
              </button>
            </>
          ) : (
            <>
              <button className="button ghost nav-login" onClick={() => navigate('/login')}>
                登录
              </button>
              <button className="button primary nav-cta" onClick={() => navigate('/login')}>
                开始使用
              </button>
            </>
          )}
        </div>
      </header>
      <main
        className={`main-pane ${location.pathname === '/' ? 'home-main-pane' : ''} ${
          location.pathname === '/profile' || location.pathname === '/account' || location.pathname.startsWith('/report/') ? 'review-main-pane' : ''
        } ${location.pathname.startsWith('/code') ? 'code-main-pane' : ''}`}
      >
        <Outlet />
      </main>
    </div>
  )
}

function BrandIcon() {
  return (
    <svg viewBox="10 8 44 48" aria-hidden="true">
      <g fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round">
        <path
          vectorEffect="non-scaling-stroke"
          strokeWidth="4.1"
          d="M18.4 13.2C23.7 11.7 40.3 11.7 45.6 13.2C47.5 13.8 48 16 46.3 17.3C41.7 20.8 36.2 26 32 32C36.2 38 41.7 43.2 46.3 46.7C48 48 47.5 50.2 45.6 50.8C40.3 52.3 23.7 52.3 18.4 50.8C16.5 50.2 16 48 17.7 46.7C22.3 43.2 27.8 38 32 32C27.8 26 22.3 20.8 17.7 17.3C16 16 16.5 13.8 18.4 13.2Z"
        />
      </g>
    </svg>
  )
}

function SideLink({ to, label }) {
  return (
    <NavLink to={to} end={to === '/'} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
      <span>{label}</span>
    </NavLink>
  )
}

const TITLE_CHAR_WIDTH = {
  a: 0.47,
  b: 0.5,
  c: 0.45,
  d: 0.52,
  e: 0.46,
  f: 0.34,
  g: 0.5,
  h: 0.5,
  i: 0.24,
  j: 0.28,
  k: 0.46,
  l: 0.25,
  m: 0.78,
  n: 0.5,
  o: 0.5,
  p: 0.5,
  q: 0.5,
  r: 0.36,
  s: 0.4,
  t: 0.32,
  u: 0.5,
  v: 0.48,
  w: 0.72,
  x: 0.48,
  y: 0.48,
  z: 0.42,
}

function estimateTitleWidth(text, count = text.length) {
  return Array.from(text)
    .slice(0, count)
    .reduce((sum, letter) => sum + (TITLE_CHAR_WIDTH[letter.toLowerCase()] ?? 0.5), 0)
}

function titleStepDelay(seed, base) {
  const offsets = [0, 14, -6, 10, 4, -4]
  return Math.max(56, base + offsets[Math.abs(seed) % offsets.length])
}

function HomeIntroIcon() {
  return (
    <svg className="home-intro-icon" viewBox="10 8 44 48" aria-hidden="true">
      <g fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round">
        <path
          className="home-intro-icon-path"
          pathLength="1"
          strokeWidth="4.1"
          d="M18.4 13.2C23.7 11.7 40.3 11.7 45.6 13.2C47.5 13.8 48 16 46.3 17.3C41.7 20.8 36.2 26 32 32C36.2 38 41.7 43.2 46.3 46.7C48 48 47.5 50.2 45.6 50.8C40.3 52.3 23.7 52.3 18.4 50.8C16.5 50.2 16 48 17.7 46.7C22.3 43.2 27.8 38 32 32C27.8 26 22.3 20.8 17.7 17.3C16 16 16.5 13.8 18.4 13.2Z"
        />
      </g>
    </svg>
  )
}

function useHomeIntroTitle(words, playIntro, onIntroComplete) {
  const [wordIndex, setWordIndex] = useState(0)
  const currentWord = words[wordIndex % words.length] || 'Interview'
  const prefix = currentWord.startsWith('I') ? currentWord.slice(1) : currentWord
  const [phase, setPhase] = useState(playIntro ? 'drawIcon' : 'cyclePrefixWords')
  const [cycleMode, setCycleMode] = useState(playIntro ? 'intro' : 'hold')
  const [echoCount, setEchoCount] = useState(playIntro ? 0 : ECHO_WORD.length)
  const [prefixCount, setPrefixCount] = useState(playIntro ? 0 : prefix.length)
  const completedRef = useRef(!playIntro)

  const completeIntro = useCallback(() => {
    if (completedRef.current) return
    completedRef.current = true
    homeIntroHasPlayed = true
    onIntroComplete?.()
  }, [onIntroComplete])

  useEffect(() => {
    let timeout

    if (phase === 'drawIcon') {
      timeout = window.setTimeout(() => setPhase('iconGrow'), 820)
    } else if (phase === 'iconGrow') {
      timeout = window.setTimeout(() => setPhase('typeEcho'), 920)
    } else if (phase === 'typeEcho') {
      if (echoCount < ECHO_WORD.length) {
        timeout = window.setTimeout(
          () => setEchoCount((value) => Math.min(ECHO_WORD.length, value + 1)),
          titleStepDelay(echoCount, 100),
        )
      } else {
        timeout = window.setTimeout(() => setPhase('typePrefix'), 180)
      }
    } else if (phase === 'typePrefix') {
      if (prefixCount < prefix.length) {
        timeout = window.setTimeout(
          () => setPrefixCount((value) => Math.min(prefix.length, value + 1)),
          titleStepDelay(prefixCount, 86),
        )
      } else {
        timeout = window.setTimeout(() => {
          completeIntro()
          setCycleMode('hold')
          setPhase('cyclePrefixWords')
        }, 620)
      }
    } else if (phase === 'cyclePrefixWords') {
      if (cycleMode === 'hold') {
        timeout = window.setTimeout(() => setCycleMode('delete'), 1500)
      } else if (cycleMode === 'delete') {
        if (prefixCount > 0) {
          timeout = window.setTimeout(
            () => setPrefixCount((value) => Math.max(0, value - 1)),
            titleStepDelay(prefixCount, 68),
          )
        } else {
          timeout = window.setTimeout(() => {
            setWordIndex((value) => (value + 1) % words.length)
            setCycleMode('type')
          }, 180)
        }
      } else if (cycleMode === 'type') {
        if (prefixCount < prefix.length) {
          timeout = window.setTimeout(
            () => setPrefixCount((value) => Math.min(prefix.length, value + 1)),
            titleStepDelay(prefixCount, 84),
          )
        } else {
          timeout = window.setTimeout(() => setCycleMode('hold'), 460)
        }
      }
    }

    return () => window.clearTimeout(timeout)
  }, [completeIntro, cycleMode, echoCount, phase, prefix.length, prefixCount, words.length])

  return {
    currentWord,
    prefix,
    prefixLetters: Array.from(prefix),
    prefixCount,
    prefixWidthEm: estimateTitleWidth(prefix, prefixCount) + prefixCount * 0.055,
    echoLetters: Array.from(ECHO_WORD),
    echoCount,
    phase,
    cycleMode,
    playIntro,
  }
}

function HomeIntroTitle({ onIntroComplete }) {
  const [playIntro] = useState(() => !homeIntroHasPlayed)
  const title = useHomeIntroTitle(BRAND_WORDS, playIntro, onIntroComplete)

  return (
    <h1
      className="hero-title workbench-title home-intro-title"
      data-phase={title.phase}
      data-cycle-mode={title.cycleMode}
      data-intro={title.playIntro ? 'true' : 'false'}
      aria-label={`${title.currentWord}${ECHO_WORD} 面试练习工作台`}
    >
      <span
        className="home-intro-line"
        style={{ '--prefix-width-em': `${title.prefixWidthEm}em` }}
        aria-hidden="true"
      >
        <span className="home-intro-icon-wrap">
          <HomeIntroIcon />
        </span>
        <span className="home-prefix-window">
          <span className="home-prefix-word">
            {title.prefixLetters.map((letter, index) => {
              const isVisible = index < title.prefixCount
              const letterWidth = (TITLE_CHAR_WIDTH[letter.toLowerCase()] ?? 0.5) + 0.055
              return (
                <span
                  className={`home-title-letter ${isVisible ? 'is-visible' : ''}`}
                  key={`${title.currentWord}-${letter}-${index}`}
                  style={{ '--letter-em': `${letterWidth}em`, '--letter-index': index }}
                >
                  {letter}
                </span>
              )
            })}
          </span>
        </span>
        <span className="home-echo-word">
          {title.echoLetters.map((letter, index) => {
            const letterWidth = (TITLE_CHAR_WIDTH[letter.toLowerCase()] ?? 0.5) + 0.055
            return (
              <span
                className={`home-echo-letter ${index < title.echoCount ? 'is-visible' : ''}`}
                key={`${letter}-${index}`}
                style={{ '--letter-em': `${letterWidth}em`, '--letter-index': index }}
              >
                {letter}
              </span>
            )
          })}
        </span>
      </span>
    </h1>
  )
}

function HomePage() {
  const auth = useAuth()
  const navigate = useNavigate()
  const [history, setHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [introComplete, setIntroComplete] = useState(() => homeIntroHasPlayed)
  const homeScrollRef = useRef(null)
  const handleIntroComplete = useCallback(() => setIntroComplete(true), [])

  useEffect(() => {
    if (!auth.isAuthenticated) {
      setHistory([])
      return
    }

    let alive = true
    setHistoryLoading(true)
    api
      .get('/interview/history')
      .then(({ data }) => {
        if (alive) setHistory(Array.isArray(data) ? data : [])
      })
      .catch(() => {
        if (alive) setHistory([])
      })
      .finally(() => {
        if (alive) setHistoryLoading(false)
      })

    return () => {
      alive = false
    }
  }, [auth.isAuthenticated])

  useEffect(() => {
    if (!auth.isAuthenticated || !history.some(isHistoryGenerating)) return undefined

    const timerId = window.setInterval(() => {
      api
        .get('/interview/history')
        .then(({ data }) => setHistory(Array.isArray(data) ? data : []))
        .catch(() => {})
    }, EVALUATION_POLL_INTERVAL_MS)

    return () => window.clearInterval(timerId)
  }, [auth.isAuthenticated, history])

  const latest = history[0]
  const completedHistory = history.filter(isHistoryCompleted)
  const averageScore = completedHistory.length
    ? (completedHistory.reduce((sum, item) => sum + Number(item.total_score || 0), 0) / completedHistory.length).toFixed(1)
    : '暂无'
  const recentRoles = Array.from(new Set(history.map((item) => item.role))).slice(0, 3)

  useEffect(() => {
    const element = homeScrollRef.current
    if (!element) return undefined
    let locked = false
    const onWheel = (event) => {
      if (Math.abs(event.deltaY) < 28) return
      event.preventDefault()
      if (locked) return
      const pageHeight = element.clientHeight || 1
      const currentPage = Math.round(element.scrollTop / pageHeight)
      const nextPage = Math.max(0, Math.min(1, currentPage + (event.deltaY > 0 ? 1 : -1)))
      if (nextPage === currentPage) return
      locked = true
      element.scrollTo({ top: nextPage * pageHeight, behavior: 'smooth' })
      window.setTimeout(() => {
        locked = false
      }, 760)
    }
    element.addEventListener('wheel', onWheel, { passive: false })
    return () => element.removeEventListener('wheel', onWheel)
  }, [])

  return (
    <div className="page enter-page home-page" ref={homeScrollRef}>
      <section className={`home-snap-section home-landing ${introComplete ? 'intro-complete' : 'intro-running'}`}>
        <div className="home-title-stage">
          <HomeIntroTitle onIntroComplete={handleIntroComplete} />
        </div>

        <div className="home-landing-reveal" aria-hidden={!introComplete}>
          <p className="home-landing-slogan">拥抱AI，拥抱未来</p>

          <div className="home-action-panel">
            <button className="button primary" onClick={() => navigate(auth.isAuthenticated ? '/dashboard' : '/login')}>
              <Play size={17} />
              {auth.isAuthenticated ? '开始一场面试' : '登录 / 注册'}
            </button>
            {auth.isAuthenticated && (
              <button className="button ghost" onClick={() => navigate('/profile')}>
                <History size={17} />
                查看全部记录
              </button>
            )}
          </div>
        </div>
      </section>

      <section className="home-snap-section home-workbench-section">
      <div className="workbench-grid">
        <section className="panel next-panel">
          <div className="panel-head">
            <div>
              <h2>下一步</h2>
            </div>
          </div>

          {auth.isAuthenticated ? (
            latest ? (
              <div className="latest-report-card">
                <div className="latest-score">
                  <span>{isHistoryCompleted(latest) ? '最近得分' : '报告状态'}</span>
                  <b>
                    {isHistoryCompleted(latest)
                      ? Number(latest.total_score || 0).toFixed(1)
                      : isHistoryFailed(latest)
                        ? '失败'
                        : '生成中'}
                  </b>
                </div>
                <div className="latest-copy">
                  <h3>{latest.role}</h3>
                  <p>{formatDateTime(latest.created_at)} · {latest.difficulty || '中等'}</p>
                  <div className="latest-actions">
                    {isHistoryCompleted(latest) ? (
                      <button className="button primary small" onClick={() => navigate(`/report/${latest.id}`)}>
                        看报告
                      </button>
                    ) : (
                      <button className="button primary small" disabled>
                        {isHistoryFailed(latest) ? '生成失败' : '生成中'}
                      </button>
                    )}
                    <button className="button ghost small" onClick={() => navigate('/dashboard')}>
                      再练一次
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="plain-empty">
                <h3>还没有完成过面试</h3>
                <p>先选一个岗位，完成后这里会显示最近报告。</p>
                <button className="button primary small" onClick={() => navigate('/dashboard')}>去选择岗位</button>
              </div>
            )
          ) : (
            <div className="plain-empty">
              <h3>记录会保存在你的账号下</h3>
            </div>
          )}
        </section>

        <section className="panel home-history-panel">
          <div className="panel-head">
            <div>
              <h2>最近记录</h2>
            </div>
          </div>

          {auth.isAuthenticated && historyLoading && <EmptyState text="正在读取历史记录" loading compact />}
          {auth.isAuthenticated && !historyLoading && history.length > 0 && (
            <div className="recent-report-list">
              {history.slice(0, 4).map((item) => {
                const completed = isHistoryCompleted(item)
                return (
                  <button
                    className="recent-report-row"
                    key={item.id}
                    disabled={!completed}
                    onClick={() => completed && navigate(`/report/${item.id}`)}
                  >
                    <span className="row-main">
                      <b>{item.role}</b>
                      <small>{formatDateTime(item.created_at)}</small>
                    </span>
                    <span className={`difficulty ${difficultyTone(item.difficulty)}`}>{item.difficulty || '中等'}</span>
                    <span className="row-score">
                      {isHistoryGenerating(item) ? '生成中' : isHistoryFailed(item) ? '失败' : Number(item.total_score || 0).toFixed(1)}
                    </span>
                  </button>
                )
              })}
            </div>
          )}
          {auth.isAuthenticated && !historyLoading && history.length === 0 && <EmptyState text="暂无历史记录" compact />}
          {!auth.isAuthenticated && <EmptyState text="暂无登录数据" compact />}
        </section>
      </div>

      {auth.isAuthenticated && (
        <div className="home-facts">
          <MetricPill label="已完成面试" value={String(completedHistory.length)} />
          <MetricPill label="平均分" value={averageScore} />
          <MetricPill label="常练岗位" value={recentRoles.length ? String(recentRoles.length) : '0'} />
        </div>
      )}
      </section>
    </div>
  )
}

function LoginPage() {
  const auth = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ username: '', password: '' })
  const [loading, setLoading] = useState(false)
  const from = location.state?.from || '/dashboard'

  useEffect(() => {
    if (auth.isAuthenticated) navigate(from, { replace: true })
  }, [auth.isAuthenticated, from, navigate])

  const update = (field, value) => setForm((current) => ({ ...current, [field]: value }))

  const submit = async (event) => {
    event.preventDefault()
    if (!form.username.trim() || !form.password.trim()) {
      toast('请输入用户名和密码。', 'warning')
      return
    }
    setLoading(true)
    try {
      if (mode === 'register') {
        await api.post('/auth/register', form)
        toast('注册成功，请使用新账号登录。', 'success')
        setMode('login')
      } else {
        const { data } = await api.post('/auth/login', form)
        auth.login(data.access_token, { username: form.username })
        toast('登录成功。', 'success')
        navigate(from, { replace: true })
      }
    } catch (error) {
      toast(`${mode === 'register' ? '注册' : '登录'}失败：${getErrorMessage(error)}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={submit}>
        <button className="brand" type="button" onClick={() => navigate('/')}>
          <span className="brand-mark">
            <BrandIcon />
          </span>
          <span>
            <span className="brand-name">InterviewEcho</span>
          </span>
        </button>
        <h1>{mode === 'register' ? '创建账号' : '欢迎回来'}</h1>
        <p>{mode === 'register' ? '注册后即可开始结构化模拟面试。' : '登录后进入你的面试大厅。'}</p>
        <div className="form-stack">
          <label>
            用户名
            <input
              autoComplete="username"
              value={form.username}
              placeholder="请输入用户名"
              onChange={(event) => update('username', event.target.value)}
            />
          </label>
          <label>
            密码
            <input
              autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
              type="password"
              value={form.password}
              placeholder="请输入密码"
              onChange={(event) => update('password', event.target.value)}
            />
          </label>
          <button className="button primary full" disabled={loading}>
            {loading ? <LoaderCircle className="spin" size={16} /> : <LogIn size={16} />}
            {mode === 'register' ? '注册' : '登录'}
          </button>
        </div>
        <div className="login-footer">
          <button
            type="button"
            className="inline-link"
            onClick={() => setMode((value) => (value === 'register' ? 'login' : 'register'))}
          >
            {mode === 'register' ? '已有账号，去登录' : '没有账号，创建一个'}
          </button>
        </div>
      </form>
    </div>
  )
}

function DashboardPage() {
  const navigate = useNavigate()
  const toast = useToast()
  const [roles, setRoles] = useState(FALLBACK_ROLES)
  const [loading, setLoading] = useState(true)
  const [selectedRole, setSelectedRole] = useState(null)
  const [sectionCache, setSectionCache] = useState({})
  const sectionCacheRef = useRef({})
  const [starting, setStarting] = useState(false)
  const [startingCopy, setStartingCopy] = useState({
    title: '正在准备面试房间',
    text: '面试官正在读取配置。',
  })

  const writeSectionCache = useCallback((key, entry) => {
    const next = { ...sectionCacheRef.current, [key]: entry }
    sectionCacheRef.current = next
    setSectionCache(next)
  }, [])

  const fetchSectionsForRole = useCallback(
    async (role, { silent = true, retryFailed = false } = {}) => {
      const key = role?.key
      if (!key) return []

      const cached = sectionCacheRef.current[key]
      if (
        cached?.status === 'ready' ||
        cached?.status === 'loading' ||
        (cached?.status === 'failed' && !retryFailed)
      ) {
        return cached.items || []
      }

      writeSectionCache(key, { status: 'loading', items: cached?.items || [] })

      try {
        const { data } = await api.get(`/interview/roles/${key}/sections`)
        const items = Array.isArray(data) ? data : []
        writeSectionCache(key, { status: 'ready', items })
        return items
      } catch {
        writeSectionCache(key, { status: 'failed', items: [] })
        if (!silent) toast('知识点列表暂时不可用，将按完整流程面试。', 'warning')
        return []
      }
    },
    [toast, writeSectionCache],
  )

  useEffect(() => {
    let alive = true
    api
      .get('/interview/roles')
      .then(({ data }) => {
        if (alive && Array.isArray(data) && data.length) setRoles(data)
      })
      .catch(() => {
        toast('岗位列表暂时使用本地兜底数据。', 'warning')
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [toast])

  useEffect(() => {
    if (loading) return
    roles.forEach((role) => fetchSectionsForRole(role, { silent: true }))
  }, [fetchSectionsForRole, loading, roles])

  const openSettings = (role) => {
    setSelectedRole(role)
    fetchSectionsForRole(role, { silent: false, retryFailed: true })
  }

  const handleStart = async (settings) => {
    const hasRepos = (settings.repo_urls || []).length > 0
    setStarting(true)
    setStartingCopy(
      hasRepos
        ? {
            title: '正在整理 GitHub 项目',
            text: '将复用已分析的仓库摘要，并生成项目深挖题。',
          }
        : {
            title: '正在准备面试房间',
            text: '智能面试官正在生成开场与题目节奏。',
          },
    )

    try {
      const { data } = await api.post(
        '/interview/start',
        {
          role: selectedRole.name,
          ...settings,
        },
        { timeout: hasRepos ? 90000 : 30000 },
      )
      navigate(`/interview/${encodeURIComponent(selectedRole.name)}?interviewId=${data.id}`)
    } catch (error) {
      toast(`面试启动失败：${getErrorMessage(error)}`, 'error')
    } finally {
      setStarting(false)
    }
  }

  return (
    <div className="page enter-page dashboard-page">
      {starting && <FullscreenLoader title={startingCopy.title} text={startingCopy.text} />}
      <PageHeader
        eyebrow="面试大厅"
        title="选择目标岗位"
        action={
          <button className="button ghost" onClick={() => navigate('/profile')}>
            <History size={16} />
            历史记录
          </button>
        }
      />

      <div className="role-grid">
        {roles.map((role, index) => (
          <button
            className="role-card"
            key={role.id || role.key || role.name}
            onClick={() => openSettings(role)}
            onFocus={() => fetchSectionsForRole(role, { silent: true })}
            onMouseEnter={() => fetchSectionsForRole(role, { silent: true })}
          >
            <div className="role-icon">{roleIcon(index)}</div>
            <div className="role-card-body">
              <span className="tag">岗位 {String(index + 1).padStart(2, '0')}</span>
              <h3>{role.name}</h3>
              <p>{role.desc || '该岗位题库已连接，适合进行结构化模拟面试。'}</p>
            </div>
            <span className="card-arrow">
              <ChevronRight size={18} />
            </span>
          </button>
        ))}
      </div>

      <StartSettingsModal
        role={selectedRole}
        open={Boolean(selectedRole)}
        sectionState={selectedRole?.key ? sectionCache[selectedRole.key] : null}
        onClose={() => setSelectedRole(null)}
        onConfirm={handleStart}
      />
    </div>
  )
}

function StartSettingsModal({ role, open, sectionState, onClose, onConfirm }) {
  const navigate = useNavigate()
  const [difficulty, setDifficulty] = useState('中等')
  const [rounds, setRounds] = useState(6)
  const [selectedSections, setSelectedSections] = useState([])
  const [repoSlots, setRepoSlots] = useState([{ url: '', analyzing: false, summary: null, error: '' }])
  const [repoExpanded, setRepoExpanded] = useState(false)
  const [profileLibrary, setProfileLibrary] = useState({ profile: null, projects: [] })
  const [profileLoading, setProfileLoading] = useState(false)
  const [selectedSavedProjectIds, setSelectedSavedProjectIds] = useState([])
  const sections = sectionState?.items || []
  const loadingSections = Boolean(open && role?.key && (!sectionState || sectionState.status === 'loading'))

  useEffect(() => {
    if (!open || !role) return
    setDifficulty('中等')
    setRounds(6)
    setSelectedSections([])
    setRepoSlots([{ url: '', analyzing: false, summary: null, error: '' }])
    setRepoExpanded(false)
    setSelectedSavedProjectIds([])
  }, [open, role])

  useEffect(() => {
    if (!open) return undefined
    let alive = true
    setProfileLoading(true)
    api
      .get('/profile')
      .then(({ data }) => {
        if (!alive) return
        setProfileLibrary({
          profile: data?.profile || null,
          projects: Array.isArray(data?.projects) ? data.projects : [],
        })
      })
      .catch(() => {
        if (alive) setProfileLibrary({ profile: null, projects: [] })
      })
      .finally(() => {
        if (alive) setProfileLoading(false)
      })
    return () => {
      alive = false
    }
  }, [open])

  const groupedSections = useMemo(() => groupInterviewSections(sections), [sections])
  const savedProjects = profileLibrary.projects || []
  const profile = profileLibrary.profile || {}
  const hasSavedResume = Boolean((profile.resume_summary || profile.resume_text || '').trim())
  const selectedRepoCount = selectedSavedProjectIds.length + repoSlots.filter((slot) => slot.url.trim() && !slot.error).length
  const selectedSectionText = loadingSections
    ? '正在准备'
    : selectedSections.length
      ? `已选 ${selectedSections.length} 项`
      : '默认完整流程'
  const roundText = selectedRepoCount
    ? `${rounds} 常规轮 + ${selectedRepoCount} 项目轮`
    : `${rounds} 轮 · ${roundsTone(rounds)}`
  const repoRoundHint = selectedRepoCount ? `项目深挖将额外增加 ${selectedRepoCount} 轮，每个项目 1 题。` : ''
  const roundProgress = `${Math.min(100, Math.max(0, ((Number(rounds) - 2) / 8) * 100))}%`

  if (!open || !role) return null

  const toggleSection = (section) => {
    setSelectedSections((current) =>
      current.includes(section) ? current.filter((item) => item !== section) : [...current, section],
    )
  }

  const updateRepoSlot = (index, patch) => {
    setRepoSlots((current) => current.map((slot, idx) => (idx === index ? { ...slot, ...patch } : slot)))
  }

  const toggleSavedProject = (projectId) => {
    setSelectedSavedProjectIds((current) => {
      if (current.includes(projectId)) return current.filter((item) => item !== projectId)
      if (selectedRepoCount >= 3) return current
      return [...current, projectId]
    })
  }

  const analyzeRepo = async (index) => {
    const slot = repoSlots[index]
    if (!slot?.url?.trim()) return
    updateRepoSlot(index, { analyzing: true, error: '', summary: null })
    try {
      const { data } = await api.post('/interview/repo/analyze', { url: slot.url.trim() }, { timeout: 15000 })
      updateRepoSlot(index, { analyzing: false, summary: data })
    } catch (error) {
      updateRepoSlot(index, { analyzing: false, error: getErrorMessage(error) || '仓库分析失败' })
    }
  }

  const submit = () => {
    const selectedRepoSlots = repoSlots.filter((slot) => slot.url.trim() && !slot.error)
    const selectedSavedProjects = savedProjects.filter((project) => selectedSavedProjectIds.includes(project.id))
    const repoEntries = [
      ...selectedSavedProjects.map((project) => ({ url: project.url, summary: project.summary || null })),
      ...selectedRepoSlots.map((slot) => ({ url: slot.url.trim(), summary: slot.summary })),
    ].slice(0, 3)
    const repo_urls = repoEntries.map((entry) => entry.url)
    const repo_summaries = repoEntries.map((entry) => entry.summary).filter(Boolean)

    onConfirm({
      difficulty,
      total_rounds: Number(rounds),
      knowledge_points: selectedSections,
      repo_urls,
      repo_summaries,
    })
    onClose()
  }

  return createPortal(
    <div className="modal-backdrop" role="presentation">
      <div className="modal settings-modal" role="dialog" aria-modal="true" aria-label="配置面试">
        <div className="modal-head">
          <div>
            <span className="modal-kicker">面试设置</span>
            <h2>{role.name} · 模拟面试</h2>
          </div>
          <button className="icon-button" onClick={onClose} title="关闭">
            <X size={18} />
          </button>
        </div>

        <div className="modal-body settings-body">
          <div className="settings-config-row">
            <section className="settings-field">
              <div className="settings-field-head">
                <span>难度</span>
              </div>
              <div className="segmented three settings-difficulty">
                {DIFFICULTIES.map((item) => (
                  <button
                    key={item}
                    className={difficulty === item ? 'active' : ''}
                    onClick={() => setDifficulty(item)}
                  >
                    {item}
                  </button>
                ))}
              </div>
            </section>

            <section className="settings-field">
              <div className="settings-field-head">
                <span>轮次</span>
                <strong>{roundText}</strong>
              </div>
              <input
                className="range"
                type="range"
                min="2"
                max="10"
                value={rounds}
                style={{ '--range-progress': roundProgress }}
                onChange={(event) => setRounds(event.target.value)}
              />
              <div className="range-labels">
                <span>短</span>
                <span>标准</span>
                <span>深</span>
              </div>
              {repoRoundHint && <div className="muted-row">{repoRoundHint}</div>}
            </section>
          </div>

          <section className="settings-field settings-section-field">
            <div className="settings-field-head">
              <span>考察领域</span>
              <strong>{selectedSectionText}</strong>
            </div>
            {loadingSections ? (
              <div className="section-groups is-loading" aria-busy="true" aria-label="正在读取知识点">
                {SECTION_SKELETON_GROUPS.map((group) => (
                  <div className="section-chip-group" key={group.label}>
                    <span className="section-group-label skeleton-label">{group.label}</span>
                    <div className="chip-list">
                      {group.widths.map((width, index) => (
                        <span
                          className="chip skeleton-chip"
                          key={`${group.label}-${index}`}
                          style={{ '--skeleton-width': `${width}px` }}
                        />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : groupedSections.length ? (
              <div className="section-groups">
                {groupedSections.map((group) => (
                  <div className="section-chip-group" key={group.label}>
                    <span className="section-group-label">{group.label}</span>
                    <div className="chip-list">
                      {group.items.map((section) => (
                        <button
                          className={`chip ${selectedSections.includes(section) ? 'active' : ''}`}
                          key={section}
                          onClick={() => toggleSection(section)}
                        >
                          {section}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="muted-row">暂无可选知识点，默认走完整流程。</div>
            )}
          </section>

          <section className="settings-field candidate-field">
            <div className="candidate-field-head">
              <div>
                <span>候选人资料</span>
                <strong>
                  {profileLoading
                    ? '读取中'
                    : hasSavedResume
                      ? '已保存简历'
                      : savedProjects.length
                        ? '已保存项目'
                        : '用户中心未填写'}
                </strong>
              </div>
              <button
                type="button"
                className="button ghost small"
                onClick={() => {
                  onClose()
                  navigate('/account')
                }}
              >
                管理资料
              </button>
            </div>
            <div className="candidate-library">
              {hasSavedResume ? (
                <div className="candidate-resume-snapshot">
                  <FileText size={17} />
                  <p>{profile.resume_summary || '已保存简历文本，面试官会在自我介绍与项目题中自然参考。'}</p>
                </div>
              ) : (
                <div className="muted-row">可在用户中心上传 PDF 或粘贴简历，之后会自动带入面试上下文。</div>
              )}

              {savedProjects.length > 0 && (
                <div className="saved-project-list">
                  {savedProjects.map((project) => {
                    const active = selectedSavedProjectIds.includes(project.id)
                    const disabled = !active && selectedRepoCount >= 3
                    return (
                      <button
                        type="button"
                        className={`saved-project-chip ${active ? 'active' : ''}`}
                        key={project.id}
                        disabled={disabled}
                        onClick={() => toggleSavedProject(project.id)}
                      >
                        <Github size={14} />
                        <span>{project.full_name}</span>
                      </button>
                    )
                  })}
                </div>
              )}
            </div>
          </section>

          <section className={`settings-field github-field ${repoExpanded ? 'expanded' : ''}`}>
            <button
              className="github-toggle"
              type="button"
              aria-expanded={repoExpanded}
              onClick={() => setRepoExpanded((value) => !value)}
            >
              <span className="github-toggle-title">
                <Github size={19} />
                <span>关联 GitHub 项目深挖</span>
                <em>（可选）</em>
              </span>
              <span className="github-toggle-meta">
                {selectedRepoCount ? `已添加 ${selectedRepoCount} 个 · 额外 ${selectedRepoCount} 轮` : '展开添加'}
                <ChevronDown size={18} />
              </span>
            </button>

            {repoExpanded && (
              <div className="repo-list github-repo-panel">
                {repoSlots.map((slot, index) => (
                  <div className="repo-slot" key={index}>
                    <div className="repo-input-line">
                      <Github size={16} />
                      <input
                        value={slot.url}
                        disabled={slot.analyzing || Boolean(slot.summary)}
                        placeholder="https://github.com/owner/repo"
                        onChange={(event) => updateRepoSlot(index, { url: event.target.value, error: '', summary: null })}
                      />
                      {slot.summary ? (
                        <button className="button ghost small" onClick={() => updateRepoSlot(index, { url: '', summary: null })}>
                          移除
                        </button>
                      ) : (
                        <button
                          className="button ghost small"
                          disabled={!slot.url.trim() || slot.analyzing}
                          onClick={() => analyzeRepo(index)}
                        >
                          {slot.analyzing ? <LoaderCircle className="spin" size={15} /> : <Sparkles size={15} />}
                          分析
                        </button>
                      )}
                    </div>
                    {slot.summary && (
                      <div className="repo-summary">
                        <b>{slot.summary.full_name}</b>
                        <span>{slot.summary.main_language || '未知语言'} · 星标 {slot.summary.stars || 0}</span>
                        <p>{slot.summary.description || '无描述'}</p>
                      </div>
                    )}
                    {slot.error && <div className="inline-error">{slot.error}</div>}
                  </div>
                ))}
                {repoSlots.length < 3 && (
                  <button
                    className="add-repo"
                    onClick={() => setRepoSlots((current) => [...current, { url: '', analyzing: false, summary: null, error: '' }])}
                  >
                    <Plus size={15} /> 添加仓库
                  </button>
                )}
              </div>
            )}
          </section>
        </div>

        <div className="modal-actions settings-actions">
          <button className="button ghost" onClick={onClose}>
            取消
          </button>
          <button className="button primary" onClick={submit}>
            <Play size={16} />
            进入面试房间
          </button>
        </div>
      </div>
    </div>,
    document.body,
  )
}

function InterviewRoom() {
  const { role: roleParam } = useParams()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const toast = useToast()
  const role = decodeURIComponent(roleParam || '')
  const [interviewId, setInterviewId] = useState(() => searchParams.get('interviewId'))
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [ending, setEnding] = useState(false)
  const [closingPending, setClosingPending] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [composerMultiline, setComposerMultiline] = useState(false)
  const [focusMode, setFocusMode] = useState(false)
  const [ttsSettings, setTtsSettings] = useState(readStoredTtsSettings)
  const [ttsLoadingId, setTtsLoadingId] = useState(null)
  const [speakingMessageId, setSpeakingMessageId] = useState(null)
  const chatRef = useRef(null)
  const composerInputRef = useRef(null)
  const recorderRef = useRef(null)
  const streamRef = useRef(null)
  const chunksRef = useRef([])
  const audioRef = useRef(null)
  const spokenMessageKeysRef = useRef(new Set())
  const autoEndTimerRef = useRef(null)

  const scrollToBottom = useCallback(() => {
    window.requestAnimationFrame(() => {
      if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight
    })
  }, [])

  const endInterview = useCallback(async () => {
    if (!interviewId || ending) return
    if (autoEndTimerRef.current) {
      window.clearTimeout(autoEndTimerRef.current)
      autoEndTimerRef.current = null
    }
    setClosingPending(false)
    setEnding(true)
    toast('评估报告已进入后台生成。', 'info')
    navigate(`/profile?startEvaluation=${interviewId}`, {
      state: {
        pendingInterview: {
          id: interviewId,
          role,
          status: 'evaluating',
          created_at: new Date().toISOString(),
        },
      },
    })
  }, [ending, interviewId, navigate, role, toast])

  const scheduleAutoEndInterview = useCallback(
    (finalMessage) => {
      if (!interviewId || ending || autoEndTimerRef.current) return
      const readableChars = String(finalMessage?.content || '').replace(/\s/g, '').length
      const delay = Math.min(
        INTERVIEW_AUTO_END_MAX_DELAY_MS,
        Math.max(INTERVIEW_AUTO_END_MIN_DELAY_MS, readableChars * 85),
      )
      setClosingPending(true)
      toast('面试已结束，稍等几秒后为你生成报告。', 'info')
      autoEndTimerRef.current = window.setTimeout(() => {
        autoEndTimerRef.current = null
        endInterview()
      }, delay)
    },
    [endInterview, ending, interviewId, toast],
  )

  useEffect(() => {
    let alive = true
    async function boot() {
      const id = searchParams.get('interviewId')
      if (id) {
        setInterviewId(id)
        try {
          const { data } = await api.get(`/interview/${id}/messages`)
          if (alive) setMessages(Array.isArray(data) ? data : [])
        } catch (error) {
          toast(`加载面试消息失败：${getErrorMessage(error)}`, 'error')
        } finally {
          scrollToBottom()
        }
        return
      }

      try {
        const { data } = await api.post('/interview/start', { role })
        if (!alive) return
        setInterviewId(data.id)
        navigate(`/interview/${encodeURIComponent(role)}?interviewId=${data.id}`, { replace: true })
        const messagesRes = await api.get(`/interview/${data.id}/messages`)
        if (alive) setMessages(messagesRes.data || [])
      } catch (error) {
        toast(`无法启动面试：${getErrorMessage(error)}`, 'error')
        navigate('/dashboard')
      } finally {
        scrollToBottom()
      }
    }
    boot()
    return () => {
      alive = false
      if (autoEndTimerRef.current) {
        window.clearTimeout(autoEndTimerRef.current)
        autoEndTimerRef.current = null
      }
      streamRef.current?.getTracks?.().forEach((track) => track.stop())
    }
  }, [navigate, role, scrollToBottom, searchParams, toast])

  useEffect(scrollToBottom, [messages, sending, closingPending, scrollToBottom])

  useEffect(() => {
    const textarea = composerInputRef.current
    if (!textarea) return
    const maxHeight = 156
    textarea.style.height = 'auto'
    const nextHeight = Math.min(textarea.scrollHeight, maxHeight)
    textarea.style.height = `${Math.max(nextHeight, 38)}px`
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? 'auto' : 'hidden'
    const isMultiline = textarea.scrollHeight > 56
    setComposerMultiline((current) => (current === isMultiline ? current : isMultiline))
  }, [input])

  useEffect(() => {
    try {
      localStorage.setItem(TTS_SETTINGS_STORAGE_KEY, JSON.stringify(ttsSettings))
    } catch {
      // Local storage may be unavailable in strict privacy modes.
    }
  }, [ttsSettings])

  useEffect(
    () => () => {
      audioRef.current?.pause?.()
      audioRef.current = null
    },
    [],
  )

  const updateTtsSetting = (key, value) => {
    setTtsSettings((current) => ({ ...current, [key]: value }))
  }

  const stopInterviewerAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
      audioRef.current = null
    }
    setSpeakingMessageId(null)
  }, [])

  const playInterviewerMessage = useCallback(
    async (message, manual = false) => {
      if (!interviewId || !message?.id || message.sender === 'user' || message.status === 'typing') return
      if (!ttsSettings.autoPlay && !manual) return
      if (speakingMessageId === message.id && audioRef.current) {
        stopInterviewerAudio()
        return
      }

      stopInterviewerAudio()
      setTtsLoadingId(message.id)
      try {
        const { data } = await api.post(`/interview/${interviewId}/messages/${message.id}/tts`, {
          voice: ttsSettings.voice,
          speed: ttsSettings.speed,
          style: ttsSettings.style,
        })
        const nextAudio = new Audio(`data:${data.mime_type || 'audio/wav'};base64,${data.audio_base64}`)
        audioRef.current = nextAudio
        nextAudio.onended = () => {
          if (audioRef.current === nextAudio) audioRef.current = null
          setSpeakingMessageId(null)
        }
        nextAudio.onerror = () => {
          if (audioRef.current === nextAudio) audioRef.current = null
          setSpeakingMessageId(null)
          if (manual) toast('面试官语音播放失败，请稍后重试。', 'warning')
        }
        setSpeakingMessageId(message.id)
        await nextAudio.play()
      } catch (error) {
        audioRef.current?.pause?.()
        audioRef.current = null
        setSpeakingMessageId(null)
        if (manual) toast(`面试官语音生成失败：${getErrorMessage(error)}`, 'error')
      } finally {
        setTtsLoadingId(null)
      }
    },
    [interviewId, speakingMessageId, stopInterviewerAudio, toast, ttsSettings],
  )

  const latestAiMessage = useMemo(
    () => [...messages].reverse().find((message) => message.sender === 'ai' && message.id && message.status !== 'typing'),
    [messages],
  )
  const latestAiSpeechKey = latestAiMessage
    ? `${latestAiMessage.id}:${ttsSettings.voice}:${ttsSettings.speed}:${ttsSettings.style}`
    : ''

  useEffect(() => {
    if (!ttsSettings.autoPlay || !latestAiMessage || !latestAiSpeechKey) return
    if (spokenMessageKeysRef.current.has(latestAiSpeechKey)) return
    spokenMessageKeysRef.current.add(latestAiSpeechKey)
    playInterviewerMessage(latestAiMessage, false)
  }, [latestAiMessage, latestAiSpeechKey, playInterviewerMessage, ttsSettings.autoPlay])

  const updateStreamingMessage = useCallback((streamKey, nextContent) => {
    setMessages((current) =>
      current.map((message) =>
        message._streamKey === streamKey ? { ...message, content: nextContent } : message,
      ),
    )
  }, [])

  const replaceStreamingMessage = useCallback((streamKey, finalMessage) => {
    setMessages((current) =>
      current.map((message) => (message._streamKey === streamKey ? finalMessage : message)),
    )
  }, [])

  const dropStreamingMessage = useCallback((streamKey) => {
    setMessages((current) => current.filter((message) => message._streamKey !== streamKey))
  }, [])

  // Consume the interviewer reply as Server-Sent Events so the answer renders
  // progressively. Returns the final message (with real id) on success.
  // Throws an error with `.fallback = true` when the streaming endpoint is
  // unavailable (e.g. an older backend), so the caller can degrade gracefully.
  const streamAiReply = useCallback(
    async (content, streamKey) => {
      const base = api.defaults.baseURL || '/api'
      const token = localStorage.getItem('token')
      const response = await fetch(`${base}/interview/${interviewId}/message/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ content }),
      })

      if (!response.ok || !response.body) {
        const error = new Error('streaming endpoint unavailable')
        error.fallback = true
        throw error
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let accumulated = ''
      let finalMessage = null
      let isFinal = false
      let streamError = null

      const handleFrame = (frame) => {
        const dataLine = frame
          .split('\n')
          .filter((line) => line.startsWith('data:'))
          .map((line) => line.slice(5).trim())
          .join('')
        if (!dataLine) return
        let event
        try {
          event = JSON.parse(dataLine)
        } catch {
          return
        }
        if (event.type === 'delta') {
          accumulated += event.text || ''
          updateStreamingMessage(streamKey, accumulated)
        } else if (event.type === 'replace') {
          accumulated = event.text || ''
          updateStreamingMessage(streamKey, accumulated)
        } else if (event.type === 'done') {
          finalMessage = event.message || null
          isFinal = Boolean(event.is_final)
        } else if (event.type === 'error') {
          streamError = new Error(event.detail || '生成回复失败')
        }
      }

      for (;;) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        let separatorIndex
        while ((separatorIndex = buffer.indexOf('\n\n')) !== -1) {
          const frame = buffer.slice(0, separatorIndex)
          buffer = buffer.slice(separatorIndex + 2)
          handleFrame(frame)
          if (streamError) break
        }
        if (streamError) break
      }
      if (buffer.trim() && !streamError) handleFrame(buffer)

      if (streamError) throw streamError
      if (!finalMessage) throw new Error('未收到完整的面试官回复')

      replaceStreamingMessage(streamKey, finalMessage)
      return { finalMessage, isFinal: isFinal || Boolean(finalMessage.is_final) }
    },
    [interviewId, replaceStreamingMessage, updateStreamingMessage],
  )

  const sendMessage = async () => {
    if (isRecording) {
      stopRecording()
      return
    }
    const content = input.trim()
    if (!content || sending || ending || closingPending || !interviewId) return
    setMessages((current) => [...current, { sender: 'user', content, created_at: new Date().toISOString() }])
    setInput('')
    setSending(true)

    const streamKey = `stream-${Date.now()}`
    setMessages((current) => [
      ...current,
      { sender: 'ai', content: '', status: 'streaming', _streamKey: streamKey, created_at: new Date().toISOString() },
    ])

    try {
      const { finalMessage, isFinal } = await streamAiReply(content, streamKey)
      if (isFinal) {
        scheduleAutoEndInterview(finalMessage)
      }
    } catch (error) {
      dropStreamingMessage(streamKey)
      if (error?.fallback) {
        // Backend without the streaming endpoint: fall back to the blocking API.
        try {
          const { data } = await api.post(`/interview/${interviewId}/message`, { content })
          setMessages((current) => [...current, data])
          if (data.is_final) {
            scheduleAutoEndInterview(data)
          }
        } catch (fallbackError) {
          toast(`消息发送失败：${getErrorMessage(fallbackError)}`, 'error')
        }
      } else {
        // Stream broke after the answer was persisted server-side: re-sync so we
        // pick up whatever reply the backend managed to save.
        try {
          const { data } = await api.get(`/interview/${interviewId}/messages`)
          if (Array.isArray(data)) setMessages(data)
        } catch {
          // Ignore re-sync failures; the toast below already surfaces the issue.
        }
        toast(`回复生成中断：${getErrorMessage(error)}`, 'error')
      }
    } finally {
      setSending(false)
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      const recorder = new MediaRecorder(stream)
      recorderRef.current = recorder
      chunksRef.current = []
      recorder.ondataavailable = (event) => {
        if (event.data?.size) chunksRef.current.push(event.data)
      }
      recorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        stream.getTracks().forEach((track) => track.stop())
        await uploadVoice(blob)
      }
      recorder.start()
      setIsRecording(true)
      toast('录音已开始。', 'info')
    } catch (error) {
      toast('无法访问麦克风，请检查浏览器权限。', 'error')
    }
  }

  const stopRecording = () => {
    const recorder = recorderRef.current
    if (recorder && recorder.state !== 'inactive') {
      recorder.stop()
      setIsRecording(false)
    }
  }

  const uploadVoice = async (blob) => {
    if (!interviewId) return
    setIsTranscribing(true)
    setSending(true)
    const formData = new FormData()
    formData.append('file', blob, 'voice.webm')
    let userMessageId = null
    try {
      const { data } = await api.post(`/interview/${interviewId}/voice`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 300000,
      })
      const userMessage = data.user_message || { sender: 'user', content: data.transcription, created_at: new Date().toISOString() }
      userMessageId = userMessage.id || null
      setMessages((current) => [...current, userMessage])
      setIsTranscribing(false)
      if (data.ai_message) {
        setMessages((current) => [...current, data.ai_message])
      } else if (userMessageId) {
        let pollFailures = 0
        for (let attempt = 0; attempt < VOICE_REPLY_MAX_POLL_ATTEMPTS; attempt += 1) {
          await wait(VOICE_REPLY_POLL_INTERVAL_MS)
          try {
            const messagesRes = await api.get(`/interview/${interviewId}/messages`)
            pollFailures = 0
            const nextMessages = Array.isArray(messagesRes.data) ? messagesRes.data : []
            setMessages(nextMessages)
            const aiReply = nextMessages.find(
              (message) => message.sender === 'ai' && Number(message.id) > Number(userMessageId),
            )
            if (aiReply) {
              if (aiReply.is_final) {
                scheduleAutoEndInterview(aiReply)
              }
              return
            }
          } catch (pollError) {
            pollFailures += 1
            if (pollFailures >= VOICE_REPLY_MAX_POLL_FAILURES) {
              toast(`语音已转写，但拉取 AI 回复失败：${getErrorMessage(pollError)}`, 'warning')
              return
            }
          }
        }
        toast('语音已转写，AI 回复生成较慢，你可以稍后刷新查看。', 'info')
      }
      if (data.ai_message?.is_final) {
        scheduleAutoEndInterview(data.ai_message)
      }
    } catch (error) {
      toast(`语音处理失败：${getErrorMessage(error)}`, 'error')
    } finally {
      setIsTranscribing(false)
      setSending(false)
    }
  }

  return (
    <div className={`interview-room ${focusMode ? 'focus' : ''}`}>
      {ending && <FullscreenLoader title="正在生成评估报告" text="正在汇总整场对话、表达数据与学习计划。" />}
      <header className="interview-topbar">
        <button className="room-brand" onClick={() => navigate('/dashboard')}>
          <ArrowLeft size={17} />
          <span>{role}</span>
        </button>
        <Timer onDone={endInterview} />
        <div className="top-actions">
          <button className="icon-button" onClick={() => setFocusMode((value) => !value)} title="切换沉浸模式">
            {focusMode ? <Sun size={17} /> : <Moon size={17} />}
          </button>
          <button className="button danger small" onClick={endInterview} disabled={ending || closingPending || !interviewId}>
            结束面试
          </button>
        </div>
      </header>

      <div className="voice-settings-bar" aria-label="面试官声音设置">
        <button
          className={`voice-auto-toggle ${ttsSettings.autoPlay ? 'active' : ''}`}
          onClick={() => updateTtsSetting('autoPlay', !ttsSettings.autoPlay)}
          title={ttsSettings.autoPlay ? '关闭自动朗读' : '开启自动朗读'}
        >
          {ttsSettings.autoPlay ? <Volume2 size={15} /> : <VolumeX size={15} />}
          <span>自动朗读</span>
        </button>
        <div className="voice-select-field">
          <span>音色</span>
          <FilterSelect
            ariaLabel="选择面试官音色"
            value={ttsSettings.voice}
            options={INTERVIEW_TTS_VOICES.map((voice) => ({ value: voice.id, label: voice.label }))}
            onChange={(value) => updateTtsSetting('voice', value)}
          />
        </div>
        <div className="voice-speed-group" aria-label="语速">
          {INTERVIEW_TTS_SPEEDS.map((speed) => (
            <button
              key={speed.id}
              className={ttsSettings.speed === speed.id ? 'active' : ''}
              onClick={() => updateTtsSetting('speed', speed.id)}
              type="button"
            >
              {speed.label}
            </button>
          ))}
        </div>
        <div className="voice-select-field">
          <span>语气</span>
          <FilterSelect
            ariaLabel="选择面试官语气"
            value={ttsSettings.style}
            options={INTERVIEW_TTS_STYLES.map((style) => ({ value: style.id, label: style.label }))}
            onChange={(value) => updateTtsSetting('style', value)}
          />
        </div>
      </div>

      <main className="chat-shell">
        <div className="chat-feed" ref={chatRef}>
          {!messages.length && (
            <div className="empty-chat">
              <LoaderCircle className="spin" size={26} />
              <span>正在连接智能面试官</span>
            </div>
          )}
          {messages.map((message, index) => (
            <ChatBubble
              key={message.id || message._streamKey || `${message.sender}-${index}`}
              message={message}
              onSpeak={playInterviewerMessage}
              speakingMessageId={speakingMessageId}
              ttsLoadingId={ttsLoadingId}
            />
          ))}
          {sending && !messages.some((message) => message.status === 'streaming') && (
            <ChatBubble message={{ sender: 'ai', content: '正在分析你的回答并组织下一轮追问...', status: 'typing' }} />
          )}
          {closingPending && (
            <div className="interview-closing-strip" role="status">
              <LoaderCircle className="spin" size={15} />
              <span>面试已结束，正在整理评估报告。</span>
            </div>
          )}
        </div>

        <div
          className={`composer ${composerMultiline ? 'composer-multiline' : ''} ${isRecording ? 'composer-recording' : ''} ${isTranscribing ? 'composer-transcribing' : ''}`}
        >
          {(isRecording || isTranscribing) && (
            <div className={`recording-strip ${isRecording ? 'recording' : 'transcribing'}`} aria-live="polite">
              {isRecording ? <span className="record-dot" /> : <LoaderCircle className="spin" size={14} />}
              {isRecording ? '正在录音' : '正在转写语音'}
            </div>
          )}
          <textarea
            ref={composerInputRef}
            value={input}
            rows={1}
            disabled={sending || ending || closingPending}
            placeholder={closingPending ? '面试已结束，正在准备评估报告' : '输入你的回答，Enter 发送，Shift + Enter 换行'}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault()
                sendMessage()
              }
            }}
          />
          <div className="composer-actions">
            <button
              className={`mic-button ${isRecording ? 'recording' : ''}`}
              disabled={sending || ending || closingPending}
              onClick={isRecording ? stopRecording : startRecording}
              title={isRecording ? '停止录音' : '开始录音'}
            >
              {isRecording ? <Square size={18} /> : <Mic size={18} />}
            </button>
            <button
              className="send-button"
              disabled={sending || ending || closingPending || (!input.trim() && !isRecording)}
              onClick={sendMessage}
              title="发送"
              aria-label="发送"
            >
              {sending ? <LoaderCircle className="spin" size={18} /> : <ArrowUp size={20} />}
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}

function AccountPage() {
  const navigate = useNavigate()
  const auth = useAuth()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const toast = useToast()
  const pageRef = useRef(null)
  const evaluationStartRef = useRef(null)
  const pendingCreatedAtRef = useRef(new Date().toISOString())
  const pendingInterviewId = searchParams.get('startEvaluation')
  const pendingInterview = location.state?.pendingInterview
  const [history, setHistory] = useState([])
  const [filterRole, setFilterRole] = useState('All')
  const [filterDifficulty, setFilterDifficulty] = useState('All')
  const [historyPage, setHistoryPage] = useState(1)
  const pendingRecord = useMemo(() => {
    if (!pendingInterviewId) return null
    return {
      id: pendingInterviewId,
      role: pendingInterview?.role || '目标岗位',
      difficulty: pendingInterview?.difficulty || '中等',
      total_score: null,
      status: 'evaluating',
      created_at: pendingInterview?.created_at || pendingCreatedAtRef.current,
    }
  }, [pendingInterview, pendingInterviewId])
  const pdfInputRef = useRef(null)
  const [profileData, setProfileData] = useState(null)
  const [profileProjects, setProfileProjects] = useState([])
  const [profileDraft, setProfileDraft] = useState({
    display_name: '',
    headline: '',
    target_role: '',
    resume_text: '',
  })
  const [profileLoading, setProfileLoading] = useState(true)
  const [resumeSaving, setResumeSaving] = useState(false)
  const [pdfUploading, setPdfUploading] = useState(false)
  const [projectUrl, setProjectUrl] = useState('')
  const [projectSaving, setProjectSaving] = useState(false)
  const [resumeEditorOpen, setResumeEditorOpen] = useState(false)
  const [projectInputOpen, setProjectInputOpen] = useState(false)

  const withPendingRecord = useCallback(
    (records) => {
      if (!pendingRecord) return records
      const hasRecord = records.some((item) => String(item.id) === String(pendingRecord.id))
      return hasRecord ? records : [pendingRecord, ...records]
    },
    [pendingRecord],
  )

  const loadHistory = useCallback(
    async ({ includePending = false } = {}) => {
      const { data } = await api.get('/interview/history')
      const records = Array.isArray(data) ? data : []
      setHistory(includePending ? withPendingRecord(records) : records)
      return records
    },
    [withPendingRecord],
  )

  const applyProfileResponse = useCallback((data) => {
    const nextProfile = data?.profile || {}
    const nextProjects = Array.isArray(data?.projects) ? data.projects : []
    setProfileData(nextProfile)
    setProfileProjects(nextProjects)
    setProfileDraft({
      display_name: nextProfile.display_name || '',
      headline: nextProfile.headline || '',
      target_role: nextProfile.target_role || '',
      resume_text: nextProfile.resume_text || '',
    })
  }, [])

  const loadProfile = useCallback(async () => {
    setProfileLoading(true)
    try {
      const { data } = await api.get('/profile')
      applyProfileResponse(data)
    } catch (error) {
      toast(`无法加载用户资料：${getErrorMessage(error)}`, 'error')
    } finally {
      setProfileLoading(false)
    }
  }, [applyProfileResponse, toast])

  useEffect(() => {
    loadHistory({ includePending: Boolean(pendingRecord) })
      .catch((error) => toast(`无法加载历史记录：${getErrorMessage(error)}`, 'error'))
  }, [loadHistory, pendingRecord, toast])

  useEffect(() => {
    loadProfile()
  }, [loadProfile])

  useEffect(() => {
    if (!pendingInterviewId || !pendingRecord || evaluationStartRef.current === pendingInterviewId) return undefined

    let alive = true
    evaluationStartRef.current = pendingInterviewId
    setHistory((current) => withPendingRecord(current))

    async function startEvaluation() {
      try {
        await api.post(`/interview/${pendingInterviewId}/end`, null, { timeout: 30000 })
        if (!alive) return
        await loadHistory({ includePending: true })
        navigate('/profile', { replace: true })
      } catch (error) {
        if (!alive) return
        toast(`提交评估任务失败：${getErrorMessage(error)}`, 'error')
        setHistory((current) =>
          current.map((item) =>
            String(item.id) === String(pendingInterviewId) ? { ...item, status: 'evaluation_failed' } : item,
          ),
        )
      }
    }

    startEvaluation()
    return () => {
      alive = false
    }
  }, [loadHistory, navigate, pendingInterviewId, pendingRecord, toast, withPendingRecord])

  useEffect(() => {
    if (!history.some(isHistoryGenerating)) return undefined

    const timerId = window.setInterval(() => {
      loadHistory().catch(() => {})
    }, EVALUATION_POLL_INTERVAL_MS)

    return () => window.clearInterval(timerId)
  }, [history, loadHistory])

  const availableRoles = useMemo(() => Array.from(new Set(history.map((item) => item.role))), [history])
  const roleFilterOptions = useMemo(
    () => [{ value: 'All', label: '全部岗位' }, ...availableRoles.map((role) => ({ value: role, label: role }))],
    [availableRoles],
  )
  const difficultyFilterOptions = useMemo(
    () => [{ value: 'All', label: '全部难度' }, ...DIFFICULTIES.map((difficulty) => ({ value: difficulty, label: difficulty }))],
    [],
  )
  const filteredHistory = useMemo(
    () =>
      history.filter((item) => {
        const roleMatch = filterRole === 'All' || item.role === filterRole
        const diffMatch = filterDifficulty === 'All' || item.difficulty === filterDifficulty
        return roleMatch && diffMatch
      }),
    [filterDifficulty, filterRole, history],
  )
  const historyTotalPages = Math.max(1, Math.ceil(filteredHistory.length / PROFILE_HISTORY_PAGE_SIZE))
  const visibleHistory = filteredHistory.slice(
    (historyPage - 1) * PROFILE_HISTORY_PAGE_SIZE,
    historyPage * PROFILE_HISTORY_PAGE_SIZE,
  )

  useEffect(() => {
    setHistoryPage(1)
  }, [filterDifficulty, filterRole])

  useEffect(() => {
    setHistoryPage((current) => Math.min(current, historyTotalPages))
  }, [historyTotalPages])

  const averageScore = useMemo(() => {
    const completedHistory = history.filter(isHistoryCompleted)
    if (!completedHistory.length) return '0.0'
    const total = completedHistory.reduce((sum, item) => sum + Number(item.total_score || 0), 0)
    return (total / completedHistory.length).toFixed(1)
  }, [history])
  const topRole = history[0]?.role || '暂无'
  const resumeReady = Boolean((profileData?.resume_summary || profileData?.resume_text || '').trim())
  const profileSummary = profileData?.resume_summary || '保存简历后，面试官会在自我介绍、项目经历和场景题中自然参考。'
  const profileSkills = Array.isArray(profileData?.skills) ? profileData.skills.slice(0, 8) : []
  const profileDisplayName = profileData?.display_name || auth.user?.username || '候选人'

  const updateProfileDraft = (field, value) => {
    setProfileDraft((current) => ({ ...current, [field]: value }))
  }

  const saveResume = async () => {
    const hasAnyProfileInput = Object.values(profileDraft).some((value) => String(value || '').trim())
    if (!hasAnyProfileInput) {
      toast('请先填写资料，或上传 PDF 自动识别。', 'warning')
      return
    }
    setResumeSaving(true)
    try {
      const payload = {
        display_name: profileDraft.display_name,
        headline: profileDraft.headline,
        target_role: profileDraft.target_role,
        use_ai: Boolean(profileDraft.resume_text.trim()),
      }
      if (profileDraft.resume_text.trim()) payload.resume_text = profileDraft.resume_text
      const { data } = await api.put(
        '/profile/resume',
        payload,
        { timeout: 70000 },
      )
      applyProfileResponse(data)
      toast('用户资料已保存。', 'success')
      setResumeEditorOpen(false)
    } catch (error) {
      toast(`保存简历失败：${getErrorMessage(error)}`, 'error')
    } finally {
      setResumeSaving(false)
    }
  }

  const uploadResumePdf = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return
    setPdfUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const { data } = await api.post('/profile/resume/pdf', formData, {
        timeout: 90000,
      })
      applyProfileResponse(data)
      toast('PDF 简历已识别并保存。', 'success')
    } catch (error) {
      toast(`PDF 识别失败：${getErrorMessage(error)}`, 'error')
    } finally {
      setPdfUploading(false)
      if (pdfInputRef.current) pdfInputRef.current.value = ''
    }
  }

  const addProfileProject = async () => {
    if (!projectUrl.trim()) {
      toast('请输入 GitHub 仓库地址。', 'warning')
      return
    }
    setProjectSaving(true)
    try {
      const { data } = await api.post('/profile/projects', { url: projectUrl.trim() }, { timeout: 30000 })
      setProfileProjects((current) => {
        const withoutDuplicate = current.filter((item) => item.id !== data.id && item.full_name !== data.full_name)
        return [data, ...withoutDuplicate]
      })
      setProjectUrl('')
      setProjectInputOpen(false)
      toast('GitHub 项目已保存。', 'success')
    } catch (error) {
      toast(`添加项目失败：${getErrorMessage(error)}`, 'error')
    } finally {
      setProjectSaving(false)
    }
  }

  const deleteProfileProject = async (projectId) => {
    try {
      await api.delete(`/profile/projects/${projectId}`)
      setProfileProjects((current) => current.filter((project) => project.id !== projectId))
      toast('项目已移除。', 'success')
    } catch (error) {
      toast(`移除项目失败：${getErrorMessage(error)}`, 'error')
    }
  }

  return (
    <div className="page enter-page profile-page account-page" ref={pageRef}>
      <PageHeader
        eyebrow="用户中心"
        title="个人资料"
      />

      <div className="profile-summary-band account-summary-band">
        <div className="stats-grid profile-stats-grid">
          <StatCard label="当前用户" value={profileDisplayName} compact plain />
          <StatCard label="简历资料" value={profileLoading ? '读取中' : resumeReady ? '已完善' : '未填写'} compact plain />
          <StatCard label="GitHub 项目" value={profileProjects.length} plain />
          <StatCard label="目标岗位" value={profileData?.target_role || '未设置'} compact plain />
        </div>
      </div>

      <input ref={pdfInputRef} className="sr-only" type="file" accept="application/pdf" onChange={uploadResumePdf} />

      <div className="profile-center-grid account-center-grid">
        <section className="profile-data-panel resume-panel">
          <div className="panel-head">
            <div>
              <h2>简历资料</h2>
            </div>
            <div className="account-card-actions">
              <button className="button ghost small" onClick={() => setResumeEditorOpen((value) => !value)}>
                {resumeEditorOpen ? '收起' : resumeReady ? '编辑' : '手动输入'}
              </button>
              <button className="button ghost small" onClick={() => pdfInputRef.current?.click()} disabled={pdfUploading}>
                {pdfUploading ? '上传中' : '上传 PDF'}
              </button>
            </div>
          </div>

          {resumeEditorOpen ? (
            <div className="resume-editor">
              <div className="profile-form-grid">
                <input
                  value={profileDraft.display_name}
                  placeholder="姓名 / 昵称"
                  onChange={(event) => updateProfileDraft('display_name', event.target.value)}
                />
                <input
                  value={profileDraft.target_role}
                  placeholder="目标岗位"
                  onChange={(event) => updateProfileDraft('target_role', event.target.value)}
                />
              </div>
              <input
                value={profileDraft.headline}
                placeholder="一句话定位，例如：Java 后端方向，关注并发与工程化"
                onChange={(event) => updateProfileDraft('headline', event.target.value)}
              />
              <textarea
                className="resume-textarea"
                value={profileDraft.resume_text}
                placeholder="粘贴简历正文，保存后会自动提取技能、经历和项目摘要。"
                onChange={(event) => updateProfileDraft('resume_text', event.target.value)}
              />
              <div className="account-editor-actions">
                <button className="button ghost" onClick={() => setResumeEditorOpen(false)}>
                  取消
                </button>
                <button className="button primary" onClick={saveResume} disabled={resumeSaving || pdfUploading}>
                  {resumeSaving ? '保存中' : '保存资料'}
                </button>
              </div>
            </div>
          ) : (
            <div className="resume-profile-view">
              <div className="resume-ai-summary">
                <span>AI 摘要</span>
                <p>{profileSummary}</p>
              </div>
              {profileSkills.length > 0 ? (
                <div className="profile-skill-list">
                  {profileSkills.map((skill) => (
                    <span key={skill}>{skill}</span>
                  ))}
                </div>
              ) : (
                <div className="account-empty-note">暂无简历摘要</div>
              )}
            </div>
          )}
        </section>

        <section className="profile-data-panel project-panel">
          <div className="panel-head">
            <div>
              <h2>GitHub 项目库</h2>
            </div>
            <button
              className="button ghost small"
              onClick={() => setProjectInputOpen((value) => !value)}
              disabled={profileProjects.length >= PROFILE_PROJECT_LIMIT && !projectInputOpen}
            >
              {projectInputOpen ? '收起' : '添加项目'}
            </button>
          </div>

          {projectInputOpen && (
            <div className="profile-project-input">
              <input
                value={projectUrl}
                placeholder="https://github.com/owner/repo"
                onChange={(event) => setProjectUrl(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') addProfileProject()
                }}
              />
              <button className="button ghost small" onClick={addProfileProject} disabled={projectSaving || profileProjects.length >= PROFILE_PROJECT_LIMIT}>
                {projectSaving ? '保存中' : '保存'}
              </button>
            </div>
          )}

          <div className="profile-project-list">
            {profileProjects.length ? (
              profileProjects.map((project) => (
                <article className="profile-project-card" key={project.id}>
                  <div>
                    <b>{project.full_name}</b>
                    <span>{project.main_language || '未知语言'} · 星标 {project.stars || 0}</span>
                    <p>{project.description || '暂无描述'}</p>
                  </div>
                  <button className="icon-button" onClick={() => deleteProfileProject(project.id)} title="移除项目">
                    <X size={16} />
                  </button>
                </article>
              ))
            ) : (
              <div className="account-empty-note">暂无 GitHub 项目</div>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}

function ProfilePage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const toast = useToast()
  const pageRef = useRef(null)
  const evaluationStartRef = useRef(null)
  const pendingCreatedAtRef = useRef(new Date().toISOString())
  const pendingInterviewId = searchParams.get('startEvaluation')
  const pendingInterview = location.state?.pendingInterview
  const [history, setHistory] = useState([])
  const [filterRole, setFilterRole] = useState('All')
  const [filterDifficulty, setFilterDifficulty] = useState('All')
  const [historyPage, setHistoryPage] = useState(1)

  const pendingRecord = useMemo(() => {
    if (!pendingInterviewId) return null
    return {
      id: pendingInterviewId,
      role: pendingInterview?.role || '目标岗位',
      difficulty: pendingInterview?.difficulty || '中等',
      total_score: null,
      status: 'evaluating',
      created_at: pendingInterview?.created_at || pendingCreatedAtRef.current,
    }
  }, [pendingInterview, pendingInterviewId])

  const withPendingRecord = useCallback(
    (records) => {
      if (!pendingRecord) return records
      const hasRecord = records.some((item) => String(item.id) === String(pendingRecord.id))
      return hasRecord ? records : [pendingRecord, ...records]
    },
    [pendingRecord],
  )

  const loadHistory = useCallback(
    async ({ includePending = false } = {}) => {
      const { data } = await api.get('/interview/history')
      const records = Array.isArray(data) ? data : []
      setHistory(includePending ? withPendingRecord(records) : records)
      return records
    },
    [withPendingRecord],
  )

  useEffect(() => {
    loadHistory({ includePending: Boolean(pendingRecord) })
      .catch((error) => toast(`无法加载历史记录：${getErrorMessage(error)}`, 'error'))
  }, [loadHistory, pendingRecord, toast])

  useEffect(() => {
    if (!pendingInterviewId || !pendingRecord || evaluationStartRef.current === pendingInterviewId) return undefined
    let alive = true
    evaluationStartRef.current = pendingInterviewId
    setHistory((current) => withPendingRecord(current))

    async function startEvaluation() {
      try {
        await api.post(`/interview/${pendingInterviewId}/end`, null, { timeout: 30000 })
        if (!alive) return
        await loadHistory({ includePending: true })
        navigate('/profile', { replace: true })
      } catch (error) {
        if (!alive) return
        toast(`提交评估任务失败：${getErrorMessage(error)}`, 'error')
        setHistory((current) =>
          current.map((item) =>
            String(item.id) === String(pendingInterviewId) ? { ...item, status: 'evaluation_failed' } : item,
          ),
        )
      }
    }

    startEvaluation()
    return () => {
      alive = false
    }
  }, [loadHistory, navigate, pendingInterviewId, pendingRecord, toast, withPendingRecord])

  useEffect(() => {
    if (!history.some(isHistoryGenerating)) return undefined
    const timerId = window.setInterval(() => {
      loadHistory().catch(() => {})
    }, EVALUATION_POLL_INTERVAL_MS)
    return () => window.clearInterval(timerId)
  }, [history, loadHistory])

  const availableRoles = useMemo(() => Array.from(new Set(history.map((item) => item.role))), [history])
  const roleFilterOptions = useMemo(
    () => [{ value: 'All', label: '全部岗位' }, ...availableRoles.map((role) => ({ value: role, label: role }))],
    [availableRoles],
  )
  const difficultyFilterOptions = useMemo(
    () => [{ value: 'All', label: '全部难度' }, ...DIFFICULTIES.map((difficulty) => ({ value: difficulty, label: difficulty }))],
    [],
  )
  const filteredHistory = useMemo(
    () =>
      history.filter((item) => {
        const roleMatch = filterRole === 'All' || item.role === filterRole
        const diffMatch = filterDifficulty === 'All' || item.difficulty === filterDifficulty
        return roleMatch && diffMatch
      }),
    [filterDifficulty, filterRole, history],
  )
  const historyTotalPages = Math.max(1, Math.ceil(filteredHistory.length / PROFILE_HISTORY_PAGE_SIZE))
  const visibleHistory = filteredHistory.slice(
    (historyPage - 1) * PROFILE_HISTORY_PAGE_SIZE,
    historyPage * PROFILE_HISTORY_PAGE_SIZE,
  )

  useEffect(() => {
    setHistoryPage(1)
  }, [filterDifficulty, filterRole])

  useEffect(() => {
    setHistoryPage((current) => Math.min(current, historyTotalPages))
  }, [historyTotalPages])

  const averageScore = useMemo(() => {
    const completedHistory = history.filter(isHistoryCompleted)
    if (!completedHistory.length) return '0.0'
    const total = completedHistory.reduce((sum, item) => sum + Number(item.total_score || 0), 0)
    return (total / completedHistory.length).toFixed(1)
  }, [history])
  const topRole = history[0]?.role || '暂无'

  useDampedSnapScroll(pageRef)

  return (
    <div className="page enter-page profile-page review-snap-page" ref={pageRef}>
      <section className="review-snap-section profile-snap-overview">
        <PageHeader
          eyebrow="成长记录"
          title="能力历史"
          action={
            <button className="button primary" onClick={() => navigate('/dashboard')}>
              <Play size={16} />
              新面试
            </button>
          }
        />

        <div className="profile-summary-band">
          <div className="stats-grid">
            <StatCard icon={<CalendarClock size={20} />} label="总面试次数" value={history.length} />
            <StatCard icon={<Gauge size={20} />} label="平均综合得分" value={averageScore} />
            <StatCard icon={<Trophy size={20} />} label="最近岗位" value={topRole} compact />
          </div>
        </div>

        <section className="panel chart-panel">
          <div className="panel-head">
            <div>
              <h2>近期成长曲线</h2>
            </div>
            <div className="filter-row">
              <FilterSelect ariaLabel="筛选岗位" value={filterRole} options={roleFilterOptions} onChange={setFilterRole} />
              <FilterSelect ariaLabel="筛选难度" value={filterDifficulty} options={difficultyFilterOptions} onChange={setFilterDifficulty} />
            </div>
          </div>
          {history.some(isHistoryCompleted) ? (
            <HistoryLineChart history={history} filterRole={filterRole} filterDifficulty={filterDifficulty} />
          ) : (
            <EmptyState text={history.length ? '报告生成完成后会更新曲线' : '暂无面试数据'} />
          )}
        </section>
      </section>

      <section className="review-snap-section profile-snap-records">
        <section className="panel history-panel">
          <div className="panel-head">
            <div>
              <h2>面试历史记录</h2>
            </div>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>日期</th>
                  <th>目标岗位</th>
                  <th>难度</th>
                  <th>得分</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {visibleHistory.map((item) => {
                  const generating = isHistoryGenerating(item)
                  const failed = isHistoryFailed(item)
                  return (
                    <tr key={item.id}>
                      <td>{formatDateTime(item.created_at)}</td>
                      <td>{item.role}</td>
                      <td>
                        <span className={`difficulty ${difficultyTone(item.difficulty)}`}>{item.difficulty || '中等'}</span>
                      </td>
                      <td className="score-cell">
                        {generating ? (
                          <span className="history-status">报告生成中</span>
                        ) : failed ? (
                          <span className="history-status error">生成失败</span>
                        ) : (
                          Number(item.total_score || 0).toFixed(1)
                        )}
                      </td>
                      <td className="right">
                        {generating ? (
                          <button className="inline-link pending" disabled>
                            生成中 <LoaderCircle className="spin" size={14} />
                          </button>
                        ) : failed ? (
                          <button className="inline-link pending" disabled>
                            生成失败
                          </button>
                        ) : (
                          <button className="inline-link" onClick={() => navigate(`/report/${item.id}`)}>
                            查看报告 <ChevronRight size={14} />
                          </button>
                        )}
                      </td>
                    </tr>
                  )
                })}
                {!filteredHistory.length && (
                  <tr>
                    <td colSpan="5">
                      <EmptyState text="没有符合筛选条件的记录" compact />
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <CodePagination
            page={historyPage}
            totalPages={historyTotalPages}
            totalCount={filteredHistory.length}
            pageSize={PROFILE_HISTORY_PAGE_SIZE}
            onChange={setHistoryPage}
            compact
          />
        </section>
      </section>
    </div>
  )
}

function ReportPage() {
  const { id } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const pageRef = useRef(null)
  const evaluationStartRef = useRef(null)
  const shouldStartEvaluation = Boolean(location.state?.startEvaluation) || searchParams.get('startEvaluation') === '1'
  const [report, setReport] = useState(location.state?.evaluation || null)
  const [reportStatus, setReportStatus] = useState(location.state?.evaluationStatus || (shouldStartEvaluation ? 'evaluating' : 'loading'))
  const [reportError, setReportError] = useState('')
  const [activeRoundReviewIndex, setActiveRoundReviewIndex] = useState(0)

  useEffect(() => {
    if (report || !id) return undefined
    let alive = true
    let timerId

    const applyEvaluationStatus = (data) => {
      setReportStatus(data.status || 'loading')
      if (data.evaluation) {
        setReport(data.evaluation)
        setReportError('')
        return true
      }

      if (data.status === 'evaluation_failed') {
        setReportError('评估报告生成失败，可以回到面试历史后重新生成。')
        return true
      }

      if (!shouldStartEvaluation && data.status === 'in_progress') {
        setReportError('评估报告尚未开始，请先结束面试后再查看。')
        return true
      }

      setReportError('')
      return false
    }

    const loadStatus = async () => {
      try {
        const { data } = await api.get(`/interview/${id}/evaluation/status`, { timeout: 30000 })
        if (!alive) return

        if (applyEvaluationStatus(data)) return
        timerId = window.setTimeout(loadStatus, EVALUATION_POLL_INTERVAL_MS)
      } catch (error) {
        if (!alive) return
        setReportError(`无法加载评估报告：${getErrorMessage(error)}`)
      }
    }

    const startAndLoadStatus = async () => {
      if (shouldStartEvaluation && evaluationStartRef.current !== id) {
        evaluationStartRef.current = id
        setReportStatus('evaluating')
        setReportError('')
        try {
          const { data } = await api.post(`/interview/${id}/end`, null, { timeout: 30000 })
          if (!alive) return
          if (applyEvaluationStatus(data)) return
        } catch (error) {
          if (!alive) return
          setReportError(`提交评估任务失败：${getErrorMessage(error)}`)
          return
        }
      }

      loadStatus()
    }

    startAndLoadStatus()
    return () => {
      alive = false
      if (timerId) window.clearTimeout(timerId)
    }
  }, [id, report, shouldStartEvaluation])

  const parsedReport = useMemo(() => parseReportData(report), [report])
  const roundReviews = parsedReport.round_reviews || []
  useEffect(() => {
    if (!roundReviews.length && activeRoundReviewIndex !== 0) {
      setActiveRoundReviewIndex(0)
      return
    }
    if (roundReviews.length && activeRoundReviewIndex > roundReviews.length - 1) {
      setActiveRoundReviewIndex(roundReviews.length - 1)
    }
  }, [activeRoundReviewIndex, roundReviews.length])
  useDampedSnapScroll(pageRef)

  if (!report) {
    return (
      <div className="page enter-page report-loading-page">
        <EmptyState text={reportError || evaluationStatusText(reportStatus)} loading={!reportError} />
      </div>
    )
  }

  const abilityStats = {
    technical_depth: report.content_score,
    communication: report.expression_score,
    business_scenario: report.business_scenario_score,
    problem_solving: report.problem_solving_score,
  }

  const expressionMetrics = report.expression_metrics
  const resumeMatch = report.resume_match || parsedReport.resume_match || null
  const expressionSummary = expressionMetrics?.metrics_summary || {}
  const expressionFeedback = expressionMetrics?.feedback || {}
  const expressionCards = [
    {
      label: '语速节奏',
      value: report.speech_rate_score || 0,
      detail: expressionSummary.avg_wpm ? `${Math.round(expressionSummary.avg_wpm)} 字/分钟` : '暂无语速样本',
      text: expressionFeedback.speech_rate,
    },
    {
      label: '逻辑清晰度',
      value: report.clarity_score || 0,
      detail: expressionSummary.avg_pause_ratio != null ? `停顿占比 ${Math.round(expressionSummary.avg_pause_ratio * 100)}%` : '暂无停顿样本',
      text: expressionFeedback.clarity,
    },
    {
      label: '专业自信度',
      value: report.confidence_score || 0,
      detail: expressionSummary.pitch_stability != null ? `稳定指数 ${Number(expressionSummary.pitch_stability || 0).toFixed(2)}` : '暂无声学样本',
      text: expressionFeedback.confidence,
    },
  ]
  const repoContext = Array.isArray(report.repo_context) ? report.repo_context.slice(0, 3) : []
  const repoSlots = Array.from({ length: 3 }, (_, index) => repoContext[index] || null)

  const customQuestionsForRepo = (repo) => {
    if (!report.custom_questions || !repo?.full_name) return []
    return report.custom_questions.filter((question) => question.repo === repo.full_name)
  }

  return (
    <div className="page enter-page report-page review-snap-page" ref={pageRef}>
      <section className="review-snap-section report-snap-overview">
        <PageHeader
          eyebrow="评估报告"
          title="面试评估报告"
          subtitle={`${report.role || '目标岗位'} · ${formatDateTime(report.created_at)} · 综合得分 ${Number(report.total_score || 0).toFixed(1)}`}
          action={
            <div className="action-row">
              <button className="button ghost" onClick={() => window.print()}>
                <Download size={16} />
                导出 PDF
              </button>
              <button className="button primary" onClick={() => navigate('/profile')}>
                <History size={16} />
                返回历史
              </button>
            </div>
          }
        />

        <div className="report-score-strip">
          <div className="report-total-score">
            <span>综合得分</span>
            <b>{Number(report.total_score || 0).toFixed(1)}</b>
          </div>
          <div className="report-score-metrics">
            <span>
              技术深度 <b>{Number(report.content_score || 0).toFixed(1)}</b>
            </span>
            <span>
              沟通表达 <b>{Number(report.expression_score || 0).toFixed(1)}</b>
            </span>
            <span>
              场景理解 <b>{Number(report.business_scenario_score || 0).toFixed(1)}</b>
            </span>
            <span>
              问题解决 <b>{Number(report.problem_solving_score || 0).toFixed(1)}</b>
            </span>
          </div>
        </div>

        <div className="report-grid report-overview-grid">
          <section className="panel">
            <div className="panel-head">
              <div>
                <h2>多维能力图谱</h2>
                <p>基于技术、表达、场景与问题解决维度。</p>
              </div>
            </div>
            <RadarChart stats={abilityStats} />
          </section>

          <section className="panel report-notes">
            <ReportBlock tone="green" title="核心优势" items={parsedReport.highlights} />
            <ReportBlock tone="amber" title="待提升项" items={parsedReport.weaknesses} />
            <div className="note-block neutral">
              <h3>提升建议</h3>
              <p>{report.recommendations || parsedReport.recommendations || '暂无具体建议，请继续保持练习。'}</p>
            </div>
          </section>
        </div>
      </section>

      {roundReviews.length > 0 && (
        <section className="panel report-section round-review-section review-snap-section">
          <div className="panel-head">
            <div>
              <h2>逐轮回答改进建议</h2>
              <p>按题目顺序复盘每次回答的具体改法。</p>
            </div>
          </div>
          <RoundReviewCarousel
            reviews={roundReviews}
            activeIndex={activeRoundReviewIndex}
            onChange={setActiveRoundReviewIndex}
          />
        </section>
      )}

      {resumeMatch?.has_resume && (
        <section className="panel report-section resume-match-section review-snap-section">
          <div className="panel-head">
            <div>
              <h2>简历匹配度</h2>
              <p>基于简历资料、简历深挖题和整场回答交叉验证。</p>
            </div>
          </div>

          <div className="resume-match-layout">
            <article className="resume-match-score">
              <span>匹配度</span>
              <b>{Number(resumeMatch.score || 0).toFixed(1)}</b>
              <p>{resumeMatch.summary || '暂无简历匹配度摘要。'}</p>
            </article>
            <div className="report-grid resume-match-grid">
              <ReportBlock tone="green" title="已验证亮点" items={resumeMatch.verified_strengths || []} />
              <ReportBlock tone="amber" title="风险缺口" items={resumeMatch.consistency_risks || []} />
              <ReportBlock tone="neutral" title="简历修改建议" items={resumeMatch.resume_improvements || []} />
              <ReportBlock tone="neutral" title="关键证据" items={resumeMatch.evidence || []} />
            </div>
          </div>
        </section>
      )}

      {expressionMetrics && (
        <section className="panel report-section expression-section review-snap-section">
          <div className="panel-head">
            <div>
              <h2>表达沟通专项分析</h2>
              <p>来自语音输入时的节奏、清晰度与自信度诊断。</p>
            </div>
          </div>

          <div className="expression-score-row">
            {expressionCards.map((item) => (
              <article className="expression-score-card" key={item.label}>
                <span>{item.label}</span>
                <b>{Number(item.value || 0).toFixed(1)}</b>
                <p>{item.detail}</p>
              </article>
            ))}
          </div>

          <div className="expression-layout">
            <article className="expression-visual-card">
              <div className="mini-section-title">
                <span>能力图谱</span>
                <p>三项语音指标的相对表现。</p>
              </div>
              <RadarChart
                indicators={[
                  { name: '语速节奏', max: 100 },
                  { name: '语义清晰度', max: 100 },
                  { name: '用词自信度', max: 100 },
                ]}
                dataValues={[
                  report.speech_rate_score || 0,
                  report.clarity_score || 0,
                  report.confidence_score || 0,
                ]}
                seriesName="表达能力诊断"
                compact
              />
            </article>

            <article className="expression-visual-card">
              <div className="mini-section-title">
                <span>逐题节奏</span>
                <p>按回答顺序观察语速变化。</p>
              </div>
              <ExpressionLineChart data={expressionMetrics.per_message || []} />
            </article>

            <div className="expression-feedback-grid">
              {expressionCards.map((item) => (
                <FeedbackCard title={item.label} text={item.text} key={item.label} />
              ))}
              <FillerWords data={expressionSummary.top_filler_words || []} />
            </div>
          </div>
        </section>
      )}

      {!report.expression_metrics && (
        <section className="panel report-section expression-section voice-section review-snap-section">
          <div className="panel-head">
            <div>
              <h2>表达沟通专项分析</h2>
              <p>本模块需要至少一段有效语音样本。</p>
            </div>
          </div>
          <div className="voice-empty">
            <div className="voice-empty-mark">
              <AudioLines size={26} />
            </div>
            <div className="voice-empty-copy">
              <h3>暂无有效语音表达数据</h3>
              <p>
                本场报告没有保存到表达分析指标。通常是语音片段短于 3 秒，或转写为空。你最近一次语音“你好”约 2.34 秒，
                已成功转写并参与对话，但未达到表达沟通专项分析的采样门槛。
              </p>
            </div>
            <div className="voice-empty-grid">
              <article>
                <span>当前状态</span>
                <b>已转写，但样本不足</b>
                <p>语音内容参与了对话流程，只是没有进入表达沟通专项评分。</p>
              </article>
              <article>
                <span>采样门槛</span>
                <b>建议超过 3 秒</b>
                <p>完整句子更容易判断语速、清晰度和专业自信度。</p>
              </article>
              <article>
                <span>下一次建议</span>
                <b>用语音回答一段完整说明</b>
                <p>例如先给结论，再补充两到三个技术要点。</p>
              </article>
            </div>
          </div>
        </section>
      )}

      {repoContext.length > 0 && (
        <section className="panel report-section repo-section review-snap-section">
          <div className="panel-head">
            <div>
              <h2>GitHub 项目深挖</h2>
              <p>最多可添加三个仓库，页面会为每个项目保留独立追问区。</p>
            </div>
          </div>
          <div className="repo-slots-grid">
            {repoSlots.map((repo, slotIndex) => {
              const questions = repo ? customQuestionsForRepo(repo).slice(0, 5) : []
              return (
                <article
                  className={`repo-report ${repo ? '' : 'repo-report-placeholder'}`}
                  key={repo?.full_name || `repo-slot-${slotIndex}`}
                >
                  <div className="repo-slot-kicker">项目 {String(slotIndex + 1).padStart(2, '0')}</div>
                  {repo ? (
                    <>
                      <div className="repo-report-head">
                        <div>
                          <a href={repo.url} target="_blank" rel="noreferrer">
                            {repo.full_name}
                          </a>
                          <p>{repo.description || '无项目描述'}</p>
                        </div>
                        <span className="tag accent">{repo.main_language || '未知语言'}</span>
                      </div>
                      <div className="chip-list compact">
                        {(repo.tech_keywords || []).slice(0, 6).map((keyword) => (
                          <span className="chip passive" key={keyword}>
                            {keyword}
                          </span>
                        ))}
                      </div>
                      {questions.length > 0 && (
                        <div className="question-list">
                          {questions.map((question, index) => (
                            <div className="question-item" key={`${repo.full_name}-${index}`}>
                              <span>{index + 1}</span>
                              <p>{question.question}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="repo-placeholder-content">
                      <Github size={28} />
                      <h3>预留项目槽位</h3>
                      <p>在面试设置中继续添加 GitHub 仓库后，这里会展示项目摘要、技术栈与定制追问。</p>
                    </div>
                  )}
                </article>
              )
            })}
          </div>
        </section>
      )}

      {report.study_plan && (
        <section className="panel report-section study-section review-snap-section">
          <div className="panel-head">
            <div>
              <h2>能力提升计划</h2>
              <p>按周组织的复习路径与快速收益项。</p>
            </div>
          </div>
          <StudyPlan plan={report.study_plan} />
        </section>
      )}
    </div>
  )
}

function RoundReviewCarousel({ reviews, activeIndex, onChange }) {
  const touchStartRef = useRef(null)
  const total = reviews.length
  const clampIndex = (index) => Math.min(total - 1, Math.max(0, index))
  const goTo = (index) => {
    if (!total) return
    onChange(clampIndex(index))
  }
  const handleTouchStart = (event) => {
    const touch = event.touches?.[0]
    touchStartRef.current = touch ? { x: touch.clientX, y: touch.clientY } : null
  }
  const handleTouchEnd = (event) => {
    const start = touchStartRef.current
    const touch = event.changedTouches?.[0]
    touchStartRef.current = null
    if (!start || !touch) return
    const dx = touch.clientX - start.x
    const dy = touch.clientY - start.y
    if (Math.abs(dx) < 44 || Math.abs(dx) < Math.abs(dy)) return
    goTo(activeIndex + (dx < 0 ? 1 : -1))
  }

  if (!total) return null

  return (
    <div className="round-review-carousel">
      <div className="round-review-toolbar">
        <div className="round-review-counter">
          <span>{String(activeIndex + 1).padStart(2, '0')}</span>
          <b>/ {String(total).padStart(2, '0')}</b>
        </div>
        <div className="round-review-controls">
          <button
            className="icon-button round-review-nav"
            type="button"
            onClick={() => goTo(activeIndex - 1)}
            disabled={activeIndex <= 0}
            aria-label="上一轮"
            title="上一轮"
          >
            <ChevronLeft size={18} />
          </button>
          <button
            className="icon-button round-review-nav"
            type="button"
            onClick={() => goTo(activeIndex + 1)}
            disabled={activeIndex >= total - 1}
            aria-label="下一轮"
            title="下一轮"
          >
            <ChevronRight size={18} />
          </button>
        </div>
      </div>

      <div className="round-review-viewport" onTouchStart={handleTouchStart} onTouchEnd={handleTouchEnd}>
        <div className="round-review-track" style={{ transform: `translateX(-${activeIndex * 100}%)` }}>
          {reviews.map((review, index) => (
            <RoundReviewCard
              key={`round-review-${review.round || index + 1}-${index}`}
              review={review}
              index={index}
              total={total}
              hidden={index !== activeIndex}
            />
          ))}
        </div>
      </div>

      <div className="round-review-dots" role="tablist" aria-label="逐轮回答">
        {reviews.map((review, index) => (
          <button
            key={`round-review-dot-${review.round || index + 1}-${index}`}
            className={index === activeIndex ? 'active' : ''}
            type="button"
            onClick={() => goTo(index)}
            aria-label={`第 ${index + 1} 轮`}
            aria-selected={index === activeIndex}
          />
        ))}
      </div>
    </div>
  )
}

function RoundReviewCard({ review, index, total, hidden }) {
  const scoreItems = [
    { label: '内容', value: review.content_score },
    { label: '表达', value: review.expression_score },
    { label: '场景', value: review.business_scenario_score },
    { label: '技术', value: review.problem_solving_score },
  ].filter((item) => Number.isFinite(Number(item.value)))

  return (
    <article className="round-review-card" aria-hidden={hidden}>
      <header className="round-review-card-head">
        <div>
          <span>第 {String(review.round || index + 1).padStart(2, '0')} 轮</span>
          <h3>{review.question || '本轮问题未记录。'}</h3>
        </div>
        <div className="round-review-total">
          {String(index + 1).padStart(2, '0')}
          <small>/ {String(total).padStart(2, '0')}</small>
        </div>
      </header>

      {scoreItems.length > 0 && (
        <div className="round-score-pills">
          {scoreItems.map((item) => (
            <span key={item.label}>
              {item.label}
              <b>{Number(item.value || 0).toFixed(0)}</b>
            </span>
          ))}
        </div>
      )}

      <div className="round-review-body">
        <section className="round-answer-summary">
          <span>回答概述</span>
          <p>{review.answer_summary || '本轮没有记录到有效回答。'}</p>
        </section>

        <div className="round-review-columns">
          <RoundReviewList title="做得好的地方" items={review.strengths} />
          <RoundReviewList title="可以改进" items={review.improvements} />
          <RoundReviewList title="建议补充的关键点" items={review.missing_points} />
        </div>

        <section className="round-better-answer">
          <span>更优回答方向</span>
          <p>{review.better_answer || '建议用结论、关键要点、项目例子和边界条件重新组织这轮回答。'}</p>
        </section>
      </div>
    </article>
  )
}

function RoundReviewList({ title, items = [] }) {
  const safeItems = items.length ? items : ['暂无明确记录。']
  return (
    <section className="round-review-block">
      <h4>{title}</h4>
      <ul>
        {safeItems.map((item, index) => (
          <li key={`${title}-${index}`}>{item}</li>
        ))}
      </ul>
    </section>
  )
}

function EChart({ option, className = 'chart' }) {
  const ref = useRef(null)
  const chartRef = useRef(null)

  useEffect(() => {
    if (!ref.current) return undefined
    chartRef.current = echarts.init(ref.current)
    const resize = () => chartRef.current?.resize()
    window.addEventListener('resize', resize)
    return () => {
      window.removeEventListener('resize', resize)
      chartRef.current?.dispose()
      chartRef.current = null
    }
  }, [])

  useEffect(() => {
    if (chartRef.current) chartRef.current.setOption(option, true)
  }, [option])

  return <div ref={ref} className={className} />
}

function RadarChart({ stats, indicators, dataValues, seriesName = '能力评估雷达图', compact = false }) {
  const values = dataValues?.length
    ? dataValues
    : [
        stats?.technical_depth || 0,
        stats?.problem_solving || 0,
        stats?.communication || 0,
        stats?.business_scenario || 0,
        average([
          stats?.technical_depth,
          stats?.problem_solving,
          stats?.communication,
          stats?.business_scenario,
        ]),
      ]

  const finalIndicators =
    indicators || [
      { name: '技术准确性', max: 100 },
      { name: '问题解决', max: 100 },
      { name: '沟通表达', max: 100 },
      { name: '场景理解', max: 100 },
      { name: '综合稳定性', max: 100 },
    ]

  const option = {
    color: ['#000000'],
    tooltip: { trigger: 'item' },
    radar: {
      indicator: finalIndicators,
      shape: 'polygon',
      splitNumber: 5,
      radius: compact ? '58%' : '66%',
      axisName: { color: '#555854', fontSize: 12, fontWeight: 400 },
      splitArea: {
        areaStyle: {
          color: ['rgba(0,0,0,.012)', 'rgba(0,0,0,.026)', 'rgba(0,0,0,.04)'],
        },
      },
      axisLine: { lineStyle: { color: 'rgba(0, 0, 0, .14)' } },
      splitLine: { lineStyle: { color: 'rgba(0, 0, 0, .12)' } },
    },
    series: [
      {
        name: seriesName,
        type: 'radar',
        data: [{ value: values, name: seriesName }],
        symbolSize: 6,
        areaStyle: { color: 'rgba(0, 0, 0, .09)' },
        lineStyle: { width: 2.4, color: '#000000' },
        itemStyle: { color: '#000000', borderColor: '#fffdf7', borderWidth: 2 },
      },
    ],
  }

  return <EChart option={option} className={compact ? 'chart compact' : 'chart radar-chart'} />
}

function HistoryLineChart({ history, filterRole, filterDifficulty }) {
  const filtered = useMemo(
    () =>
      [...history]
        .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
        .filter((item) => {
          const roleMatch = filterRole === 'All' || item.role === filterRole
          const diffMatch = filterDifficulty === 'All' || item.difficulty === filterDifficulty
          return roleMatch && diffMatch && isHistoryCompleted(item)
        }),
    [filterDifficulty, filterRole, history],
  )

  const option = {
    tooltip: { trigger: 'axis' },
    grid: { left: 32, right: 22, top: 28, bottom: 34, containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: filtered.map((item) => formatShortDate(item.created_at)),
      axisLine: { lineStyle: { color: 'rgba(23, 23, 23, .16)' } },
      axisTick: { show: false },
      axisLabel: { color: '#747474' },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      splitLine: { lineStyle: { color: 'rgba(23, 23, 23, .08)', type: 'dashed' } },
      axisLabel: { color: '#747474' },
    },
    series: [
      {
        name: '综合得分',
        type: 'line',
        smooth: true,
        symbolSize: 8,
        data: filtered.map((item) => Number(item.total_score || 0)),
        itemStyle: { color: '#000000', borderColor: '#fffdf7', borderWidth: 2 },
        lineStyle: { width: 3, color: '#000000' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0, 0, 0, .13)' },
            { offset: 1, color: 'rgba(0, 0, 0, 0)' },
          ]),
        },
      },
    ],
  }

  return <EChart option={option} className="chart history-chart" />
}

function ExpressionLineChart({ data = [] }) {
  const option = {
    tooltip: { trigger: 'axis' },
    grid: { left: 24, right: 18, top: 20, bottom: 30, containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.map((_, index) => `第${index + 1}题`),
      axisLine: { lineStyle: { color: 'rgba(23, 23, 23, .16)' } },
      axisLabel: { color: '#747474' },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { type: 'dashed', color: 'rgba(23, 23, 23, .08)' } },
      axisLabel: { color: '#747474' },
    },
    series: [
      {
        name: '语速 WPM',
        type: 'line',
        smooth: true,
        data: data.map((item) => item.wpm || 0),
        itemStyle: { color: '#000000' },
        lineStyle: { width: 3, color: '#000000' },
      },
    ],
  }
  return <EChart option={option} className="chart expression-chart" />
}

function ChatBubble({ message, onSpeak, speakingMessageId, ttsLoadingId }) {
  const isUser = message.sender === 'user'
  const isStreaming = message.status === 'streaming'
  const isTyping = message.status === 'typing'
  const canSpeak = !isUser && message.id && !isStreaming && !isTyping && onSpeak
  const isLoadingVoice = canSpeak && ttsLoadingId === message.id
  const isSpeaking = canSpeak && speakingMessageId === message.id
  // While streaming, show typing dots only until the first characters arrive.
  const showTypingDots = isTyping || (isStreaming && !message.content)
  return (
    <div className={`chat-row ${isUser ? 'user' : 'ai'}`}>
      <div className="speaker-line">
        <div className="speaker">{isUser ? '候选人' : '智能面试官'}</div>
        {canSpeak && (
          <button
            className={`bubble-voice-button ${isSpeaking ? 'speaking' : ''}`}
            onClick={() => onSpeak(message, true)}
            disabled={isLoadingVoice}
            title={isSpeaking ? '停止播放' : '播放面试官声音'}
            type="button"
          >
            {isLoadingVoice ? <LoaderCircle className="spin" size={13} /> : <Volume2 size={13} />}
          </button>
        )}
      </div>
      <div className={`bubble ${showTypingDots ? 'typing' : ''} ${isStreaming && message.content ? 'streaming' : ''}`}>
        {showTypingDots ? (
          <TypingDots />
        ) : (
          <>
            <FormattedMessage content={message.content} />
            {isStreaming && <span className="stream-caret" aria-hidden="true" />}
          </>
        )}
      </div>
    </div>
  )
}

function FormattedMessage({ content = '' }) {
  const blocks = parseMessageBlocks(String(content))
  return (
    <>
      {blocks.map((block, index) => {
        if (block.type === 'code') {
          return (
            <pre className="message-code" key={`code-${index}`}>
              <code>{block.content}</code>
            </pre>
          )
        }
        if (block.type === 'ordered' || block.type === 'unordered') {
          const Tag = block.type === 'ordered' ? 'ol' : 'ul'
          return (
            <Tag className="message-list" key={`list-${index}`}>
              {block.items.map((item, itemIndex) => (
                <li key={`${item}-${itemIndex}`}>{formatInlineMarkdown(item)}</li>
              ))}
            </Tag>
          )
        }
        return (
          <p key={`p-${index}`}>
            {block.lines.map((line, lineIndex) => (
              <React.Fragment key={`${line}-${lineIndex}`}>
                {lineIndex > 0 && <br />}
                {formatInlineMarkdown(line)}
              </React.Fragment>
            ))}
          </p>
        )
      })}
    </>
  )
}

function parseMessageBlocks(content) {
  const lines = content.split('\n')
  const blocks = []
  let index = 0

  while (index < lines.length) {
    const line = lines[index]
    if (!line.trim()) {
      index += 1
      continue
    }

    if (line.trim().startsWith('```')) {
      const codeLines = []
      index += 1
      while (index < lines.length && !lines[index].trim().startsWith('```')) {
        codeLines.push(lines[index])
        index += 1
      }
      index += 1
      blocks.push({ type: 'code', content: codeLines.join('\n') })
      continue
    }

    const orderedMatch = line.match(/^\s*\d+\.\s+(.+)/)
    const unorderedMatch = line.match(/^\s*[-*]\s+(.+)/)
    if (orderedMatch || unorderedMatch) {
      const type = orderedMatch ? 'ordered' : 'unordered'
      const items = []
      while (index < lines.length) {
        const match = lines[index].match(type === 'ordered' ? /^\s*\d+\.\s+(.+)/ : /^\s*[-*]\s+(.+)/)
        if (!match) break
        items.push(match[1])
        index += 1
      }
      blocks.push({ type, items })
      continue
    }

    const paragraphLines = []
    while (index < lines.length && lines[index].trim()) {
      if (lines[index].trim().startsWith('```')) break
      if (/^\s*(\d+\.|[-*])\s+/.test(lines[index])) break
      paragraphLines.push(lines[index])
      index += 1
    }
    blocks.push({ type: 'paragraph', lines: paragraphLines })
  }

  return blocks
}

function formatInlineMarkdown(text) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={`${part}-${index}`}>{part.slice(2, -2)}</strong>
    }
    return part
  })
}

function Timer({ onDone }) {
  const [timeLeft, setTimeLeft] = useState(45 * 60)
  const doneRef = useRef(false)

  useEffect(() => {
    const timer = window.setInterval(() => {
      setTimeLeft((value) => {
        if (value <= 1) {
          window.clearInterval(timer)
          if (!doneRef.current) {
            doneRef.current = true
            onDone?.()
          }
          return 0
        }
        return value - 1
      })
    }, 1000)
    return () => window.clearInterval(timer)
  }, [onDone])

  const minutes = String(Math.floor(timeLeft / 60)).padStart(2, '0')
  const seconds = String(timeLeft % 60).padStart(2, '0')

  return (
    <div className="timer">
      <TimerReset size={15} />
      {minutes}:{seconds}
    </div>
  )
}

function TypingDots() {
  return (
    <span className="typing-dots">
      <span />
      <span />
      <span />
    </span>
  )
}

function CodePracticePage() {
  const navigate = useNavigate()
  const toast = useToast()
  const [problems, setProblems] = useState([])
  const [tags, setTags] = useState([])
  const [submissions, setSubmissions] = useState([])
  const [loading, setLoading] = useState(true)
  const [historyLoading, setHistoryLoading] = useState(true)
  const [keyword, setKeyword] = useState('')
  const [difficulty, setDifficulty] = useState('全部')
  const [tag, setTag] = useState('全部')
  const [problemPage, setProblemPage] = useState(1)
  const [historyPage, setHistoryPage] = useState(1)

  const difficultyOptions = useMemo(
    () => [
      { value: '全部', label: '全部难度' },
      ...DIFFICULTIES.map((item) => ({ value: item, label: item })),
    ],
    [],
  )
  const tagOptions = useMemo(
    () => [{ value: '全部', label: '全部主题' }, ...tags.map((item) => ({ value: item, label: item }))],
    [tags],
  )

  useEffect(() => {
    let alive = true
    const params = {}
    if (difficulty !== '全部') params.difficulty = difficulty
    if (tag !== '全部') params.tag = tag
    if (keyword.trim()) params.q = keyword.trim()
    setLoading(true)
    api
      .get('/code/problems', { params })
      .then(({ data }) => {
        if (!alive) return
        setProblems(data.items || [])
        setTags(data.tags || [])
      })
      .catch((error) => {
        if (alive) toast(getErrorMessage(error), 'error')
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [difficulty, keyword, tag, toast])

  useEffect(() => {
    setProblemPage(1)
  }, [difficulty, keyword, tag])

  useEffect(() => {
    let alive = true
    setHistoryLoading(true)
    api
      .get('/code/submissions')
      .then(({ data }) => {
        if (alive) setSubmissions(Array.isArray(data) ? data : [])
      })
      .catch(() => {
        if (alive) setSubmissions([])
      })
      .finally(() => {
        if (alive) setHistoryLoading(false)
      })
    return () => {
      alive = false
    }
  }, [])

  const solvedCount = problems.filter((item) => item.solved).length
  const judgableCount = problems.filter((item) => item.judgable).length
  const problemTotalPages = Math.max(1, Math.ceil(problems.length / CODE_PAGE_SIZE))
  const visibleProblems = problems.slice((problemPage - 1) * CODE_PAGE_SIZE, problemPage * CODE_PAGE_SIZE)
  const historyTotalPages = Math.max(1, Math.ceil(submissions.length / CODE_PAGE_SIZE))
  const visibleHistory = submissions.slice((historyPage - 1) * CODE_PAGE_SIZE, historyPage * CODE_PAGE_SIZE)

  useEffect(() => {
    setProblemPage((current) => Math.min(current, problemTotalPages))
  }, [problemTotalPages])

  useEffect(() => {
    setHistoryPage((current) => Math.min(current, historyTotalPages))
  }, [historyTotalPages])

  return (
    <div className="page code-page enter-page">
      <PageHeader
        eyebrow="Hot100 ACM"
        title="代码练习"
      />

      <section className="code-hero-strip">
        <div>
          <span>Hot100</span>
          <strong>{problems.length || 100}</strong>
        </div>
        <div>
          <span>Ready</span>
          <strong>{judgableCount}</strong>
        </div>
        <div>
          <span>Accepted</span>
          <strong>{solvedCount}</strong>
        </div>
      </section>

      <section className="code-filter-bar">
        <label className="code-search">
          <Code2 size={18} />
          <input value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="搜索题名或 slug" />
        </label>
        <FilterSelect ariaLabel="筛选代码题难度" value={difficulty} options={difficultyOptions} onChange={setDifficulty} />
        <FilterSelect ariaLabel="筛选代码题标签" value={tag} options={tagOptions} onChange={setTag} />
      </section>

      <div className="code-workspace-grid">
        <section className="code-list-panel">
          <div className="code-section-head">
            <div>
              <h2>题目列表</h2>
            </div>
          </div>

          {loading ? (
            <EmptyState text="正在整理题库" loading />
          ) : problems.length ? (
            <>
              <div className="code-problem-list">
                {visibleProblems.map((problem) => (
                  <button
                    type="button"
                    className={`code-problem-row ${problem.solved ? 'solved' : ''}`}
                    key={problem.id}
                    onClick={() => navigate(`/code/problems/${problem.id}`)}
                  >
                    <span className="code-row-index">{String(problem.id).padStart(2, '0')}</span>
                    <span className="code-row-main">
                      <strong>{problem.title}</strong>
                      <span>
                        {problem.tags.slice(0, 4).map((item) => (
                          <em key={`${problem.id}-${item}`}>{item}</em>
                        ))}
                      </span>
                    </span>
                    <span className={`difficulty-badge ${difficultyTone(problem.difficulty)}`}>{problem.difficulty}</span>
                    <span className={`code-status-pill ${problem.solved ? 'accepted' : problem.judgable ? 'ready' : 'draft'}`}>
                      {problem.solved ? '已通过' : problem.judgable ? '可练习' : '占位'}
                    </span>
                    <ChevronRight size={17} />
                  </button>
                ))}
              </div>
              <CodePagination page={problemPage} totalPages={problemTotalPages} totalCount={problems.length} onChange={setProblemPage} />
            </>
          ) : (
            <EmptyState text="没有匹配的题目" />
          )}
        </section>

        <aside className="code-history-panel">
          <div className="code-section-head compact">
            <div>
              <h2>最近提交</h2>
            </div>
          </div>
          {historyLoading ? (
            <EmptyState text="正在读取提交历史" loading compact />
          ) : submissions.length ? (
            <>
              <div className="code-history-list">
                {visibleHistory.map((item) => (
                  <button
                    type="button"
                    className="code-history-item"
                    key={item.id}
                    onClick={() => navigate(`/code/problems/${item.problem_id}`)}
                  >
                    <span className={`code-status-dot ${statusTone(item.status)}`} />
                    <strong>{item.problem_title || `题目 ${item.problem_id}`}</strong>
                    <span>
                      {languageLabel(item.language)} · {item.passed_count}/{item.total_count} · {formatDateTime(item.created_at)}
                    </span>
                  </button>
                ))}
              </div>
              <CodePagination page={historyPage} totalPages={historyTotalPages} totalCount={submissions.length} onChange={setHistoryPage} compact />
            </>
          ) : (
            <EmptyState text="还没有正式提交" compact />
          )}
        </aside>
      </div>
    </div>
  )
}

function CodeProblemPage() {
  const { problemId } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const [problem, setProblem] = useState(null)
  const [submissions, setSubmissions] = useState([])
  const [language, setLanguage] = useState('python')
  const [sourceCode, setSourceCode] = useState('')
  const [codeByLanguage, setCodeByLanguage] = useState({})
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState(null)
  const [resultMode, setResultMode] = useState('')
  const [submissionPage, setSubmissionPage] = useState(1)
  const languageRef = useRef(language)

  const languageOptions = useMemo(() => CODE_LANGUAGE_OPTIONS, [])
  const editorExtensions = useMemo(() => {
    const languageExtension = CODE_EDITOR_EXTENSIONS[language] || python
    return [languageExtension(), indentUnit.of('    '), keymap.of([indentWithTab]), CODE_EDITOR_THEME]
  }, [language])

  useEffect(() => {
    languageRef.current = language
  }, [language])

  const refreshSubmissions = useCallback(async () => {
    if (!problem?.id) return []
    try {
      const { data } = await api.get('/code/submissions', { params: { problem_id: problem.id } })
      const nextSubmissions = Array.isArray(data) ? data : []
      setSubmissions(nextSubmissions)
      return nextSubmissions
    } catch {
      setSubmissions([])
      return []
    }
  }, [problem?.id])

  useEffect(() => {
    let alive = true
    setLoading(true)
    api
      .get(`/code/problems/${problemId}`)
      .then(({ data }) => {
        if (!alive) return
        const starterCode = data.starter_code || {}
        const preferredLanguage = starterCode[languageRef.current] !== undefined ? languageRef.current : 'python'
        setProblem(data)
        setLanguage(preferredLanguage)
        setCodeByLanguage(starterCode)
        setSourceCode(starterCode[preferredLanguage] || '')
        setResult(null)
        setResultMode('')
      })
      .catch((error) => {
        if (alive) toast(getErrorMessage(error), 'error')
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [problemId, toast])

  useEffect(() => {
    refreshSubmissions()
  }, [refreshSubmissions])

  useEffect(() => {
    setSubmissionPage(1)
  }, [problemId])

  const waitForSubmissionResult = useCallback(async (submissionId) => {
    let latestResult = null
    for (let attempt = 0; attempt < CODE_RESULT_SYNC_ATTEMPTS; attempt += 1) {
      if (attempt > 0) {
        await wait(CODE_RESULT_SYNC_INTERVAL_MS)
      }
      const { data: detail } = await api.get(`/code/submissions/${submissionId}`, { timeout: CODE_JUDGE_TIMEOUT_MS })
      latestResult = toCodeSubmissionResult(detail)
      setResultMode('submit')
      setResult(latestResult)
      if (isCodeFinalStatus(latestResult.status)) {
        return latestResult
      }
    }
    return latestResult
  }, [])

  const syncLatestSubmissionResult = useCallback(
    async (previousLatestId) => {
      if (!problem?.id) return false
      for (let attempt = 0; attempt < CODE_RESULT_SYNC_ATTEMPTS; attempt += 1) {
        if (attempt > 0) {
          await wait(CODE_RESULT_SYNC_INTERVAL_MS)
        }
        try {
          const { data } = await api.get('/code/submissions', {
            params: { problem_id: problem.id },
            timeout: CODE_JUDGE_TIMEOUT_MS,
          })
          const nextSubmissions = Array.isArray(data) ? data : []
          setSubmissions(nextSubmissions)
          const latest = nextSubmissions[0]
          if (!latest || latest.id === previousLatestId) continue

          const syncedResult = await waitForSubmissionResult(latest.id)
          return Boolean(syncedResult)
        } catch {
          // Keep polling; the backend may still be finishing a long Judge0 run.
        }
      }
      return false
    },
    [problem?.id, waitForSubmissionResult],
  )

  const handleSourceCodeChange = useCallback((value) => {
    setSourceCode(value)
    setCodeByLanguage((current) => ({
      ...current,
      [languageRef.current]: value,
    }))
  }, [])

  const handleLanguageChange = (nextLanguage) => {
    if (nextLanguage === language) return
    const nextCodeByLanguage = {
      ...codeByLanguage,
      [language]: sourceCode,
    }
    const nextSourceCode = nextCodeByLanguage[nextLanguage] ?? problem?.starter_code?.[nextLanguage] ?? ''
    languageRef.current = nextLanguage
    setCodeByLanguage({
      ...nextCodeByLanguage,
      [nextLanguage]: nextSourceCode,
    })
    setLanguage(nextLanguage)
    setSourceCode(nextSourceCode)
  }

  const resetStarter = () => {
    const starterCode = problem?.starter_code?.[language] || ''
    setSourceCode(starterCode)
    setCodeByLanguage((current) => ({
      ...current,
      [language]: starterCode,
    }))
    setResult(null)
    setResultMode('')
  }

  const runCode = async () => {
    if (!problem) return
    setRunning(true)
    setResultMode('run')
    setResult(null)
    try {
      const { data } = await api.post(
        `/code/problems/${problem.id}/run`,
        {
          language,
          source_code: sourceCode,
        },
        { timeout: CODE_JUDGE_TIMEOUT_MS },
      )
      setResult(data)
      toast(data.status === 'Accepted' ? '样例已通过' : '样例运行完成', data.status === 'Accepted' ? 'success' : 'warning')
    } catch (error) {
      const message = getErrorMessage(error)
      setResult({
        status: 'Judge Error',
        passed_count: 0,
        total_count: problem.sample_count || 0,
        results: [
          {
            ...CODE_CLIENT_ERROR_RESULT,
            message,
          },
        ],
      })
      toast(message, 'error')
    } finally {
      setRunning(false)
    }
  }

  const submitCode = async () => {
    if (!problem) return
    const previousLatestId = submissions[0]?.id
    setSubmitting(true)
    setResultMode('submit')
    setResult(null)
    try {
      const { data } = await api.post(
        `/code/problems/${problem.id}/submit`,
        {
          language,
          source_code: sourceCode,
        },
        { timeout: CODE_JUDGE_TIMEOUT_MS },
      )
      setResult(data)
      await refreshSubmissions()
      if (CODE_PENDING_STATUSES.has(data.status) && data.submission_id) {
        try {
          const finalResult = await waitForSubmissionResult(data.submission_id)
          await refreshSubmissions()
          if (finalResult && isCodeFinalStatus(finalResult.status)) {
            toast(
              finalResult.status === 'Accepted' ? '提交通过' : `提交结果：${finalResult.status}`,
              finalResult.status === 'Accepted' ? 'success' : 'warning',
            )
          } else {
            toast('判题仍在进行，可稍后在提交历史查看', 'warning')
          }
        } catch {
          await refreshSubmissions()
          toast('提交已进入判题队列，可稍后在提交历史查看', 'warning')
        }
        return
      }
      toast(data.status === 'Accepted' ? '提交通过' : `提交结果：${data.status}`, data.status === 'Accepted' ? 'success' : 'warning')
    } catch (error) {
      const responseStatus = error.response?.status
      const canSyncFromHistory =
        error.code === 'ECONNABORTED' ||
        !error.response ||
        responseStatus === 408 ||
        responseStatus === 499 ||
        responseStatus >= 500
      const synced = canSyncFromHistory ? await syncLatestSubmissionResult(previousLatestId) : false
      if (synced) {
        toast('提交已完成，结果已从历史同步', 'warning')
      } else {
        const message = getErrorMessage(error)
        setResult({
          status: 'Judge Error',
          passed_count: 0,
          total_count: problem.test_count || 0,
          results: [
            {
              ...CODE_CLIENT_ERROR_RESULT,
              message,
            },
          ],
        })
        toast(message, 'error')
        await refreshSubmissions()
      }
    } finally {
      setSubmitting(false)
    }
  }

  const submissionTotalPages = Math.max(1, Math.ceil(submissions.length / CODE_PAGE_SIZE))

  useEffect(() => {
    setSubmissionPage((current) => Math.min(current, submissionTotalPages))
  }, [submissionTotalPages])

  if (loading) {
    return (
      <div className="page code-page enter-page">
        <EmptyState text="正在加载题目" loading />
      </div>
    )
  }

  if (!problem) {
    return (
      <div className="page code-page enter-page">
        <EmptyState text="没有找到这道题" />
      </div>
    )
  }

  const busy = running || submitting
  const visibleSubmissions = submissions.slice((submissionPage - 1) * CODE_PAGE_SIZE, submissionPage * CODE_PAGE_SIZE)

  return (
    <div className="page code-detail-page enter-page">
      <button type="button" className="inline-link code-back-link" onClick={() => navigate('/code')}>
        <ArrowLeft size={16} />
        返回题库
      </button>

      <div className="code-detail-title">
        <div>
          <span className="eyebrow">Hot100 / ACM</span>
          <h1>{problem.title}</h1>
          <p>{problem.description}</p>
        </div>
        <div className="code-title-meta">
          <span className={`difficulty-badge ${difficultyTone(problem.difficulty)}`}>{problem.difficulty}</span>
          <span className={`code-status-pill ${problem.solved ? 'accepted' : problem.judgable ? 'ready' : 'draft'}`}>
            {problem.solved ? '已通过' : problem.judgable ? `${problem.test_count} 组测试` : '暂未开放'}
          </span>
        </div>
      </div>

      <div className="code-detail-grid">
        <article className="code-problem-statement">
          <CodeStatementBlock title="输入格式" text={problem.input_format} />
          <CodeStatementBlock title="输出格式" text={problem.output_format} />
          <section className="code-statement-block">
            <h2>样例</h2>
            <div className="code-sample-list">
              {(problem.samples || []).map((sample, index) => (
                <div className="code-sample" key={`${problem.id}-sample-${index}`}>
                  <span>Sample {index + 1}</span>
                  <pre>{sample.input || '(空输入)'}</pre>
                  <pre>{sample.output || '(空输出)'}</pre>
                  {sample.explanation && <p>{sample.explanation}</p>}
                </div>
              ))}
            </div>
          </section>
          <section className="code-statement-block">
            <h2>约束</h2>
            <ul className="code-constraints">
              {(problem.constraints || []).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
          <section className="code-statement-block">
            <h2>主题</h2>
            <div className="chip-list compact">
              {problem.tags.map((item) => (
                <span className="chip passive" key={item}>
                  {item}
                </span>
              ))}
            </div>
          </section>
        </article>

        <aside className="code-editor-panel">
          <div className="code-editor-toolbar">
            <FilterSelect
              ariaLabel="选择代码语言"
              value={language}
              options={languageOptions}
              onChange={handleLanguageChange}
            />
            <button type="button" className="button ghost small" onClick={resetStarter} disabled={busy}>
              重置模板
            </button>
          </div>
          <CodeMirror
            className="code-editor-shell"
            value={sourceCode}
            minHeight="460px"
            basicSetup={{
              autocompletion: true,
              bracketMatching: true,
              closeBrackets: true,
              drawSelection: false,
              foldGutter: true,
              highlightActiveLine: true,
              highlightSelectionMatches: true,
              lineNumbers: true,
              searchKeymap: true,
            }}
            extensions={editorExtensions}
            onChange={handleSourceCodeChange}
            aria-label="代码编辑器"
          />
          <div className="code-action-row">
            <button type="button" className="button ghost grow" onClick={runCode} disabled={busy || !problem.sample_count}>
              {running ? <LoaderCircle className="spin" size={16} /> : <Play size={16} />}
              {running ? '正在运行样例' : '运行样例'}
            </button>
            <button type="button" className="button primary grow" onClick={submitCode} disabled={busy || !problem.judgable}>
              {submitting ? <LoaderCircle className="spin" size={16} /> : <Trophy size={16} />}
              {submitting ? '正在提交判题' : '正式提交'}
            </button>
          </div>

          <CodeResultPanel result={result} mode={resultMode} loadingText={running ? '正在运行样例' : submitting ? '正在提交判题' : ''} />

          <section className="code-submission-panel">
            <div className="code-section-head compact">
              <div>
                <h2>提交历史</h2>
              </div>
            </div>
            {submissions.length ? (
              <>
                <div className="code-submission-list">
                  {visibleSubmissions.map((item) => (
                    <div className="code-submission-row" key={item.id}>
                      <span className={`code-status-dot ${statusTone(item.status)}`} />
                      <strong>{CODE_STATUS_TEXT[item.status] || item.status}</strong>
                      <span>{languageLabel(item.language)}</span>
                      <span>
                        {item.passed_count}/{item.total_count}
                      </span>
                      <span>{formatDateTime(item.created_at)}</span>
                    </div>
                  ))}
                </div>
                <CodePagination
                  page={submissionPage}
                  totalPages={submissionTotalPages}
                  totalCount={submissions.length}
                  onChange={setSubmissionPage}
                />
              </>
            ) : (
              <EmptyState text="这道题还没有提交记录" compact />
            )}
          </section>
        </aside>
      </div>
    </div>
  )
}

function CodeStatementBlock({ title, text }) {
  return (
    <section className="code-statement-block">
      <h2>{title}</h2>
      <p>{text}</p>
    </section>
  )
}

function CodePagination({ page, totalPages, totalCount, onChange, compact = false, pageSize = CODE_PAGE_SIZE }) {
  if (totalPages <= 1) return null
  const start = (page - 1) * pageSize + 1
  const end = Math.min(totalCount, page * pageSize)
  return (
    <div className={`code-pagination ${compact ? 'compact' : ''}`}>
      <span>
        {start}-{end} / {totalCount}
      </span>
      <div>
        <button type="button" className="button ghost small" onClick={() => onChange(page - 1)} disabled={page <= 1}>
          <ChevronRight size={16} className="flip-x" aria-hidden="true" />
          <span className="sr-only">上一页</span>
        </button>
        <em>
          {page}/{totalPages}
        </em>
        <button type="button" className="button ghost small" onClick={() => onChange(page + 1)} disabled={page >= totalPages}>
          <ChevronRight size={16} aria-hidden="true" />
          <span className="sr-only">下一页</span>
        </button>
      </div>
    </div>
  )
}

function CodeResultPanel({ result, mode, loadingText }) {
  const isLoading = Boolean(loadingText)
  return (
    <section className="code-result-panel" aria-live="polite">
      <div className="code-section-head compact">
        <div>
          <h2>{mode === 'submit' ? '提交结果' : '运行结果'}</h2>
          <p>隐藏用例只显示通过情况与错误摘要。</p>
        </div>
      </div>
      {isLoading ? (
        <EmptyState text={loadingText} loading compact />
      ) : result ? (
        <>
          <div className={`code-result-summary ${statusTone(result.status)}`}>
            <strong>{CODE_STATUS_TEXT[result.status] || result.status}</strong>
            <span>
              {result.passed_count}/{result.total_count} passed
            </span>
          </div>
          <div className="code-case-list">
            {(result.results || []).map((item) => (
              <div className={`code-case ${item.passed ? 'passed' : 'failed'}`} key={`${item.index}-${item.status}`}>
                <div className="code-case-head">
                  <strong>{item.is_sample ? `样例 ${item.index}` : `测试 ${item.index}`}</strong>
                  <span>{item.passed ? '通过' : item.status}</span>
                </div>
                {item.message && <p>{item.message}</p>}
                {item.input !== null && item.input !== undefined && (
                  <pre>
                    <b>输入</b>
                    {item.input || '(空输入)'}
                  </pre>
                )}
                {item.expected_output !== null && item.expected_output !== undefined && (
                  <pre>
                    <b>期望</b>
                    {item.expected_output || '(空输出)'}
                  </pre>
                )}
                {item.actual_output !== null && item.actual_output !== undefined && (
                  <pre>
                    <b>实际</b>
                    {item.actual_output || '(空输出)'}
                  </pre>
                )}
                {(item.stderr || item.compile_output) && (
                  <pre>
                    <b>错误</b>
                    {item.compile_output || item.stderr}
                  </pre>
                )}
              </div>
            ))}
          </div>
        </>
      ) : (
        <EmptyState text="运行或提交后，这里会稳定展示判题结果" compact />
      )}
    </section>
  )
}

function PageHeader({ eyebrow, title, subtitle, action }) {
  return (
    <header className="page-header">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {action && <div className="page-action">{action}</div>}
    </header>
  )
}

function FieldGroup({ label, children }) {
  return (
    <div className="field-group">
      <label>{label}</label>
      {children}
    </div>
  )
}

function FilterSelect({ ariaLabel, value, options, onChange }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)
  const selected = options.find((option) => option.value === value) || options[0]

  useEffect(() => {
    if (!open) return undefined
    const closeOnOutside = (event) => {
      if (ref.current && !ref.current.contains(event.target)) setOpen(false)
    }
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('pointerdown', closeOnOutside)
    document.addEventListener('keydown', closeOnEscape)
    return () => {
      document.removeEventListener('pointerdown', closeOnOutside)
      document.removeEventListener('keydown', closeOnEscape)
    }
  }, [open])

  return (
    <div className={`filter-select ${open ? 'open' : ''}`} ref={ref}>
      <button
        type="button"
        className="filter-select-trigger"
        aria-label={ariaLabel}
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <span>{selected?.label || value}</span>
        <ChevronDown size={16} />
      </button>
      {open && (
        <div className="filter-select-menu" role="listbox" aria-label={ariaLabel}>
          {options.map((option) => (
            <button
              type="button"
              role="option"
              aria-selected={option.value === value}
              className={`filter-select-option ${option.value === value ? 'selected' : ''}`}
              key={option.value}
              onClick={() => {
                onChange(option.value)
                setOpen(false)
              }}
            >
              {option.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function FullscreenLoader({ title, text }) {
  return createPortal(
    <div className="fullscreen-loader">
      <div className="loader-card">
        <div className="loader-ring">
          <LoaderCircle className="spin" size={34} />
        </div>
        <h3>{title}</h3>
        <p>{text}</p>
      </div>
    </div>,
    document.body,
  )
}

function MetricPill({ label, value }) {
  return (
    <span className="metric-pill">
      <b>{value}</b>
      {label}
    </span>
  )
}

function InfoCard({ icon, title, text }) {
  return (
    <article className="info-card">
      <div className="info-icon">{icon}</div>
      <h3>{title}</h3>
      <p>{text}</p>
    </article>
  )
}

function StatCard({ icon, label, value, compact, plain = false }) {
  return (
    <article className={`stat-card ${compact ? 'compact' : ''} ${plain ? 'plain' : ''}`}>
      <div>
        <span>{label}</span>
        <b>{value}</b>
      </div>
      {icon && <div className="stat-icon">{icon}</div>}
    </article>
  )
}

function EmptyState({ text, loading = false, compact = false }) {
  return (
    <div className={`empty-state ${loading ? 'loading' : ''} ${compact ? 'compact' : ''}`}>
      {loading && <LoaderCircle className="spin" size={22} />}
      <span>{text}</span>
    </div>
  )
}

function ReportBlock({ title, items = [], tone }) {
  const safeItems = items?.length ? items : ['暂无明确记录。']
  return (
    <div className={`note-block ${tone}`}>
      <h3>{title}</h3>
      <ul>
        {safeItems.map((item, index) => (
          <li key={`${title}-${index}`}>{item}</li>
        ))}
      </ul>
    </div>
  )
}

function FeedbackCard({ title, text }) {
  return (
    <div className="feedback-card">
      <h3>{title}</h3>
      <p>{text || '暂无专项反馈。'}</p>
    </div>
  )
}

function FillerWords({ data }) {
  return (
    <div className="feedback-card">
      <h3>高频填充词</h3>
      {data.length ? (
        <div className="chip-list compact">
          {data.map((item) => (
            <span className="chip passive" key={item.word}>
              {item.word} x{item.count}
            </span>
          ))}
        </div>
      ) : (
        <p>未检测到明显高频填充词。</p>
      )}
    </div>
  )
}

function StudyPlan({ plan }) {
  const weakAreas = plan.weak_areas || []
  const rawWeeks = Array.isArray(plan.plan) ? plan.plan : []
  const quickWins = plan.quick_wins || []
  const fallbackWeeks = [
    { week: 1, focus: '夯实核心基础', tasks: ['复盘本次薄弱题目并整理关键概念', '补齐一个高频知识点的原理图谱', '完成一次 20 分钟口述练习'] },
    { week: 2, focus: '强化工程实践', tasks: ['阅读一篇官方文档并写 150 字总结', '用小 Demo 验证一个工程化知识点', '整理项目中可量化的技术亮点'] },
    { week: 3, focus: '提升表达结构', tasks: ['准备 STAR 结构项目案例', '录制 3 分钟技术讲解并复盘', '把复杂问题拆成背景、方案、结果三段'] },
    { week: 4, focus: '模拟面试冲刺', tasks: ['完成一轮同岗位限时模拟', '复盘错题并更新答案模板', '总结 5 个可追问的项目细节'] },
  ]
  const weeks = Array.from({ length: 4 }, (_, index) => ({
    ...fallbackWeeks[index],
    ...(rawWeeks[index] || {}),
    week: rawWeeks[index]?.week || index + 1,
  }))
  const formatTask = (item) => {
    if (typeof item === 'string') return item
    if (!item || typeof item !== 'object') return '完成一项针对性练习'
    return [item.title, item.note].filter(Boolean).join('：') || item.type || '完成一项针对性练习'
  }
  const formatWeakArea = (area) => {
    if (typeof area === 'string') return `中 · ${area}`
    if (!area || typeof area !== 'object') return '中 · 待加强领域'
    return `${area.severity || '中'} · ${area.area || area.title || area.diagnosis || '待加强领域'}`
  }
  const weekIcons = [
    <Code2 size={36} />,
    <Settings size={36} />,
    <Gauge size={36} />,
    <MessageCircle size={36} />,
  ]
  const blocks = [
    {
      icon: <BrainCircuit size={36} />,
      kicker: '诊断',
      title: '薄弱领域优先级',
      items: weakAreas.length
        ? weakAreas.slice(0, 3).map(formatWeakArea)
        : ['暂无明显薄弱领域，保持当前练习节奏'],
    },
    {
      icon: <TimerReset size={36} />,
      kicker: '快速收益',
      title: '本周可立即完成',
      items: quickWins.length
        ? quickWins.slice(0, 3).map(formatTask)
        : ['完成一次同岗位限时复盘', '整理 3 个高频追问答案', '用 10 分钟复述本次最弱知识点'],
    },
    ...weeks.map((week, index) => ({
      icon: weekIcons[index] || <FileText size={36} />,
      kicker: `第 ${week.week || index + 1} 周`,
      title: week.focus || `第 ${index + 1} 周训练`,
      items: (week.tasks?.length ? week.tasks : fallbackWeeks[index].tasks).slice(0, 3).map(formatTask),
    })),
  ].slice(0, 6)

  return (
    <div className="study-plan bai-study-plan">
      <div className="study-hero">
        <h3>四周能力提升路线</h3>
      </div>
      <div className="study-feature-grid">
        {blocks.map((block, index) => (
          <article className="study-feature-card" key={`${block.kicker}-${block.title}-${index}`}>
            <div className="study-feature-icon">{block.icon}</div>
            <span className="study-feature-kicker">/ {block.kicker}</span>
            <h4>{block.title}</h4>
            <ul>
              {block.items.map((item, itemIndex) => (
                <li key={itemIndex}>{item}</li>
              ))}
            </ul>
          </article>
        ))}
      </div>
    </div>
  )
}

function roleIcon(index) {
  const icons = [<Code2 size={24} />, <Activity size={24} />, <BrainCircuit size={24} />]
  return icons[index % icons.length]
}

function reportText(value, fallback = '') {
  if (value == null) return fallback
  const text = String(value).trim()
  return text || fallback
}

function reportItems(value, fallback = []) {
  if (!Array.isArray(value)) return fallback
  return value
    .map((item) => {
      if (typeof item === 'string') return item.trim()
      if (item && typeof item === 'object') {
        return Object.values(item)
          .map((part) => String(part || '').trim())
          .filter(Boolean)
          .join(' / ')
      }
      return String(item || '').trim()
    })
    .filter(Boolean)
}

function reportScore(value) {
  if (value == null) return null
  const score = Number(value)
  return Number.isFinite(score) ? score : null
}

function normalizeRoundReviews(value) {
  if (!Array.isArray(value)) return []
  return value
    .map((item, index) => {
      if (!item || typeof item !== 'object') return null
      const round = Number.parseInt(item.round, 10) || index + 1
      const answerSummary = reportText(item.answer_summary || item.summary, '本轮没有记录到有效回答。')
      return {
        round,
        question: reportText(item.question || item.prompt, '本轮问题未记录。'),
        answer_summary: answerSummary,
        strengths: reportItems(item.strengths || item.good_points || item.what_went_well, ['暂无明确记录。']),
        improvements: reportItems(item.improvements || item.areas_to_improve || item.improvement_suggestions, ['暂无明确记录。']),
        missing_points: reportItems(item.missing_points || item.key_points_to_add || item.suggested_points, ['暂无明确记录。']),
        better_answer: reportText(item.better_answer || item.better_answer_direction || item.answer_example, '建议用结论、关键要点、项目例子和边界条件重新组织这轮回答。'),
        content_score: reportScore(item.content_score),
        expression_score: reportScore(item.expression_score),
        business_scenario_score: reportScore(item.business_scenario_score),
        problem_solving_score: reportScore(item.problem_solving_score),
      }
    })
    .filter(Boolean)
}

function parseReportData(report) {
  if (!report) return { highlights: [], weaknesses: [], recommendations: '', round_reviews: [] }
  if (report.report_json) {
    try {
      const data = typeof report.report_json === 'string' ? JSON.parse(report.report_json) : report.report_json
      return {
        highlights: data.highlights || data.strengths || [],
        weaknesses: data.weaknesses || [],
        recommendations: data.recommendations || data.improvement_suggestions || '',
        round_reviews: normalizeRoundReviews(data.round_reviews || report.round_reviews),
        resume_match: data.resume_match,
      }
    } catch {
      return { highlights: [], weaknesses: ['报告数据解析异常。'], recommendations: '', round_reviews: [] }
    }
  }
  return {
    highlights: report.highlights || report.strengths || [],
    weaknesses: report.weaknesses || [],
    recommendations: report.recommendations || report.improvement_suggestions || '',
    round_reviews: normalizeRoundReviews(report.round_reviews),
    resume_match: report.resume_match,
  }
}

function average(values) {
  const nums = values.map(Number).filter((value) => Number.isFinite(value) && value > 0)
  if (!nums.length) return 0
  return nums.reduce((sum, value) => sum + value, 0) / nums.length
}

function getErrorMessage(error) {
  if (error?.code === 'ERR_NETWORK' || error?.message === 'Network Error') {
    return '后端服务暂时无法访问，请刷新页面或稍后重试'
  }
  const detail = error?.response?.data?.detail
  if (Array.isArray(detail)) return detail.map((item) => item.msg || item.message || JSON.stringify(item)).join('；')
  if (typeof detail === 'object' && detail) return JSON.stringify(detail)
  return detail || error?.message || '未知错误'
}

function formatDateTime(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function formatShortDate(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return `${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')}`
}

function difficultyTone(value) {
  if (value === '简单') return 'easy'
  if (value === '困难') return 'hard'
  return 'medium'
}

function languageLabel(value) {
  return CODE_LANGUAGE_OPTIONS.find((item) => item.value === value)?.label || value
}

function statusTone(value) {
  if (value === 'Accepted') return 'accepted'
  if (value === 'Compile Error' || value === 'Runtime Error' || value === 'Time Limit Exceeded' || value === 'Judge Error') return 'error'
  if (value === 'Wrong Answer') return 'wrong'
  return 'ready'
}

function routeName(pathname) {
  if (pathname.startsWith('/dashboard')) return '模拟面试'
  if (pathname.startsWith('/code')) return '代码练习'
  if (pathname.startsWith('/account')) return '用户中心'
  if (pathname.startsWith('/profile')) return '能力历史'
  if (pathname.startsWith('/report')) return '评估报告'
  return '工作台'
}

export default App
