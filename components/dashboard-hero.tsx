import { Button } from "@/components/ui/button"
import { PlusCircle } from "lucide-react"

export function DashboardHero() {
  return (
    <section className="bg-white py-8 border-b">
      <div className="container mx-auto px-4">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight">Your Scraping Projects</h1>
            <p className="text-muted-foreground mt-1">Overview of status, performance, and quick actions</p>
          </div>
          <Button className="bg-[#4F46E5] hover:bg-[#4338CA]">
            <PlusCircle className="mr-2 h-4 w-4" />
            New Project
          </Button>
        </div>
      </div>
    </section>
  )
}
