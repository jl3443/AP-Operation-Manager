"use client"

import * as React from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import {
  Upload,
  FileText,
  X,
  CheckCircle,
  Loader2,
  ArrowLeft,
  AlertCircle,
} from "lucide-react"

import { PageHeader } from "@/components/page-header"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card"
import { useUploadInvoiceFile } from "@/hooks/use-invoices"

type FileStatus = "pending" | "uploading" | "uploaded" | "error"

interface UploadFile {
  id: string
  file: File
  name: string
  size: number
  status: FileStatus
  invoiceId?: string
  errorMessage?: string
}

export default function InvoiceUploadPage() {
  const router = useRouter()
  const [files, setFiles] = React.useState<UploadFile[]>([])
  const [isDragging, setIsDragging] = React.useState(false)
  const fileInputRef = React.useRef<HTMLInputElement>(null)

  const uploadMutation = useUploadInvoiceFile()

  // Auto-redirect to pipeline as soon as first file is uploaded successfully
  React.useEffect(() => {
    const firstUploaded = files.find((f) => f.status === "uploaded" && f.invoiceId)
    if (firstUploaded?.invoiceId) {
      router.push(`/invoices/${firstUploaded.invoiceId}/pipeline`)
    }
  }, [files, router])

  function updateFile(id: string, updates: Partial<UploadFile>) {
    setFiles((prev) =>
      prev.map((f) => (f.id === id ? { ...f, ...updates } : f)),
    )
  }

  async function uploadSingleFile(uploadFile: UploadFile) {
    updateFile(uploadFile.id, { status: "uploading" })

    try {
      const invoice = await uploadMutation.mutateAsync({
        file: uploadFile.file,
      })
      updateFile(uploadFile.id, {
        status: "uploaded",
        invoiceId: invoice.id,
      })
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Upload failed"
      updateFile(uploadFile.id, {
        status: "error",
        errorMessage: message,
      })
    }
  }

  async function handleFiles(fileList: FileList) {
    const newFiles: UploadFile[] = Array.from(fileList).map((file, i) => ({
      id: `${Date.now()}-${i}`,
      file,
      name: file.name,
      size: file.size,
      status: "pending" as const,
    }))

    setFiles((prev) => [...prev, ...newFiles])

    for (const file of newFiles) {
      await uploadSingleFile(file)
    }
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

  const uploadedCount = files.filter((f) => f.status === "uploaded").length
  const hasActiveUploads = files.some((f) => f.status === "uploading")

  return (
    <div className="space-y-6">
      <PageHeader
        title="Upload Invoices"
        description="Upload invoice documents — AI will extract data, match the vendor, and run the full pipeline"
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
              onChange={(e) => {
                if (e.target.files) handleFiles(e.target.files)
                e.target.value = ""
              }}
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
              {uploadedCount} of {files.length} files uploaded — redirecting to pipeline automatically
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {files.map((file) => (
              <div key={file.id} className="rounded-lg border">
                <div className="flex items-center gap-3 p-3">
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
                        {file.status === "uploading" && (
                          <Loader2 className="size-4 text-primary animate-spin" />
                        )}
                        {file.status === "uploaded" && (
                          <CheckCircle className="size-4 text-green-600" />
                        )}
                        {file.status === "error" && (
                          <AlertCircle className="size-4 text-destructive" />
                        )}
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          className="size-6"
                          onClick={(e) => {
                            e.stopPropagation()
                            removeFile(file.id)
                          }}
                          disabled={file.status === "uploading"}
                        >
                          <X className="size-3" />
                        </Button>
                      </div>
                    </div>
                    {file.status === "pending" && (
                      <p className="text-xs text-muted-foreground mt-1">Waiting to upload...</p>
                    )}
                    {file.status === "uploading" && (
                      <p className="text-xs text-muted-foreground mt-1">Uploading to server...</p>
                    )}
                    {file.status === "uploaded" && (
                      <p className="text-xs text-green-600 mt-1">
                        Uploaded — launching Agent Pipeline…
                      </p>
                    )}
                    {file.status === "error" && (
                      <p className="text-xs text-destructive mt-1">
                        {file.errorMessage ?? "An error occurred"}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Actions */}
      {files.length > 0 && (
        <div className="flex justify-end gap-3">
          <Button
            variant="outline"
            onClick={() => setFiles([])}
            disabled={hasActiveUploads}
          >
            Clear All
          </Button>
        </div>
      )}
    </div>
  )
}
