import api from './api'
import { useAuthStore } from '../store/authStore'

interface UserInfo {
    id: string
    email: string
    full_name?: string
    is_verified: boolean
}

interface GoogleLoginResponse {
    access_token: string
    refresh_token: string
    token_type: string
    user: UserInfo
}

export const authService = {
    /**
     * Login with Google OAuth access token
     */
    async googleLogin(googleAccessToken: string): Promise<void> {
        console.log('[AuthService] Starting Google login...')

        const response = await api.post<GoogleLoginResponse>('/auth/google', {
            access_token: googleAccessToken,
        })

        console.log('[AuthService] Got response from backend')
        const { access_token, refresh_token, user } = response.data
        console.log('[AuthService] User:', user.email)

        // Update auth store with user info from response
        useAuthStore.getState().setAuth(access_token, refresh_token, user)
        console.log('[AuthService] Auth state updated, login complete!')
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
    async getCurrentUser(): Promise<UserInfo> {
        const response = await api.get<UserInfo>('/auth/me')
        useAuthStore.getState().setUser(response.data)
        return response.data
    },
}
