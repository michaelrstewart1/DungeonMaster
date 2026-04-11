import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import { Home } from './pages/Home'
import { CampaignDetail } from './pages/CampaignDetail'
import { GameSession } from './pages/GameSession'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <nav className="navbar">
          <Link to="/" className="navbar-brand">
            <span className="brand-icon">⚔️</span>
            <span className="brand-text">AI Dungeon Master</span>
          </Link>
        </nav>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/campaign/:campaignId" element={<CampaignDetail />} />
          <Route path="/game/:sessionId" element={<GameSession />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App
