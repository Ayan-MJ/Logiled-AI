"use client"

import { useState } from "react"
import { IframePreview } from "@/components/selector-builder/iframe-preview"
import { FieldConfigSidebar } from "@/components/selector-builder/field-config-sidebar"
import { FloatingActionToolbar } from "@/components/selector-builder/floating-action-toolbar"

export function SelectorBuilderCanvas() {
  const [selectedField, setSelectedField] = useState<string | null>(null)
  const [fields, setFields] = useState([
    {
      id: "1",
      name: "Product Title",
      selector: "h1.product-title",
      samples: ["iPhone 13 Pro", "Samsung Galaxy S22", "Google Pixel 6"],
    },
    { id: "2", name: "Price", selector: "span.price", samples: ["$999.99", "$899.99", "$799.99"] },
    {
      id: "3",
      name: "Description",
      selector: "div.product-description p",
      samples: ["The latest iPhone with...", "Experience the next generation...", "Google's flagship phone..."],
    },
  ])

  const [targetUrl, setTargetUrl] = useState("https://example.com/products")

  const handleAddField = () => {
    const newField = {
      id: `${fields.length + 1}`,
      name: `New Field ${fields.length + 1}`,
      selector: "",
      samples: [],
    }
    setFields([...fields, newField])
    setSelectedField(newField.id)
  }

  const handleDeleteField = (id: string) => {
    setFields(fields.filter((field) => field.id !== id))
    if (selectedField === id) {
      setSelectedField(null)
    }
  }

  const handleUpdateField = (id: string, updates: Partial<(typeof fields)[0]>) => {
    setFields(fields.map((field) => (field.id === id ? { ...field, ...updates } : field)))
  }

  const handleElementSelect = (selector: string) => {
    if (selectedField) {
      handleUpdateField(selectedField, { selector })
    } else if (fields.length > 0) {
      setSelectedField(fields[0].id)
      handleUpdateField(fields[0].id, { selector })
    } else {
      const newField = {
        id: "1",
        name: "New Field",
        selector,
        samples: [],
      }
      setFields([newField])
      setSelectedField(newField.id)
    }
  }

  return (
    <main className="flex flex-1 overflow-hidden">
      {/* Left Pane - Live Preview Frame */}
      <div className="relative flex-1 overflow-hidden border-r">
        <IframePreview url={targetUrl} onElementSelect={handleElementSelect} />
        <FloatingActionToolbar />
      </div>

      {/* Right Pane - Field Configuration Sidebar */}
      <div className="w-full md:w-96 lg:w-[400px] flex-shrink-0 overflow-y-auto bg-white">
        <FieldConfigSidebar
          fields={fields}
          selectedField={selectedField}
          onSelectField={setSelectedField}
          onAddField={handleAddField}
          onDeleteField={handleDeleteField}
          onUpdateField={handleUpdateField}
        />
      </div>
    </main>
  )
}
