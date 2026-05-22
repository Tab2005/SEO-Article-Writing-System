import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { Project } from '../services/planning.service'

interface ProjectState {
    currentProjectId: string | null
    currentProject: Project | null
    setCurrentProject: (project: Project | null) => void
    setCurrentProjectId: (id: string | null) => void
}

export const useProjectStore = create<ProjectState>()(
    persist(
        (set) => ({
            currentProjectId: null,
            currentProject: null,
            setCurrentProject: (project) => set({
                currentProject: project,
                currentProjectId: project ? project.id : null
            }),
            setCurrentProjectId: (id) => set({
                currentProjectId: id,
                currentProject: null // Will be populated when needed, or kept separate
            })
        }),
        {
            name: 'seo-project-store',
        }
    )
)
