import { AlertTriangle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"

export function QueryError({
  error,
  retry,
}: {
  error: Error
  retry?: () => void
}) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center justify-center py-12 text-center">
        <AlertTriangle className="size-8 text-destructive mb-3" />
        <p className="text-sm font-medium">Something went wrong</p>
        <p className="text-xs text-muted-foreground mt-1">{error.message}</p>
        {retry && (
          <Button variant="outline" size="sm" className="mt-4" onClick={retry}>
            Try Again
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
