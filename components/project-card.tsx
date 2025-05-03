"use client"

import { useState } from "react"
import { Play, Settings, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface ProjectCardProps {
  project: {
    id: string
    name: string
    status: "active" | "warning" | "error"
    lastRun: string
    duration: string
  }
}

export function ProjectCard({ project }: ProjectCardProps) {
  const [isHovered, setIsHovered] = useState(false)

  const statusColors = {
    active: "bg-[#10B981] text-white",
    warning: "bg-[#F59E0B] text-white",
    error: "bg-[#EF4444] text-white",
  }

  const statusLabels = {
    active: "Active",
    warning: "Warning",
    error: "Error",
  }

  return (
    <div
      className={cn(
        "bg-white rounded-lg border p-4 transition-all duration-150",
        isHovered ? "shadow-md translate-y-[-2px]" : "shadow-sm",
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Card Header */}
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-bold text-lg truncate">{project.name}</h3>
        <span className={cn("px-2 py-1 rounded-full text-xs font-medium", statusColors[project.status])}>
          {statusLabels[project.status]}
        </span>
      </div>

      {/* Card Body */}
      <div className="mb-4 text-sm text-muted-foreground">
        <p>Last run: {project.lastRun}</p>
        <p>Runtime: {project.duration}</p>
      </div>

      {/* Card Footer */}
      <div className="flex justify-between items-center">
        <Button
          variant={isHovered ? "default" : "outline"}
          size="sm"
          className={cn("transition-colors duration-150", isHovered && "bg-[#4F46E5] hover:bg-[#4338CA]")}
        >
          <Play className="h-4 w-4 mr-1" />
          Run Now
        </Button>
        <div className="flex gap-2">
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <Settings className="h-4 w-4" />
            <span className="sr-only">Settings</span>
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <FileText className="h-4 w-4" />
            <span className="sr-only">Logs</span>
          </Button>
        </div>
      </div>
    </div>
  )
}
