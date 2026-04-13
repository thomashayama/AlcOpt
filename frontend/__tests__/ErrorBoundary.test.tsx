import { expect, test, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ErrorBoundary } from '../src/components/ErrorBoundary'

function ThrowingComponent() {
  throw new Error('Test error')
}

function GoodComponent() {
  return <p>Everything is fine</p>
}

test('renders children when no error occurs', () => {
  render(
    <ErrorBoundary>
      <GoodComponent />
    </ErrorBoundary>
  )
  expect(screen.getByText('Everything is fine')).toBeDefined()
})

test('renders error UI when child throws', () => {
  // Suppress console.error from React
  vi.spyOn(console, 'error').mockImplementation(() => {})

  render(
    <ErrorBoundary>
      <ThrowingComponent />
    </ErrorBoundary>
  )
  expect(screen.getByText('Something went wrong')).toBeDefined()
  expect(screen.getByText('Test error')).toBeDefined()
  expect(screen.getByRole('button', { name: 'Try again' })).toBeDefined()

  vi.restoreAllMocks()
})

test('renders custom fallback when provided', () => {
  vi.spyOn(console, 'error').mockImplementation(() => {})

  render(
    <ErrorBoundary fallback={<p>Custom fallback</p>}>
      <ThrowingComponent />
    </ErrorBoundary>
  )
  expect(screen.getByText('Custom fallback')).toBeDefined()

  vi.restoreAllMocks()
})
