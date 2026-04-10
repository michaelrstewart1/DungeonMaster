import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Home } from './pages/Home'
import { GameSession } from './pages/GameSession'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/game/:sessionId" element={<GameSession />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App
