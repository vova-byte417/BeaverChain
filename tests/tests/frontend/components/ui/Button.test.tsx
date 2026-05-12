import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '@/components/ui/Button'

describe('Button Component', () => {
  it('should render correctly', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument()
  })

  it('should handle click events', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Click</Button>)
    
    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('should show loading state', () => {
    render(<Button loading>Submit</Button>)
    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
    expect(button).toHaveTextContent(/loading|Submit/i)
  })

  it('should be disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('should apply variant classes correctly', () => {
    const { rerender } = render(<Button variant="primary">Primary</Button>)
    expect(screen.getByRole('button')).toHaveClass(/primary|bg-blue/)

    rerender(<Button variant="secondary">Secondary</Button>)
    expect(screen.getByRole('button')).toHaveClass(/secondary|bg-gray/)

    rerender(<Button variant="danger">Danger</Button>)
    expect(screen.getByRole('button')).toHaveClass(/danger|bg-red/)
  })

  it('should apply size classes correctly', () => {
    const { rerender } = render(<Button size="sm">Small</Button>)
    expect(screen.getByRole('button')).toHaveClass(/sm|text-sm|py-1/)

    rerender(<Button size="md">Medium</Button>)
    expect(screen.getByRole('button')).toHaveClass(/md|text-base|py-2/)

    rerender(<Button size="lg">Large</Button>)
    expect(screen.getByRole('button')).toHaveClass(/lg|text-lg|py-3/)
  })

  it('should pass through additional props', () => {
    render(
      <Button 
        data-testid="custom-btn" 
        aria-label="Test button"
        type="submit"
      >
        Button
      </Button>
    )
    
    const button = screen.getByTestId('custom-btn')
    expect(button).toHaveAttribute('aria-label', 'Test button')
    expect(button).toHaveAttribute('type', 'submit')
  })

  it('should render icon when provided', () => {
    const Icon = () => <span data-testid="icon">🔍</span>
    render(<Button icon={<Icon />}>Search</Button>)
    
    expect(screen.getByTestId('icon')).toBeInTheDocument()
  })

  it('should have correct default type', () => {
    render(<Button>Default</Button>)
    expect(screen.getByRole('button')).toHaveAttribute('type', 'button')
  })

  it('should not trigger click when disabled', () => {
    const handleClick = vi.fn()
    render(
      <Button disabled onClick={handleClick}>
        Disabled
      </Button>
    )
    
    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).not.toHaveBeenCalled()
  })
})
