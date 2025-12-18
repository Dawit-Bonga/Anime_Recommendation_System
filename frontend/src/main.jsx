import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Toaster } from 'react-hot-toast'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
    <Toaster 
      position="top-right"
      toastOptions={{
        duration: 4000,
        style: {
          background: 'rgba(30, 41, 59, 0.95)',
          color: '#f8fafc',
          border: '1px solid rgba(148, 163, 184, 0.2)',
          borderRadius: '12px',
          backdropFilter: 'blur(10px)',
        },
        success: {
          iconTheme: {
            primary: '#10b981',
            secondary: '#f8fafc',
          },
        },
        error: {
          iconTheme: {
            primary: '#ef4444',
            secondary: '#f8fafc',
          },
        },
      }}
    />
  </StrictMode>,
)
