import { Undo2, Redo2, Lightbulb, HelpCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

export function FloatingActionToolbar() {
  return (
    <div className="absolute bottom-4 left-4 z-10 flex items-center gap-1 rounded-md bg-white/90 p-1 shadow-md">
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <Undo2 className="h-4 w-4" />
              <span className="sr-only">Undo</span>
            </Button>
          </TooltipTrigger>
          <TooltipContent side="top">
            <p>Undo (Ctrl+Z)</p>
          </TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <Redo2 className="h-4 w-4" />
              <span className="sr-only">Redo</span>
            </Button>
          </TooltipTrigger>
          <TooltipContent side="top">
            <p>Redo (Ctrl+Y)</p>
          </TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <Lightbulb className="h-4 w-4 text-yellow-500" />
              <span className="sr-only">Toggle AI Suggestions</span>
            </Button>
          </TooltipTrigger>
          <TooltipContent side="top">
            <p>Toggle AI Suggestions</p>
          </TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <HelpCircle className="h-4 w-4" />
              <span className="sr-only">Help</span>
            </Button>
          </TooltipTrigger>
          <TooltipContent side="top">
            <p>Help & Tutorial</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  )
}
