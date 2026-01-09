import api from './api'
import { useAuthStore } from '../store/authStore'

interface GoogleLoginResponse {
    access_token: string
    refresh_token: string
    token_type: string
}

interface User {
    id: string
    email: string
    full_name?: string
    is_verified: boolean
}

export const authService = {
    /**
     * Login with Google OAuth access token
     */
    async googleLogin(googleAccessToken: string): Promise<void> {
        const response = await api.post<GoogleLoginResponse>('/auth/google', {
            access_token: googleAccessToken,
        })

        const { access_token, refresh_token } = response.data

        // Get user info
        const userResponse = await api.get<User>('/auth/me', {
            headers: { Authorization: `Bearer ${access_token}` },
        })

        // Update auth store
        useAuthStore.getState().setAuth(access_token, refresh_token, userResponse.data)
    },

    /**
     * Logout current user
     */
    async logout(): Promise<void> {
        try {
            await api.post('/auth/logout')
        } finally {
            useAuthStore.getState().clearAuth()
        }
    },

    /**
     * Get current user info
     */
    async getCurrentUser(): Promise<User> {
        const response = await api.get<User>('/auth/me')
        useAuthStore.getState().setUser(response.data)
        return response.data
    },
}
