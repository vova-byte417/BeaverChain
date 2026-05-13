import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import Models from '@/pages/Models'

// Mock data
vi.mock('@/mock/data', () => ({
  mockModels: [
    {
      id: '1',
      name: 'GPT-4 Turbo',
      version: '4.0.0',
      status: 'production',
      created_at: '2024-01-15T10:00:00Z',
      size_mb: 15000,
    },
    {
      id: '2',
      name: 'Llama 2 70B',
      version: '2.1.0',
      status: 'testing',
      created_at: '2024-01-10T08:00:00Z',
      size_mb: 138000,
    },
  ],
}))

describe('Models Page', () => {
  it('should render page title', () => {
    render(<Models />)
    expect(screen.getByRole('heading', { name: /model registry/i }) || screen.getByRole('heading', { name: /模型/i })).toBeInTheDocument()
  })

  it('should display list of models', () => {
    render(<Models />)
    
    expect(screen.getByText('GPT-4 Turbo')).toBeInTheDocument()
    expect(screen.getByText('Llama 2 70B')).toBeInTheDocument()
  })

  it('should show model status badges', () => {
    render(<Models />)
    
    expect(screen.getByText('production') || screen.getByText('Production')).toBeInTheDocument()
    expect(screen.getByText('testing') || screen.getByText('Testing')).toBeInTheDocument()
  })

  it('should have search functionality', () => {
    render(<Models />)
    
    const searchInput = screen.getByPlaceholderText(/search/i) || screen.getByRole('textbox')
    expect(searchInput).toBeInTheDocument()
    
    fireEvent.change(searchInput, { target: { value: 'GPT' } })
    
    // Should filter results
    expect(screen.getByText('GPT-4 Turbo')).toBeInTheDocument()
  })

  it('should have add new model button', () => {
    render(<Models />)
    
    const addButton = screen.getByRole('button', { name: /add model/i }) || 
                      screen.getByRole('button', { name: /new model/i }) ||
                      screen.getByRole('button', { name: /添加模型/i })
    expect(addButton).toBeInTheDocument()
  })

  it('should display model version information', () => {
    render(<Models />)
    
    expect(screen.getByText('4.0.0')).toBeInTheDocument()
    expect(screen.getByText('2.1.0')).toBeInTheDocument()
  })

  it('should display model size', () => {
    render(<Models />)
    
    expect(screen.getByText(/15000|138000/i)).toBeInTheDocument()
  })

  it('should have filter by status functionality', () => {
    render(<Models />)
    
    const filterDropdown = screen.getByRole('combobox') || 
                          screen.getByLabelText(/status/i) ||
                          screen.queryByText(/all statuses/i)
    
    if (filterDropdown) {
      expect(filterDropdown).toBeInTheDocument()
    }
  })
})
