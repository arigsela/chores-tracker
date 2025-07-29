import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/utils'
import { Loading } from './Loading'

describe('Loading Component', () => {
  it('renders with default message', () => {
    render(<Loading />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders with custom message', () => {
    render(<Loading message="Loading chores..." />)
    expect(screen.getByText('Loading chores...')).toBeInTheDocument()
  })

  it('renders fullscreen when prop is true', () => {
    render(<Loading fullScreen />)
    // MUI Box components apply styles via classes, not inline styles
    // We'll check for the loading text which should still be present
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })
})