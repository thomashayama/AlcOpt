import { expect, test, vi, beforeEach } from 'vitest'
import { api } from '../src/lib/api'

beforeEach(() => {
  vi.restoreAllMocks()
})

test('get sends GET request with credentials', async () => {
  const mockData = { id: 1, name: 'test' }
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: () => Promise.resolve(mockData),
  }))

  const result = await api.get('/api/test')
  expect(result).toEqual(mockData)
  expect(fetch).toHaveBeenCalledWith('/api/test', expect.objectContaining({
    method: 'GET',
    credentials: 'include',
  }))
})

test('post sends POST request with JSON body', async () => {
  const mockData = { success: true }
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: () => Promise.resolve(mockData),
  }))

  const body = { name: 'test' }
  const result = await api.post('/api/test', body)
  expect(result).toEqual(mockData)
  expect(fetch).toHaveBeenCalledWith('/api/test', expect.objectContaining({
    method: 'POST',
    body: JSON.stringify(body),
  }))
})

test('throws ApiError on non-ok response', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: false,
    status: 404,
    statusText: 'Not Found',
    json: () => Promise.resolve({ detail: 'Container not found' }),
  }))

  await expect(api.get('/api/test')).rejects.toThrow('Container not found')
})

test('returns undefined for 204 No Content', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true,
    status: 204,
    json: () => Promise.resolve(null),
  }))

  const result = await api.del('/api/test')
  expect(result).toBeUndefined()
})
