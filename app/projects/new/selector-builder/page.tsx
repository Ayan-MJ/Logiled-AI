import { SelectorBuilderHeader } from "@/components/selector-builder/selector-builder-header"
import { SelectorBuilderCanvas } from "@/components/selector-builder/selector-builder-canvas"
import { SelectorBuilderFooter } from "@/components/selector-builder/selector-builder-footer"

export default function SelectorBuilderPage() {
  return (
    <div className="flex flex-col h-screen bg-[#F9FAFB]">
      <SelectorBuilderHeader />
      <SelectorBuilderCanvas />
      <SelectorBuilderFooter />
    </div>
  )
}
