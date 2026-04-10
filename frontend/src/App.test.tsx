import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from './App'

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />)
    // Vite default template renders a heading or content
    expect(document.body).toBeTruthy()
  })

  it('renders the app container', () => {
    const { container } = render(<App />)
    expect(container.firstChild).toBeTruthy()
  })
})
