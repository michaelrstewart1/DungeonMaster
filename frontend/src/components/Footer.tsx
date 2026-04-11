export function Footer() {
  return (
    <footer className="app-footer">
      <div className="footer-ornament">⚜ ✦ ⚜</div>
      <div className="footer-content">
        <span className="footer-brand">AI Dungeon Master</span>
        <span className="footer-separator">•</span>
        <span className="footer-powered">Powered by AI</span>
        <span className="footer-separator">•</span>
        <span className="footer-version">v0.1.0</span>
      </div>
      <p className="footer-copyright">© {new Date().getFullYear()} AI Dungeon Master. All rights reserved.</p>
    </footer>
  )
}
