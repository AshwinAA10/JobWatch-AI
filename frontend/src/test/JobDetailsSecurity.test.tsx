import DOMPurify from 'dompurify'
import { describe, it, expect } from 'vitest'

describe('Job Details Security & HTML Sanitization', () => {
  it('strips malicious <script> tags from external job descriptions', () => {
    const maliciousHtml = '<div>Safe content</div><script>alert("xss attack")</script>'
    const sanitized = DOMPurify.sanitize(maliciousHtml, {
      ALLOWED_TAGS: ['p', 'b', 'i', 'div', 'span', 'ul', 'li', 'a'],
      ALLOWED_ATTR: ['href', 'target', 'rel'],
    })

    expect(sanitized).not.toContain('<script>')
    expect(sanitized).not.toContain('alert(')
    expect(sanitized).toContain('Safe content')
  })

  it('removes inline JavaScript event handlers (onerror, onload, onclick)', () => {
    const maliciousImg = '<p>Role description</p><img src="x" onerror="window.location=\'http://attacker.com\'" />'
    const sanitized = DOMPurify.sanitize(maliciousImg, {
      ALLOWED_TAGS: ['p', 'span', 'b', 'i'],
      ALLOWED_ATTR: ['href'],
    })

    expect(sanitized).not.toContain('onerror')
    expect(sanitized).not.toContain('attacker.com')
    expect(sanitized).toContain('Role description')
  })

  it('preserves legitimate formatting elements such as lists, bold, and paragraphs', () => {
    const validJobHtml = '<h3>Key Responsibilities:</h3><ul><li>Develop APIs</li><li>Deploy Docker</li></ul>'
    const sanitized = DOMPurify.sanitize(validJobHtml, {
      ALLOWED_TAGS: ['h3', 'ul', 'li'],
      ALLOWED_ATTR: [],
    })

    expect(sanitized).toContain('<h3>Key Responsibilities:</h3>')
    expect(sanitized).toContain('<li>Develop APIs</li>')
  })
})
