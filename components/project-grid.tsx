import { ProjectCard } from "@/components/project-card"
import { EmptyState } from "@/components/empty-state"

interface Project {
  id: string
  name: string
  status: "active" | "warning" | "error"
  lastRun: string
  duration: string
}

interface ProjectGridProps {
  projects: Project[]
}

export function ProjectGrid({ projects }: ProjectGridProps) {
  if (projects.length === 0) {
    return <EmptyState />
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {projects.map((project) => (
        <ProjectCard key={project.id} project={project} />
      ))}
    </div>
  )
}
