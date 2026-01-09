import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Research from './pages/Research'
import ContentGeneration from './pages/ContentGeneration'
import Projects from './pages/Projects'
import SEOChecker from './pages/SEOChecker'
import Settings from './pages/Settings'
import Layout from './components/Layout'

function App() {
    const { isAuthenticated } = useAuthStore()

    return (
        <Routes>
            {/* Public routes */}
            <Route
                path="/login"
                element={isAuthenticated ? <Navigate to="/" replace /> : <Login />}
            />

            {/* Protected routes */}
            <Route
                path="/"
                element={isAuthenticated ? <Layout /> : <Navigate to="/login" replace />}
            >
                <Route index element={<Dashboard />} />
                <Route path="research" element={<Research />} />
                <Route path="content" element={<ContentGeneration />} />
                <Route path="projects" element={<Projects />} />
                <Route path="seo-checker" element={<SEOChecker />} />
                <Route path="settings" element={<Settings />} />
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    )
}

export default App
