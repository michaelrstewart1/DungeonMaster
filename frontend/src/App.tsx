import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { useState, useEffect, Component, type ReactNode } from 'react'
import { Home } from './pages/Home'
import { CampaignDetail } from './pages/CampaignDetail'
import { GameSession } from './pages/GameSession'
import { NotFound } from './pages/NotFound'
import { Footer } from './components/Footer'
import { ToastProvider } from './components/Toast'
import './App.css'

class ErrorBoundary extends Component<{ children: ReactNode }, { error: string | null }> {
  constructor(props: { children: ReactNode }) {
    super(props)
    this.state = { error: null }
  }
  static getDerivedStateFromError(error: Error) {
    return { error: error.message || 'Something went wrong' }
  }
  render() {
    if (this.state.error) {
      return (
        <div style={{ background: '#0d0d14', color: '#e8c36a', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '2rem', fontFamily: 'sans-serif', fontSize: '1.2rem' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⚠️</div>
          <h2 style={{ color: '#e8c36a', marginBottom: '1rem' }}>The dungeon collapsed!</h2>
          <p style={{ color: '#b0b0c8', marginBottom: '2rem', maxWidth: '600px', textAlign: 'center' }}>{this.state.error}</p>
          <button onClick={() => window.location.reload()} style={{ background: '#d4a846', color: '#0d0d14', border: 'none', padding: '0.75rem 2rem', borderRadius: '8px', fontSize: '1rem', cursor: 'pointer', fontWeight: 700 }}>
            Try Again
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

function AppLayout() {
  const [scrolled, setScrolled] = useState(false)
  const location = useLocation()
  const isGameSession = location.pathname.startsWith('/game/')

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <div className={`app ${isGameSession ? 'app-fullscreen' : ''}`}>
      <a href="#main-content" className="skip-link">Skip to content</a>
      {!isGameSession && (
        <nav className={`navbar ${scrolled ? 'navbar-scrolled' : ''}`} role="navigation" aria-label="Main navigation">
          <Link to="/" className="navbar-brand">
            <span className="brand-icon" aria-hidden="true">⚔️</span>
            <span className="brand-text">AI Dungeon Master</span>
          </Link>
        </nav>
      )}
      <main id="main-content" className={isGameSession ? 'main-fullscreen' : ''}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/campaign/:campaignId" element={<CampaignDetail />} />
          <Route path="/game/:sessionId" element={<GameSession />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      {!isGameSession && <Footer />}
    </div>
  )
}

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <ToastProvider>
          <AppLayout />
        </ToastProvider>
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App
