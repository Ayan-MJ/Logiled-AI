import Link from "next/link"
import { ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"

export function SelectorBuilderHeader() {
  return (
    <header className="sticky top-0 z-10 w-full border-b bg-white">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        {/* Breadcrumb */}
        <div className="flex items-center text-sm">
          <Link href="/projects/new" className="text-muted-foreground hover:text-foreground">
            New Project
          </Link>
          <ChevronRight className="mx-2 h-4 w-4 text-muted-foreground" />
          <span className="font-medium">Step 3: Selector Builder</span>
        </div>

        {/* Save Button */}
        <Button className="bg-[#4F46E5] hover:bg-[#4338CA]">Save & Continue</Button>
      </div>
    </header>
  )
}
