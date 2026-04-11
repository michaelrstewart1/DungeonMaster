import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { Home } from './pages/Home'
import { CampaignDetail } from './pages/CampaignDetail'
import { GameSession } from './pages/GameSession'
import { NotFound } from './pages/NotFound'
import { Footer } from './components/Footer'
import { ToastProvider } from './components/Toast'
import './App.css'

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
    <BrowserRouter>
      <ToastProvider>
        <AppLayout />
      </ToastProvider>
    </BrowserRouter>
  )
}

export default App
