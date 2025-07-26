// Basic test to ensure CI/CD pipeline works
describe('Basic Tests', () => {
  it('should pass basic math test', () => {
    expect(1 + 1).toBe(2)
  })

  it('should handle string operations', () => {
    expect('hello'.toUpperCase()).toBe('HELLO')
  })

  it('should handle array operations', () => {
    const arr = [1, 2, 3]
    expect(arr.length).toBe(3)
    expect(arr.includes(2)).toBe(true)
  })

  it('should handle object operations', () => {
    const obj = { name: 'test', value: 42 }
    expect(obj.name).toBe('test')
    expect(obj.value).toBe(42)
  })

  it('should handle async operations', async () => {
    const promise = Promise.resolve('success')
    const result = await promise
    expect(result).toBe('success')
  })
})