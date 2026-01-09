import axios from 'axios'
import { useAuthStore } from '../store/authStore'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

// Create axios instance
const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Request interceptor - add auth token
api.interceptors.request.use(
    (config) => {
        const { accessToken } = useAuthStore.getState()
        if (accessToken) {
            config.headers.Authorization = `Bearer ${accessToken}`
        }
        return config
    },
    (error) => Promise.reject(error)
)

// Response interceptor - handle token refresh
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config

        // If 401 and not already retrying
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true

            const { refreshToken, clearAuth } = useAuthStore.getState()

            // For settings page, don't redirect - let the page handle the error
            if (originalRequest.url?.includes('/settings')) {
                // Try to refresh token silently
                if (refreshToken) {
                    try {
                        const response = await axios.post(`${API_URL}/auth/refresh`, null, {
                            params: { refresh_token: refreshToken },
                        })

                        const { access_token, refresh_token: new_refresh_token } = response.data

                        // Update store
                        useAuthStore.setState({
                            accessToken: access_token,
                            refreshToken: new_refresh_token,
                        })

                        // Retry original request
                        originalRequest.headers.Authorization = `Bearer ${access_token}`
                        return api(originalRequest)
                    } catch (refreshError) {
                        // Refresh failed, clear auth but don't redirect
                        clearAuth()
                        return Promise.reject(error)
                    }
                } else {
                    // No refresh token
                    clearAuth()
                    return Promise.reject(error)
                }
            }

            // For other pages, redirect to login
            if (refreshToken) {
                try {
                    // Try to refresh token
                    const response = await axios.post(`${API_URL}/auth/refresh`, null, {
                        params: { refresh_token: refreshToken },
                    })

                    const { access_token, refresh_token: new_refresh_token } = response.data

                    // Update store
                    useAuthStore.setState({
                        accessToken: access_token,
                        refreshToken: new_refresh_token,
                    })

                    // Retry original request
                    originalRequest.headers.Authorization = `Bearer ${access_token}`
                    return api(originalRequest)
                } catch (refreshError) {
                    // Refresh failed, clear auth and redirect
                    clearAuth()
                    window.location.href = '/login'
                }
            } else {
                clearAuth()
                window.location.href = '/login'
            }
        }

        return Promise.reject(error)
    }
)

export default api
