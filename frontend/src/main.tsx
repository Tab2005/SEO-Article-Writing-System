import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

// React Query client
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 5 * 60 * 1000, // 5 minutes
            retry: 1,
        },
    },
})

// Conditionally wrap with GoogleOAuthProvider only if client ID exists
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID

function AppWrapper() {
    const content = (
        <QueryClientProvider client={queryClient}>
            <BrowserRouter>
                <App />
            </BrowserRouter>
        </QueryClientProvider>
    )

    // Only use GoogleOAuthProvider if client ID is configured
    if (GOOGLE_CLIENT_ID) {
        // Dynamic import to avoid errors when not configured
        const { GoogleOAuthProvider } = require('@react-oauth/google')
        return (
            <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
                {content}
            </GoogleOAuthProvider>
        )
    }

    return content
}

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <AppWrapper />
    </React.StrictMode>,
)
