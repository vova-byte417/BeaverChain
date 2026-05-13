import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/Card'

describe('Card Component', () => {
  describe('Card', () => {
    it('should render correctly with children', () => {
      render(<Card>Card content</Card>)
      expect(screen.getByText('Card content')).toBeInTheDocument()
    })

    it('should apply custom className', () => {
      render(<Card className="custom-class">Content</Card>)
      expect(screen.getByText('Content').parentElement).toHaveClass('custom-class')
    })
  })

  describe('CardHeader', () => {
    it('should render header content', () => {
      render(<CardHeader>Header content</CardHeader>)
      expect(screen.getByText('Header content')).toBeInTheDocument()
    })
  })

  describe('CardTitle', () => {
    it('should render title correctly', () => {
      render(<CardTitle>Card Title</CardTitle>)
      expect(screen.getByRole('heading', { name: /card title/i })).toBeInTheDocument()
    })
  })

  describe('CardContent', () => {
    it('should render content correctly', () => {
      render(<CardContent>Body content</CardContent>)
      expect(screen.getByText('Body content')).toBeInTheDocument()
    })
  })

  describe('CardFooter', () => {
    it('should render footer correctly', () => {
      render(<CardFooter>Footer content</CardFooter>)
      expect(screen.getByText('Footer content')).toBeInTheDocument()
    })
  })

  describe('Full Card Composition', () => {
    it('should render complete card structure', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Test Card</CardTitle>
          </CardHeader>
          <CardContent>
            <p>This is the card body</p>
          </CardContent>
          <CardFooter>
            <button>Action</button>
          </CardFooter>
        </Card>
      )

      expect(screen.getByRole('heading', { name: /test card/i })).toBeInTheDocument()
      expect(screen.getByText('This is the card body')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /action/i })).toBeInTheDocument()
    })
  })
})
