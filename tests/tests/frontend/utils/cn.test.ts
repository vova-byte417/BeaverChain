import { describe, it, expect } from 'vitest'
import { cn } from '@/utils/cn'

describe('cn utility function', () => {
  it('should merge class names correctly', () => {
    const result = cn('class1', 'class2')
    expect(result).toBe('class1 class2')
  })

  it('should handle conditional classes', () => {
    const isActive = true
    const result = cn('base', isActive && 'active')
    expect(result).toBe('base active')
  })

  it('should filter out falsy values', () => {
    const result = cn('class1', null, undefined, false, 'class2')
    expect(result).toBe('class1 class2')
  })

  it('should handle object syntax', () => {
    const result = cn({ 'bg-red-500': true, 'hidden': false })
    expect(result).toBe('bg-red-500')
  })

  it('should handle array syntax', () => {
    const result = cn(['class1', 'class2'], ['class3'])
    expect(result).toBe('class1 class2 class3')
  })

  it('should handle mixed syntax', () => {
    const result = cn('base', { active: true }, ['extra'], null)
    expect(result).toBe('base active extra')
  })

  it('should return empty string for no classes', () => {
    const result = cn()
    expect(result).toBe('')
  })

  it('should handle deeply nested arrays', () => {
    const result = cn(['level1', ['level2', ['level3']]])
    expect(result).toBe('level1 level2 level3')
  })

  it('should deduplicate classes', () => {
    const result = cn('btn', 'btn', 'btn-primary')
    expect(result.split(' ').filter(c => c === 'btn').length).toBe(1)
  })
})
