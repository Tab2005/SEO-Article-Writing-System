import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Research from './pages/Research'
import ContentGeneration from './pages/ContentGeneration'
import StrategyWizard from './pages/StrategyWizard'
import Projects from './pages/Projects'
import ProjectSetup from './pages/ProjectSetup'
import SiteProfile from './pages/SiteProfile'
import TopicMap from './pages/TopicMap'
import Qualification from './pages/Qualification'
import BriefsList from './pages/BriefsList'
import BriefBuilder from './pages/BriefBuilder'
import SEOChecker from './pages/SEOChecker'
import Settings from './pages/Settings'
import ContentQueue from './pages/ContentQueue'
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
                <Route path="strategy-wizard" element={<StrategyWizard />} />
                <Route path="projects" element={<Projects />} />
                <Route path="project-setup" element={<ProjectSetup />} />
                <Route path="site-profile" element={<SiteProfile />} />
                <Route path="topic-map" element={<TopicMap />} />
                <Route path="qualification" element={<Qualification />} />
                <Route path="briefs" element={<BriefsList />} />
                <Route path="briefs/:briefId" element={<BriefBuilder />} />
                <Route path="seo-checker" element={<SEOChecker />} />
                <Route path="queue" element={<ContentQueue />} />
                <Route path="settings" element={<Settings />} />
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    )
}

export default App
