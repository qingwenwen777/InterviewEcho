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
  TrendingUp,
  Trophy,
  UserRound,
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
const EVALUATION_POLL_INTERVAL_MS = 2500

function evaluationStatusText(status) {
  if (status === 'evaluating') return '评估报告正在生成，请稍等片刻。'
  if (status === 'evaluation_failed') return '评估报告生成失败，请稍后重试。'
  if (status === 'completed') return '评估报告已生成，正在加载。'
  return '正在检查评估报告状态。'
}
const BRAND_WORDS = ['Interview', 'Insight', 'Improve', 'Inspire', 'Iterate']

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
          <SideLink to="/profile" label="能力历史" />
        </nav>

        <div className="sidebar-user">
          {auth.isAuthenticated ? (
            <>
              <div className="user-chip">
                <UserRound size={17} />
                <b>{auth.user?.username || '候选人'}</b>
              </div>
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
          location.pathname === '/profile' || location.pathname.startsWith('/report/') ? 'review-main-pane' : ''
        }`}
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

function useSlidingBrandWord(words, options = {}) {
  const stepDelay = options.stepDelay ?? 78
  const expandDelay = options.expandDelay ?? stepDelay
  const collapseDelay = options.collapseDelay ?? stepDelay
  const holdDelay = options.holdDelay ?? 1280
  const iconHoldDelay = options.iconHoldDelay ?? 320
  const [wordIndex, setWordIndex] = useState(0)
  const currentWord = words[wordIndex % words.length] || 'Interview'
  const suffix = currentWord.startsWith('I') ? currentWord.slice(1) : currentWord
  const [visibleCount, setVisibleCount] = useState(suffix.length)
  const [phase, setPhase] = useState('hold')

  useEffect(() => {
    let timeout
    if (phase === 'hold') {
      timeout = window.setTimeout(() => setPhase('collapse'), holdDelay)
    } else if (phase === 'collapse') {
      if (visibleCount > 0) {
        timeout = window.setTimeout(() => {
          setVisibleCount((value) => Math.max(0, value - 1))
        }, collapseDelay)
      } else {
        timeout = window.setTimeout(() => setPhase('icon'), iconHoldDelay)
      }
    } else if (phase === 'icon') {
      timeout = window.setTimeout(() => {
        setWordIndex((index) => (index + 1) % words.length)
        setVisibleCount(0)
        setPhase('expand')
      }, iconHoldDelay)
    } else if (phase === 'expand') {
      if (visibleCount < suffix.length) {
        timeout = window.setTimeout(
          () => setVisibleCount((value) => Math.min(suffix.length, value + 1)),
          expandDelay,
        )
      } else {
        timeout = window.setTimeout(() => setPhase('hold'), 260)
      }
    }

    return () => window.clearTimeout(timeout)
  }, [
    collapseDelay,
    expandDelay,
    holdDelay,
    iconHoldDelay,
    phase,
    suffix.length,
    visibleCount,
    words.length,
  ])

  return {
    word: currentWord,
    suffix,
    letters: Array.from(suffix),
    visibleCount,
    visibleWidthEm: estimateTitleWidth(suffix, visibleCount),
    suffixWidthEm: estimateTitleWidth(suffix),
    phase,
  }
}

function HomePage() {
  const auth = useAuth()
  const navigate = useNavigate()
  const [history, setHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const brandTitle = useSlidingBrandWord(BRAND_WORDS)
  const homeScrollRef = useRef(null)

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

  const latest = history[0]
  const averageScore = history.length
    ? (history.reduce((sum, item) => sum + Number(item.total_score || 0), 0) / history.length).toFixed(1)
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
      <section className="home-snap-section home-landing">
        <div>
          <h1 className="hero-title workbench-title" aria-label={`${brandTitle.word}Echo 面试练习工作台`}>
            <span
              className="hero-brand-line"
              data-phase={brandTitle.phase}
              style={{
                '--suffix-ch': brandTitle.suffix.length,
                '--shown-ch': brandTitle.visibleCount,
                '--shown-em': `${brandTitle.visibleWidthEm}em`,
                '--suffix-em': `${brandTitle.suffixWidthEm}em`,
              }}
              aria-hidden="true"
            >
              <span className="title-i-mark">
                <BrandIcon />
              </span>
              <span className="brand-suffix-window">
                <span className="brand-suffix-word">
                  {brandTitle.letters.map((letter, index) => {
                    const isVisible = index < brandTitle.visibleCount
                    const letterWidth = (TITLE_CHAR_WIDTH[letter.toLowerCase()] ?? 0.5) + 0.06
                    return (
                      <span
                        className={`brand-letter ${isVisible ? 'is-visible' : ''}`}
                        key={`${brandTitle.word}-${letter}-${index}`}
                        style={{ '--letter-em': `${letterWidth}em` }}
                      >
                        {letter}
                      </span>
                    )
                  })}
                </span>
              </span>
              <span className="hero-echo">Echo</span>
            </span>
          </h1>
          <p className="home-landing-slogan">拥抱AI，拥抱未来</p>
        </div>

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
                  <span>最近得分</span>
                  <b>{Number(latest.total_score || 0).toFixed(1)}</b>
                </div>
                <div className="latest-copy">
                  <h3>{latest.role}</h3>
                  <p>{formatDateTime(latest.created_at)} · {latest.difficulty || '中等'}</p>
                  <div className="latest-actions">
                    <button className="button primary small" onClick={() => navigate(`/report/${latest.id}`)}>
                      看报告
                    </button>
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
              {history.slice(0, 4).map((item) => (
                <button className="recent-report-row" key={item.id} onClick={() => navigate(`/report/${item.id}`)}>
                  <span className="row-main">
                    <b>{item.role}</b>
                    <small>{formatDateTime(item.created_at)}</small>
                  </span>
                  <span className={`difficulty ${difficultyTone(item.difficulty)}`}>{item.difficulty || '中等'}</span>
                  <span className="row-score">{Number(item.total_score || 0).toFixed(1)}</span>
                </button>
              ))}
            </div>
          )}
          {auth.isAuthenticated && !historyLoading && history.length === 0 && <EmptyState text="暂无历史记录" compact />}
          {!auth.isAuthenticated && <EmptyState text="暂无登录数据" compact />}
        </section>
      </div>

      {auth.isAuthenticated && (
        <div className="home-facts">
          <MetricPill label="已完成面试" value={String(history.length)} />
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
  const [starting, setStarting] = useState(false)
  const [startingCopy, setStartingCopy] = useState({
    title: '正在准备面试房间',
    text: '面试官正在读取配置。',
  })

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
        subtitle="每个岗位会调用后端题库、知识点与评估链路。"
        action={
          <button className="button ghost" onClick={() => navigate('/profile')}>
            <History size={16} />
            历史记录
          </button>
        }
      />

      <div className="role-grid">
        {roles.map((role, index) => (
          <button className="role-card" key={role.id || role.key || role.name} onClick={() => setSelectedRole(role)}>
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
        {loading && (
          <div className="loading-card">
            <LoaderCircle className="spin" size={22} />
            正在同步岗位列表
          </div>
        )}
      </div>

      <StartSettingsModal
        role={selectedRole}
        open={Boolean(selectedRole)}
        onClose={() => setSelectedRole(null)}
        onConfirm={handleStart}
      />
    </div>
  )
}

function StartSettingsModal({ role, open, onClose, onConfirm }) {
  const toast = useToast()
  const [difficulty, setDifficulty] = useState('中等')
  const [rounds, setRounds] = useState(6)
  const [sections, setSections] = useState([])
  const [selectedSections, setSelectedSections] = useState([])
  const [loadingSections, setLoadingSections] = useState(false)
  const [repoSlots, setRepoSlots] = useState([{ url: '', analyzing: false, summary: null, error: '' }])

  useEffect(() => {
    if (!open || !role?.key) return
    setDifficulty('中等')
    setRounds(6)
    setSelectedSections([])
    setRepoSlots([{ url: '', analyzing: false, summary: null, error: '' }])
    setLoadingSections(true)
    api
      .get(`/interview/roles/${role.key}/sections`)
      .then(({ data }) => setSections(Array.isArray(data) ? data : []))
      .catch(() => {
        setSections([])
        toast('知识点列表暂时不可用，将按完整流程面试。', 'warning')
      })
      .finally(() => setLoadingSections(false))
  }, [open, role?.key, toast])

  if (!open || !role) return null

  const toggleSection = (section) => {
    setSelectedSections((current) =>
      current.includes(section) ? current.filter((item) => item !== section) : [...current, section],
    )
  }

  const updateRepoSlot = (index, patch) => {
    setRepoSlots((current) => current.map((slot, idx) => (idx === index ? { ...slot, ...patch } : slot)))
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
    const repo_urls = selectedRepoSlots.map((slot) => slot.url.trim())
    const repo_summaries = selectedRepoSlots.map((slot) => slot.summary).filter(Boolean)

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
            <h2>开始 {role.name} 面试</h2>
          </div>
          <button className="icon-button" onClick={onClose} title="关闭">
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          <FieldGroup label="难度">
            <div className="segmented three">
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
          </FieldGroup>

          <FieldGroup label={`轮次：${rounds}`}>
            <input
              className="range"
              type="range"
              min="2"
              max="10"
              value={rounds}
              onChange={(event) => setRounds(event.target.value)}
            />
            <div className="range-labels">
              <span>短</span>
              <span>标准</span>
              <span>深</span>
            </div>
          </FieldGroup>

          <FieldGroup label="考察领域">
            {loadingSections ? (
              <div className="muted-row">
                <LoaderCircle className="spin" size={16} /> 正在读取知识点
              </div>
            ) : sections.length ? (
              <div className="chip-list">
                {sections.map((section) => (
                  <button
                    className={`chip ${selectedSections.includes(section) ? 'active' : ''}`}
                    key={section}
                    onClick={() => toggleSection(section)}
                  >
                    {section}
                  </button>
                ))}
              </div>
            ) : (
              <div className="muted-row">暂无可选知识点，默认走完整流程。</div>
            )}
          </FieldGroup>

          <FieldGroup label="GitHub 项目深挖">
            <div className="repo-list">
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
          </FieldGroup>
        </div>

        <div className="modal-actions">
          <button className="button ghost" onClick={onClose}>
            取消
          </button>
          <button className="button primary grow" onClick={submit}>
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
  const [isRecording, setIsRecording] = useState(false)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [focusMode, setFocusMode] = useState(false)
  const chatRef = useRef(null)
  const composerInputRef = useRef(null)
  const recorderRef = useRef(null)
  const streamRef = useRef(null)
  const chunksRef = useRef([])

  const scrollToBottom = useCallback(() => {
    window.requestAnimationFrame(() => {
      if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight
    })
  }, [])

  const endInterview = useCallback(async () => {
    if (!interviewId || ending) return
    setEnding(true)
    toast('评估报告已进入后台生成。', 'info')
    navigate(`/report/${interviewId}?startEvaluation=1`, {
      state: {
        startEvaluation: true,
        evaluationStatus: 'evaluating',
      },
    })
  }, [ending, interviewId, navigate, toast])

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
      streamRef.current?.getTracks?.().forEach((track) => track.stop())
    }
  }, [navigate, role, scrollToBottom, searchParams, toast])

  useEffect(scrollToBottom, [messages, sending, scrollToBottom])

  useEffect(() => {
    const textarea = composerInputRef.current
    if (!textarea) return
    const maxHeight = 156
    textarea.style.height = 'auto'
    const nextHeight = Math.min(textarea.scrollHeight, maxHeight)
    textarea.style.height = `${Math.max(nextHeight, 38)}px`
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? 'auto' : 'hidden'
  }, [input])

  const sendMessage = async () => {
    if (isRecording) {
      stopRecording()
      return
    }
    const content = input.trim()
    if (!content || sending || !interviewId) return
    setMessages((current) => [...current, { sender: 'user', content, created_at: new Date().toISOString() }])
    setInput('')
    setSending(true)
    try {
      const { data } = await api.post(`/interview/${interviewId}/message`, { content })
      setMessages((current) => [...current, data])
      if (data.is_final) {
        toast('已达到建议轮次，准备生成报告。', 'warning')
        window.setTimeout(endInterview, 1200)
      }
    } catch (error) {
      toast(`消息发送失败：${getErrorMessage(error)}`, 'error')
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
    try {
      const { data } = await api.post(`/interview/${interviewId}/voice`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 180000,
      })
      setMessages((current) => [
        ...current,
        { sender: 'user', content: data.transcription, created_at: new Date().toISOString() },
        data.ai_message,
      ])
      if (data.ai_message?.is_final) {
        toast('已达到建议轮次，准备生成报告。', 'warning')
        window.setTimeout(endInterview, 1200)
      }
    } catch (error) {
      toast(`语音处理失败：${getErrorMessage(error)}`, 'error')
    } finally {
      setIsTranscribing(false)
      setSending(false)
    }
  }

  const composerExpanded = input.length > 80 || input.includes('\n')

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
          <button className="button danger small" onClick={endInterview} disabled={ending || !interviewId}>
            结束面试
          </button>
        </div>
      </header>

      <main className="chat-shell">
        <div className="chat-feed" ref={chatRef}>
          {!messages.length && (
            <div className="empty-chat">
              <LoaderCircle className="spin" size={26} />
              <span>正在连接智能面试官</span>
            </div>
          )}
          {messages.map((message, index) => (
            <ChatBubble key={message.id || `${message.sender}-${index}`} message={message} />
          ))}
          {sending && <ChatBubble message={{ sender: 'ai', content: '正在分析你的回答并组织下一轮追问...', status: 'typing' }} />}
        </div>

        <div
          className={`composer ${composerExpanded ? 'composer-expanded' : ''} ${isRecording ? 'composer-recording' : ''} ${isTranscribing ? 'composer-transcribing' : ''}`}
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
            disabled={sending || ending}
            placeholder="输入你的回答，Enter 发送，Shift + Enter 换行"
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
              disabled={sending || ending}
              onClick={isRecording ? stopRecording : startRecording}
              title={isRecording ? '停止录音' : '开始录音'}
            >
              {isRecording ? <Square size={18} /> : <Mic size={18} />}
            </button>
            <button
              className="send-button"
              disabled={sending || ending || (!input.trim() && !isRecording)}
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

function ProfilePage() {
  const navigate = useNavigate()
  const toast = useToast()
  const pageRef = useRef(null)
  const [history, setHistory] = useState([])
  const [filterRole, setFilterRole] = useState('All')
  const [filterDifficulty, setFilterDifficulty] = useState('All')

  useEffect(() => {
    api
      .get('/interview/history')
      .then(({ data }) => setHistory(Array.isArray(data) ? data : []))
      .catch((error) => toast(`无法加载历史记录：${getErrorMessage(error)}`, 'error'))
  }, [toast])

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
  const averageScore = useMemo(() => {
    if (!history.length) return '0.0'
    const total = history.reduce((sum, item) => sum + Number(item.total_score || 0), 0)
    return (total / history.length).toFixed(1)
  }, [history])
  const topRole = history[0]?.role || '暂无'

  useDampedSnapScroll(pageRef)

  return (
    <div className="page enter-page profile-page review-snap-page" ref={pageRef}>
      <section className="review-snap-section profile-snap-overview">
        <PageHeader
          eyebrow="成长记录"
          title="能力历史"
          subtitle="按岗位和难度观察最近表现。"
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
              <p>综合得分会随筛选条件即时更新。</p>
            </div>
            <div className="filter-row">
              <FilterSelect
                ariaLabel="筛选岗位"
                value={filterRole}
                options={roleFilterOptions}
                onChange={setFilterRole}
              />
              <FilterSelect
                ariaLabel="筛选难度"
                value={filterDifficulty}
                options={difficultyFilterOptions}
                onChange={setFilterDifficulty}
              />
            </div>
          </div>
          {history.length ? (
            <HistoryLineChart history={history} filterRole={filterRole} filterDifficulty={filterDifficulty} />
          ) : (
            <EmptyState text="暂无面试数据" />
          )}
        </section>
      </section>

      <section className="review-snap-section profile-snap-records">
        <section className="panel history-panel">
          <div className="panel-head">
            <div>
              <h2>面试历史记录</h2>
              <p>报告页会重新拉取后端评估详情。</p>
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
                {filteredHistory.map((item) => (
                  <tr key={item.id}>
                    <td>{formatDateTime(item.created_at)}</td>
                    <td>{item.role}</td>
                    <td>
                      <span className={`difficulty ${difficultyTone(item.difficulty)}`}>{item.difficulty || '中等'}</span>
                    </td>
                    <td className="score-cell">{Number(item.total_score || 0).toFixed(1)}</td>
                    <td className="right">
                      <button className="inline-link" onClick={() => navigate(`/report/${item.id}`)}>
                        查看报告 <ChevronRight size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
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
  useDampedSnapScroll(pageRef)

  if (!report) {
    return (
      <div className="page enter-page">
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
          return roleMatch && diffMatch
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

function ChatBubble({ message }) {
  const isUser = message.sender === 'user'
  return (
    <div className={`chat-row ${isUser ? 'user' : 'ai'}`}>
      <div className="speaker">{isUser ? '候选人' : '智能面试官'}</div>
      <div className={`bubble ${message.status === 'typing' ? 'typing' : ''}`}>
        {message.status === 'typing' ? <TypingDots /> : <FormattedMessage content={message.content} />}
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

function StatCard({ icon, label, value, compact }) {
  return (
    <article className={`stat-card ${compact ? 'compact' : ''}`}>
      <div>
        <span>{label}</span>
        <b>{value}</b>
      </div>
      <div className="stat-icon">{icon}</div>
    </article>
  )
}

function EmptyState({ text, loading = false, compact = false }) {
  return (
    <div className={`empty-state ${compact ? 'compact' : ''}`}>
      {loading ? <LoaderCircle className="spin" size={22} /> : <Sparkles size={22} />}
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
  const weeks = plan.plan || []
  const quickWins = plan.quick_wins || []
  const blocks = [
    {
      icon: <BrainCircuit size={36} />,
      kicker: '诊断',
      title: '薄弱领域优先级',
      items: weakAreas.length
        ? weakAreas.slice(0, 3).map((area) => `${area.severity || '中'} · ${area.area}`)
        : ['暂无明显薄弱领域，保持当前练习节奏'],
    },
    {
      icon: <Sparkles size={36} />,
      kicker: '快速收益',
      title: '本周可立即完成',
      items: quickWins.length ? quickWins.slice(0, 3) : ['完成一次同岗位限时复盘', '整理 3 个高频追问答案'],
    },
    ...weeks.slice(0, 4).map((week, index) => ({
      icon: index % 2 === 0 ? <CalendarClock size={36} /> : <FileText size={36} />,
      kicker: `第 ${week.week || index + 1} 周`,
      title: week.focus || `第 ${index + 1} 周训练`,
      items: (week.tasks || []).slice(0, 3),
    })),
  ].slice(0, 6)

  return (
    <div className="study-plan bai-study-plan">
      <div className="study-hero">
        <span className="study-hero-icon">
          <Sparkles size={36} />
        </span>
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

function parseReportData(report) {
  if (!report) return { highlights: [], weaknesses: [], recommendations: '' }
  if (report.report_json) {
    try {
      const data = typeof report.report_json === 'string' ? JSON.parse(report.report_json) : report.report_json
      return {
        highlights: data.highlights || data.strengths || [],
        weaknesses: data.weaknesses || [],
        recommendations: data.recommendations || data.improvement_suggestions || '',
      }
    } catch {
      return { highlights: [], weaknesses: ['报告数据解析异常。'], recommendations: '' }
    }
  }
  return {
    highlights: report.highlights || report.strengths || [],
    weaknesses: report.weaknesses || [],
    recommendations: report.recommendations || report.improvement_suggestions || '',
  }
}

function average(values) {
  const nums = values.map(Number).filter((value) => Number.isFinite(value) && value > 0)
  if (!nums.length) return 0
  return nums.reduce((sum, value) => sum + value, 0) / nums.length
}

function getErrorMessage(error) {
  if (error?.code === 'ERR_NETWORK' || error?.message === 'Network Error') {
    return '后端服务未启动或无法访问，请先确认 http://localhost:8000 正常运行'
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

function routeName(pathname) {
  if (pathname.startsWith('/dashboard')) return '模拟面试'
  if (pathname.startsWith('/profile')) return '能力历史'
  if (pathname.startsWith('/report')) return '评估报告'
  return '工作台'
}

export default App
