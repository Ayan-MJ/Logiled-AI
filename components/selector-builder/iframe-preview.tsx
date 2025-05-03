"use client"

import { useState } from "react"
import { Minus, Plus, ArrowLeft, ArrowRight, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"

interface IframePreviewProps {
  url: string
  onElementSelect: (selector: string) => void
}

export function IframePreview({ url, onElementSelect }: IframePreviewProps) {
  const [zoom, setZoom] = useState(100)
  const [isLoading, setIsLoading] = useState(true)
  const [hoveredElement, setHoveredElement] = useState<string | null>(null)

  // This would be implemented with a real iframe communication mechanism
  // For demo purposes, we're simulating the behavior
  const handleIframeLoad = () => {
    setIsLoading(false)
    // In a real implementation, we would inject scripts into the iframe
    // to handle element hovering and selection
  }

  const handleZoomIn = () => {
    setZoom((prev) => Math.min(prev + 10, 200))
  }

  const handleZoomOut = () => {
    setZoom((prev) => Math.max(prev - 10, 50))
  }

  // Simulate element hover (in a real app, this would come from iframe events)
  const simulateElementHover = () => {
    const elements = [
      "h1.product-title",
      "span.price",
      "div.product-description p",
      "button.add-to-cart",
      "div.product-rating",
    ]
    const randomElement = elements[Math.floor(Math.random() * elements.length)]
    setHoveredElement(randomElement)

    // Clear after 3 seconds to simulate mouse moving away
    setTimeout(() => setHoveredElement(null), 3000)
  }

  return (
    <div className="relative h-full w-full">
      {/* Loading overlay */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/80 z-10">
          <Loader2 className="h-8 w-8 animate-spin text-[#4F46E5]" />
          <span className="ml-2 text-lg font-medium">Loading preview...</span>
        </div>
      )}

      {/* Navigation Controls */}
      <div className="absolute left-4 top-4 z-10 flex items-center gap-2 rounded-md bg-white/90 p-1 shadow-md">
        <Button variant="ghost" size="icon" className="h-8 w-8">
          <ArrowLeft className="h-4 w-4" />
          <span className="sr-only">Back</span>
        </Button>
        <Button variant="ghost" size="icon" className="h-8 w-8">
          <ArrowRight className="h-4 w-4" />
          <span className="sr-only">Forward</span>
        </Button>
      </div>

      {/* Zoom Controls */}
      <div className="absolute right-4 top-4 z-10 flex items-center gap-2 rounded-md bg-white/90 p-1 shadow-md">
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleZoomOut}>
          <Minus className="h-4 w-4" />
          <span className="sr-only">Zoom out</span>
        </Button>
        <span className="text-xs font-medium">{zoom}%</span>
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleZoomIn}>
          <Plus className="h-4 w-4" />
          <span className="sr-only">Zoom in</span>
        </Button>
      </div>

      {/* Iframe */}
      <div
        className="h-full w-full bg-white"
        style={{ transform: `scale(${zoom / 100})`, transformOrigin: "top left" }}
      >
        {/* For demo purposes, we'll show a placeholder instead of a real iframe */}
        <div
          className="h-full w-full overflow-auto border-0 bg-white p-4"
          onClick={() => simulateElementHover()}
          onLoad={handleIframeLoad}
        >
          <div className="mx-auto max-w-4xl">
            <h1 className="mb-4 text-3xl font-bold">Product Page Example</h1>
            <p className="text-muted-foreground">This is a simulated webpage for demonstration purposes.</p>

            <div className="mt-8 grid grid-cols-1 gap-8 md:grid-cols-2">
              <div className="aspect-square bg-gray-100 flex items-center justify-center">
                <span className="text-muted-foreground">Product Image</span>
              </div>

              <div>
                <h1 className="product-title text-2xl font-bold">iPhone 13 Pro</h1>
                <div className="product-rating mt-2 flex">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <span key={star} className="text-yellow-400">
                      ★
                    </span>
                  ))}
                  <span className="ml-2 text-sm text-muted-foreground">(128 reviews)</span>
                </div>

                <span className="price mt-4 block text-xl font-semibold">$999.99</span>

                <div className="product-description mt-6">
                  <h3 className="font-medium">Description</h3>
                  <p className="mt-2 text-muted-foreground">
                    The latest iPhone with an amazing camera, powerful A15 Bionic chip, and stunning Super Retina XDR
                    display.
                  </p>
                </div>

                <button className="add-to-cart mt-8 rounded-md bg-[#4F46E5] px-4 py-2 text-white hover:bg-[#4338CA]">
                  Add to Cart
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Hover Overlay */}
      {hoveredElement && (
        <div className="absolute left-1/4 top-1/3 z-20 rounded border-2 border-[#4F46E5] bg-[#4F46E5]/10 p-8">
          <div className="absolute -top-6 left-0 rounded-t-md bg-[#FDE68A] px-2 py-1 text-xs font-medium">
            AI Suggestion: {hoveredElement}
          </div>
        </div>
      )}
    </div>
  )
}
