"use client"

import * as React from "react"
import Link from "next/link"
import { Upload, FileText, X, CheckCircle, Loader2, ArrowLeft } from "lucide-react"
import { toast } from "sonner"

import { PageHeader } from "@/components/page-header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"

interface UploadFile {
  id: string
  name: string
  size: number
  progress: number
  status: "uploading" | "processing" | "complete" | "error"
}

export default function InvoiceUploadPage() {
  const [files, setFiles] = React.useState<UploadFile[]>([])
  const [isDragging, setIsDragging] = React.useState(false)
  const fileInputRef = React.useRef<HTMLInputElement>(null)

  function handleFiles(fileList: FileList) {
    const newFiles: UploadFile[] = Array.from(fileList).map((file, i) => ({
      id: `${Date.now()}-${i}`,
      name: file.name,
      size: file.size,
      progress: 0,
      status: "uploading" as const,
    }))
    setFiles((prev) => [...prev, ...newFiles])

    // Simulate upload progress
    newFiles.forEach((file) => {
      let progress = 0
      const interval = setInterval(() => {
        progress += Math.random() * 25
        if (progress >= 100) {
          progress = 100
          clearInterval(interval)
          setFiles((prev) =>
            prev.map((f) =>
              f.id === file.id ? { ...f, progress: 100, status: "processing" } : f,
            ),
          )
          // Simulate processing
          setTimeout(() => {
            setFiles((prev) =>
              prev.map((f) =>
                f.id === file.id ? { ...f, status: "complete" } : f,
              ),
            )
          }, 1500)
        } else {
          setFiles((prev) =>
            prev.map((f) =>
              f.id === file.id ? { ...f, progress } : f,
            ),
          )
        }
      }, 300)
    })
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files)
    }
  }

  function removeFile(id: string) {
    setFiles((prev) => prev.filter((f) => f.id !== id))
  }

  function formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1048576).toFixed(1)} MB`
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Upload Invoices"
        description="Upload invoice documents for AI extraction and processing"
      >
        <Button variant="outline" size="sm" asChild>
          <Link href="/invoices">
            <ArrowLeft className="size-4" />
            Back to Invoices
          </Link>
        </Button>
      </PageHeader>

      {/* Drop Zone */}
      <Card>
        <CardContent className="p-0">
          <div
            className={`
              flex flex-col items-center justify-center gap-4 rounded-xl border-2 border-dashed p-12
              transition-colors cursor-pointer
              ${isDragging
                ? "border-primary bg-primary/5"
                : "border-border hover:border-primary/50 hover:bg-secondary/30"
              }
            `}
            onDragOver={(e) => {
              e.preventDefault()
              setIsDragging(true)
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <div className="rounded-full bg-primary/10 p-4">
              <Upload className="size-8 text-primary" />
            </div>
            <div className="text-center">
              <p className="text-lg font-medium">
                Drag & drop your invoices here
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                or click to browse files
              </p>
            </div>
            <p className="text-xs text-muted-foreground">
              Supported formats: PDF, PNG, JPG (max 25MB per file)
            </p>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.png,.jpg,.jpeg"
              className="hidden"
              onChange={(e) => e.target.files && handleFiles(e.target.files)}
            />
          </div>
        </CardContent>
      </Card>

      {/* File List */}
      {files.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Upload Queue</CardTitle>
            <CardDescription>
              {files.filter((f) => f.status === "complete").length} of {files.length} files
              processed
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {files.map((file) => (
              <div
                key={file.id}
                className="flex items-center gap-3 rounded-lg border p-3"
              >
                <div className="rounded-lg bg-primary/10 p-2">
                  <FileText className="size-4 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium truncate">{file.name}</p>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-xs text-muted-foreground">
                        {formatFileSize(file.size)}
                      </span>
                      {file.status === "complete" && (
                        <CheckCircle className="size-4 text-green-600" />
                      )}
                      {file.status === "processing" && (
                        <Loader2 className="size-4 text-primary animate-spin" />
                      )}
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        className="size-6"
                        onClick={(e) => {
                          e.stopPropagation()
                          removeFile(file.id)
                        }}
                      >
                        <X className="size-3" />
                      </Button>
                    </div>
                  </div>
                  {file.status === "uploading" && (
                    <Progress value={file.progress} className="h-1.5 mt-2" />
                  )}
                  {file.status === "processing" && (
                    <p className="text-xs text-muted-foreground mt-1">
                      AI extracting data...
                    </p>
                  )}
                  {file.status === "complete" && (
                    <p className="text-xs text-green-600 mt-1">
                      Extraction complete
                    </p>
                  )}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Upload Action */}
      {files.length > 0 && (
        <div className="flex justify-end gap-3">
          <Button
            variant="outline"
            onClick={() => setFiles([])}
          >
            Clear All
          </Button>
          <Button
            onClick={() => toast.success("Invoices uploaded and queued for processing!")}
            disabled={files.some((f) => f.status === "uploading")}
          >
            <Upload className="size-4" />
            Upload & Extract
          </Button>
        </div>
      )}
    </div>
  )
}
