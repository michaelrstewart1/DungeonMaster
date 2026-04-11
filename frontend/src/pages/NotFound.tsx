import { Link } from 'react-router-dom'

export function NotFound() {
  return (
    <div className="page-not-found">
      <div className="not-found-content">
        <div className="not-found-icon">🐉</div>
        <h1 className="not-found-code">404</h1>
        <h2 className="not-found-title">Lost in the Dungeon</h2>
        <p className="not-found-message">
          The path you seek does not exist in this realm. 
          Perhaps the dungeon has shifted, or the map was drawn by a mischievous imp.
        </p>
        <Link to="/" className="btn-primary not-found-link">
          Return to the Tavern
        </Link>
      </div>
    </div>
  )
}
