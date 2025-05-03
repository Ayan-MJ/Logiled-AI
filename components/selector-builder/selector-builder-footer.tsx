import { ArrowLeft, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"

export function SelectorBuilderFooter() {
  return (
    <footer className="border-t bg-white py-4">
      <div className="container mx-auto flex items-center justify-between px-4">
        <Button variant="outline" className="gap-2">
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
        <Button className="gap-2 bg-[#4F46E5] hover:bg-[#4338CA]">
          Next: Scheduling
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </footer>
  )
}
