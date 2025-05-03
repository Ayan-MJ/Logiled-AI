import { DashboardHeader } from "@/components/dashboard-header"
import { DashboardHero } from "@/components/dashboard-hero"
import { ProjectGrid } from "@/components/project-grid"
import { DashboardFooter } from "@/components/dashboard-footer"

export default function Dashboard() {
  // Sample projects data - in a real app, this would come from an API or database
  const projects = [
    {
      id: "1",
      name: "E-commerce Product Scraper",
      status: "active",
      lastRun: "2 hours ago",
      duration: "1m 45s",
    },
    {
      id: "2",
      name: "News Article Aggregator",
      status: "warning",
      lastRun: "1 day ago",
      duration: "3m 12s",
    },
    {
      id: "3",
      name: "Social Media Monitor",
      status: "error",
      lastRun: "3 days ago",
      duration: "Failed",
    },
    {
      id: "4",
      name: "Price Comparison Tool",
      status: "active",
      lastRun: "5 hours ago",
      duration: "2m 30s",
    },
    {
      id: "5",
      name: "Job Listings Tracker",
      status: "active",
      lastRun: "12 hours ago",
      duration: "4m 10s",
    },
  ]

  // Toggle to show empty state
  const showEmptyState = false

  return (
    <div className="min-h-screen flex flex-col bg-[#F9FAFB]">
      <DashboardHeader />
      <main className="flex-1">
        <DashboardHero />
        <div className="container mx-auto px-4 py-8">
          <ProjectGrid projects={showEmptyState ? [] : projects} />
        </div>
      </main>
      <DashboardFooter />
    </div>
  )
}
