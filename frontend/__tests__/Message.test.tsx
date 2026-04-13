import { expect, test } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Message } from '../src/components/Message'

test('renders nothing when message is null', () => {
  const { container } = render(<Message message={null} />)
  expect(container.innerHTML).toBe('')
})

test('renders success message with green text', () => {
  render(<Message message={{ type: 'success', text: 'All good!' }} />)
  const el = screen.getByText('All good!')
  expect(el).toBeDefined()
  expect(el.className).toContain('text-green-500')
})

test('renders error message with destructive text', () => {
  render(<Message message={{ type: 'error', text: 'Something broke' }} />)
  const el = screen.getByText('Something broke')
  expect(el).toBeDefined()
  expect(el.className).toContain('text-destructive')
})
