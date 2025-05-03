"use client"

import { useState } from "react"
import { Pencil, Trash2, Plus, X, Check } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

interface Field {
  id: string
  name: string
  selector: string
  samples: string[]
}

interface FieldConfigSidebarProps {
  fields: Field[]
  selectedField: string | null
  onSelectField: (id: string | null) => void
  onAddField: () => void
  onDeleteField: (id: string) => void
  onUpdateField: (id: string, updates: Partial<Field>) => void
}

export function FieldConfigSidebar({
  fields,
  selectedField,
  onSelectField,
  onAddField,
  onDeleteField,
  onUpdateField,
}: FieldConfigSidebarProps) {
  const [editingField, setEditingField] = useState<string | null>(null)
  const [editValue, setEditValue] = useState("")

  const handleStartEdit = (field: Field) => {
    setEditingField(field.id)
    setEditValue(field.name)
  }

  const handleSaveEdit = () => {
    if (editingField) {
      onUpdateField(editingField, { name: editValue })
      setEditingField(null)
    }
  }

  const handleCancelEdit = () => {
    setEditingField(null)
  }

  const currentField = fields.find((f) => f.id === selectedField)

  return (
    <Tabs defaultValue="fields" className="h-full">
      <div className="border-b px-4">
        <TabsList className="w-full justify-start rounded-none border-b-0 p-0">
          <TabsTrigger
            value="fields"
            className="rounded-none border-b-2 border-transparent px-4 py-3 data-[state=active]:border-[#4F46E5] data-[state=active]:bg-transparent"
          >
            Fields
          </TabsTrigger>
          <TabsTrigger
            value="preview"
            className="rounded-none border-b-2 border-transparent px-4 py-3 data-[state=active]:border-[#4F46E5] data-[state=active]:bg-transparent"
          >
            Live Preview
          </TabsTrigger>
        </TabsList>
      </div>

      <TabsContent value="fields" className="h-[calc(100%-49px)] overflow-y-auto p-0">
        <div className="p-4">
          <Button
            onClick={onAddField}
            className="w-full justify-start bg-white text-[#4F46E5] hover:bg-gray-50 hover:text-[#4338CA] border border-gray-200"
          >
            <Plus className="mr-2 h-4 w-4" />
            Add Field
          </Button>
        </div>

        <div className="px-4">
          {fields.length === 0 ? (
            <div className="flex h-40 flex-col items-center justify-center rounded-md border border-dashed p-4 text-center">
              <p className="text-sm text-muted-foreground">No fields added yet</p>
              <p className="text-xs text-muted-foreground mt-1">
                Click "Add Field" or select an element in the preview
              </p>
            </div>
          ) : (
            <ul className="space-y-2">
              {fields.map((field) => (
                <li
                  key={field.id}
                  className={`rounded-md border p-3 transition-colors ${
                    selectedField === field.id
                      ? "border-[#4F46E5] bg-[#4F46E5]/5"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                  onClick={() => onSelectField(field.id)}
                >
                  <div className="flex items-center justify-between">
                    {editingField === field.id ? (
                      <div className="flex flex-1 items-center gap-2">
                        <Input
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          className="h-8"
                          autoFocus
                        />
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-green-600" onClick={handleSaveEdit}>
                          <Check className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-red-600" onClick={handleCancelEdit}>
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    ) : (
                      <>
                        <span className="font-medium">{field.name}</span>
                        <div className="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleStartEdit(field)
                            }}
                          >
                            <Pencil className="h-4 w-4" />
                            <span className="sr-only">Edit</span>
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7 text-red-600"
                            onClick={(e) => {
                              e.stopPropagation()
                              onDeleteField(field.id)
                            }}
                          >
                            <Trash2 className="h-4 w-4" />
                            <span className="sr-only">Delete</span>
                          </Button>
                        </div>
                      </>
                    )}
                  </div>
                  {field.selector && (
                    <div className="mt-2">
                      <code className="rounded bg-gray-100 px-1 py-0.5 text-xs text-gray-800">{field.selector}</code>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </TabsContent>

      <TabsContent value="preview" className="h-[calc(100%-49px)] overflow-y-auto p-4">
        {!selectedField ? (
          <div className="flex h-40 flex-col items-center justify-center rounded-md border border-dashed p-4 text-center">
            <p className="text-sm text-muted-foreground">No field selected</p>
            <p className="text-xs text-muted-foreground mt-1">Select a field to see extracted data</p>
          </div>
        ) : (
          <>
            <div className="mb-4 flex items-center justify-between">
              <h3 className="font-medium">
                Preview: <span className="text-[#4F46E5]">{currentField?.name}</span>
              </h3>
              <span className="text-xs text-muted-foreground">{currentField?.samples.length} results</span>
            </div>

            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[50px]">#</TableHead>
                    <TableHead>Value</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {currentField?.samples.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={2} className="text-center h-24 text-muted-foreground">
                        No data extracted yet
                      </TableCell>
                    </TableRow>
                  ) : (
                    currentField?.samples.map((sample, index) => (
                      <TableRow key={index}>
                        <TableCell className="font-medium">{index + 1}</TableCell>
                        <TableCell>{sample}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </>
        )}
      </TabsContent>
    </Tabs>
  )
}
