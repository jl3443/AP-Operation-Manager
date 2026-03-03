"use client"

import * as React from "react"
import {
  Layers,
  Workflow,
  Code2,
  Database,
  Brain,
  CheckCircle2,
  ArrowDown,
  Cpu,
  Globe,
  Server,
  Sparkles,
  BarChart3,
} from "lucide-react"

import {
  useArchitecture,
  useDataFlow,
  useApiContracts,
  useSystemStats,
} from "@/hooks/use-system-design"
import { KpiCardSkeleton, TableSkeleton } from "@/components/loading-skeleton"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const layerColors = [
  "border-l-blue-500 bg-blue-50/50 dark:bg-blue-950/20",
  "border-l-emerald-500 bg-emerald-50/50 dark:bg-emerald-950/20",
  "border-l-violet-500 bg-violet-50/50 dark:bg-violet-950/20",
  "border-l-amber-500 bg-amber-50/50 dark:bg-amber-950/20",
  "border-l-rose-500 bg-rose-50/50 dark:bg-rose-950/20",
]

const layerIcons = [Globe, Server, Cpu, Brain, Database]

const actColors: Record<string, string> = {
  complete: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400",
  partial: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  planned: "bg-slate-100 text-slate-800 dark:bg-slate-900/30 dark:text-slate-400",
}

const methodColors: Record<string, string> = {
  GET: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  POST: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400",
  PATCH: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  PUT: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400",
  DELETE: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
}

export default function SystemDesignPage() {
  const { data: arch, isLoading: archLoading } = useArchitecture()
  const { data: flow, isLoading: flowLoading } = useDataFlow()
  const { data: api, isLoading: apiLoading } = useApiContracts()
  const { data: stats, isLoading: statsLoading } = useSystemStats()

  if (archLoading) {
    return (
      <div className="space-y-6">
        <p className="text-muted-foreground">Loading system design...</p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => <KpiCardSkeleton key={i} />)}
        </div>
        <TableSkeleton rows={6} cols={4} />
      </div>
    )
  }

  const totalEndpoints = api?.modules.reduce((sum, m) => sum + m.endpoints.length, 0) ?? 0

  return (
    <div className="space-y-6">
      <p className="text-muted-foreground">
        AI-generated system architecture — how the 6-ACT framework was implemented end-to-end.
      </p>

      {/* Stats Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Architecture</p>
                <p className="text-2xl font-bold">{arch?.layers.length ?? 0} Layers</p>
              </div>
              <Layers className="size-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Pipeline</p>
                <p className="text-2xl font-bold">{flow?.pipeline.length ?? 0} Steps</p>
              </div>
              <Workflow className="size-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">API Endpoints</p>
                <p className="text-2xl font-bold">{totalEndpoints}</p>
              </div>
              <Code2 className="size-8 text-violet-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">DB Records</p>
                <p className="text-2xl font-bold">
                  {stats ? Object.values(stats.database).reduce((a, b) => a + b, 0) : 0}
                </p>
              </div>
              <Database className="size-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="six-acts" className="space-y-4">
        <TabsList>
          <TabsTrigger value="six-acts">6-ACT Framework</TabsTrigger>
          <TabsTrigger value="architecture">Architecture</TabsTrigger>
          <TabsTrigger value="pipeline">Data Pipeline</TabsTrigger>
          <TabsTrigger value="api">API Contracts</TabsTrigger>
          <TabsTrigger value="tech">Tech Stack</TabsTrigger>
        </TabsList>

        {/* Tab: 6-ACT Framework */}
        <TabsContent value="six-acts">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="size-5" />
                6-ACT AP Automation Framework
              </CardTitle>
              <CardDescription>
                Complete implementation status of each ACT in the framework
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {arch?.six_acts.map((act) => (
                  <div key={act.act} className="border rounded-lg p-5 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="size-10 rounded-full bg-violet-100 dark:bg-violet-900/30 flex items-center justify-center text-lg font-bold text-violet-600 dark:text-violet-400">
                          {act.act}
                        </div>
                        <div>
                          <h3 className="font-semibold text-base">{act.name}</h3>
                          <p className="text-sm text-muted-foreground">{act.description}</p>
                        </div>
                      </div>
                      <Badge variant="secondary" className={actColors[act.status]}>
                        {act.status}
                      </Badge>
                    </div>
                    <div className="grid gap-2 sm:grid-cols-2 pl-[52px]">
                      {act.features.map((feat, i) => (
                        <div key={i} className="flex items-start gap-2 text-sm">
                          <CheckCircle2 className="size-4 shrink-0 mt-0.5 text-emerald-500" />
                          <span>{feat}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Architecture */}
        <TabsContent value="architecture">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Layers className="size-5" />
                Layered Architecture
              </CardTitle>
              <CardDescription>
                {arch?.name} v{arch?.version} — {arch?.framework}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {arch?.layers.map((layer, i) => {
                  const Icon = layerIcons[i] || Layers
                  return (
                    <div
                      key={layer.name}
                      className={`border-l-4 rounded-lg p-4 space-y-2 ${layerColors[i]}`}
                    >
                      <div className="flex items-center gap-3">
                        <Icon className="size-5 shrink-0" />
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <h4 className="font-semibold">{layer.name}</h4>
                            <Badge variant="outline" className="font-mono text-xs">
                              {layer.tech}
                            </Badge>
                          </div>
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2 pl-8">
                        {layer.components.map((comp, j) => (
                          <Badge key={j} variant="secondary" className="text-xs">
                            {comp}
                          </Badge>
                        ))}
                      </div>
                      {i < (arch?.layers.length ?? 0) - 1 && (
                        <div className="flex justify-center pt-1">
                          <ArrowDown className="size-4 text-muted-foreground" />
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Data Pipeline */}
        <TabsContent value="pipeline">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Workflow className="size-5" />
                Invoice Processing Pipeline
              </CardTitle>
              <CardDescription>
                End-to-end data flow from invoice ingestion to payment and learning
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {flow?.pipeline.map((step, i) => (
                  <React.Fragment key={step.step}>
                    <div className="border rounded-lg p-4 space-y-2">
                      <div className="flex items-center gap-3">
                        <div className="size-8 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center text-sm font-bold text-emerald-600 dark:text-emerald-400">
                          {step.step}
                        </div>
                        <div className="flex-1">
                          <h4 className="font-semibold">{step.name}</h4>
                          <p className="text-sm text-muted-foreground">{step.description}</p>
                        </div>
                      </div>
                      <div className="pl-11 space-y-1.5">
                        <div className="flex items-start gap-2 text-sm">
                          <Brain className="size-4 shrink-0 mt-0.5 text-violet-500" />
                          <span className="text-violet-600 dark:text-violet-400">{step.ai_role}</span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {step.outputs.map((out, j) => (
                            <Badge key={j} variant="outline" className="text-xs">
                              {out}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                    {i < (flow?.pipeline.length ?? 0) - 1 && (
                      <div className="flex justify-center">
                        <ArrowDown className="size-4 text-muted-foreground" />
                      </div>
                    )}
                  </React.Fragment>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: API Contracts */}
        <TabsContent value="api">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Code2 className="size-5" />
                API Contract Documentation
              </CardTitle>
              <CardDescription>
                {api?.base_url} | Auth: {api?.auth} | {totalEndpoints} endpoints across {api?.modules.length} modules
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {api?.modules.map((mod) => (
                  <div key={mod.name} className="space-y-2">
                    <div className="flex items-center gap-2">
                      <h4 className="font-semibold text-sm">{mod.name}</h4>
                      <Badge variant="outline" className="font-mono text-xs">{mod.prefix}</Badge>
                    </div>
                    <Table>
                      <TableBody>
                        {mod.endpoints.map((ep, i) => (
                          <TableRow key={i}>
                            <TableCell className="w-20">
                              <Badge variant="secondary" className={`font-mono text-xs ${methodColors[ep.method]}`}>
                                {ep.method}
                              </Badge>
                            </TableCell>
                            <TableCell className="font-mono text-sm">{mod.prefix}{ep.path}</TableCell>
                            <TableCell className="text-sm text-muted-foreground">{ep.description}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Tech Stack */}
        <TabsContent value="tech">
          <div className="grid gap-4 sm:grid-cols-2">
            {stats?.tech_stack &&
              Object.entries(stats.tech_stack).map(([category, techs]) => (
                <Card key={category}>
                  <CardHeader>
                    <CardTitle className="text-base capitalize">{category}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {(techs as string[]).map((tech, i) => (
                        <Badge key={i} variant="secondary" className="text-sm px-3 py-1">
                          {tech}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}

            {/* Database Stats */}
            {stats?.database && (
              <Card className="sm:col-span-2">
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Database className="size-4" />
                    Live Database Statistics
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-3 sm:grid-cols-4">
                    {Object.entries(stats.database).map(([table, count]) => (
                      <div key={table} className="border rounded-lg p-3 text-center">
                        <p className="text-2xl font-bold">{count}</p>
                        <p className="text-xs text-muted-foreground capitalize">
                          {table.replace(/_/g, " ")}
                        </p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
