import { render, screen } from '@testing-library/react'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'

describe('UI Components', () => {
  it('Button renders without crashing', () => {
    expect(() => render(<Button>Click me</Button>)).not.toThrow()
  })

  it('Card renders without crashing', () => {
    expect(() => render(<Card><p>content</p></Card>)).not.toThrow()
  })
})
