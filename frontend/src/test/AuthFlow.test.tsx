import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, it, expect } from 'vitest'
import { LoginPage } from '../pages/Login/LoginPage'
import { AuthProvider } from '../context/AuthContext'

describe('LoginPage Component & Authentication Shell', () => {
  it('renders login form elements by default', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <LoginPage />
        </BrowserRouter>
      </AuthProvider>,
    )

    expect(screen.getByText('JobWatch AI')).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /Sign In/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /Create Account/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Sign In to Dashboard/i })).toBeInTheDocument()
  })

  it('switches between Sign In and Create Account tabs', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <LoginPage />
        </BrowserRouter>
      </AuthProvider>,
    )

    const createTab = screen.getByRole('tab', { name: /Create Account/i })
    fireEvent.click(createTab)

    expect(screen.getByRole('button', { name: /Create Candidate Account/i })).toBeInTheDocument()
    expect(screen.getByText(/At least 8 characters required/i)).toBeInTheDocument()
  })

  it('displays validation message if password is too short', async () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <LoginPage />
        </BrowserRouter>
      </AuthProvider>,
    )

    const emailInput = screen.getByLabelText(/Email Address/i)
    const passInput = screen.getByLabelText(/Password/i)
    const submitBtn = screen.getByRole('button', { name: /Sign In to Dashboard/i })

    fireEvent.change(emailInput, { target: { value: 'candidate@example.com' } })
    fireEvent.change(passInput, { target: { value: 'short' } })
    fireEvent.click(submitBtn)

    expect(await screen.findByText(/Password must be at least 8 characters long/i)).toBeInTheDocument()
  })
})
