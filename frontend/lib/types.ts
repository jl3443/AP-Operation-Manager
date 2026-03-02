// ============================================================
// Enums — aligned with backend models
// ============================================================

export type InvoiceStatus =
  | "draft"
  | "extracted"
  | "matching"
  | "exception"
  | "pending_approval"
  | "approved"
  | "rejected"
  | "posted"

export type DocumentType = "invoice" | "credit_memo" | "debit_memo"

export type SourceChannel = "manual" | "email" | "api" | "csv"

export type VendorStatus = "active" | "on_hold" | "blocked"

export type RiskLevel = "low" | "medium" | "high"

export type POStatus = "open" | "partially_received" | "fully_received" | "closed" | "cancelled"

export type MatchType = "two_way" | "three_way"

export type MatchStatus =
  | "matched"
  | "partial"
  | "unmatched"
  | "tolerance_passed"

export type ExceptionType =
  | "missing_po"
  | "amount_variance"
  | "quantity_variance"
  | "duplicate_invoice"
  | "vendor_mismatch"
  | "tax_variance"
  | "expired_po"
  | "prepayment"
  | "currency_variance"
  | "contract_price_variance"
  | "vendor_on_hold"
  | "partial_delivery_overrun"

export type ExceptionSeverity = "low" | "medium" | "high" | "critical"

export type ExceptionStatus =
  | "open"
  | "assigned"
  | "in_progress"
  | "resolved"
  | "escalated"

export type ResolutionType =
  | "auto_resolved"
  | "manual_override"
  | "vendor_credit"
  | "po_amendment"
  | "tolerance_applied"
  | "rejected"

export type ApprovalStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "escalated"
  | "timed_out"

export type AIRecommendation = "approve" | "reject" | "review"

export type ActorType = "user" | "system" | "ai_agent"

export type UserRole =
  | "ap_clerk"
  | "ap_analyst"
  | "approver"
  | "admin"
  | "auditor"

// ============================================================
// Core Models — aligned with backend schemas
// ============================================================

export interface Invoice {
  id: string
  invoice_number: string
  vendor_id: string
  vendor?: Vendor
  invoice_date: string
  due_date: string
  received_date?: string
  currency: string
  total_amount: number
  tax_amount: number
  freight_amount: number
  discount_amount: number
  status: InvoiceStatus
  document_type: DocumentType
  source_channel: SourceChannel
  file_storage_path?: string
  ocr_confidence_score?: number
  line_items: InvoiceLineItem[]
  created_at: string
  updated_at: string
}

export interface InvoiceLineItem {
  id: string
  invoice_id: string
  line_number: number
  description: string
  quantity: number
  unit_price: number
  line_total: number
  po_line_id?: string
  gl_account_id?: string
  cost_center_id?: string
  tax_code?: string
  tax_amount: number
  ai_gl_prediction?: string
  ai_confidence?: number
}

export interface Vendor {
  id: string
  vendor_code: string
  name: string
  tax_id?: string
  address?: string
  city?: string
  state?: string
  country?: string
  payment_terms_code?: string
  bank_account_info?: Record<string, unknown>
  status: VendorStatus
  risk_level: RiskLevel
  created_at: string
  updated_at: string
}

export interface PurchaseOrder {
  id: string
  po_number: string
  vendor_id: string
  vendor?: Vendor
  order_date: string
  delivery_date?: string
  total_amount: number
  currency: string
  status: POStatus
  line_items: POLineItem[]
  created_at: string
  updated_at: string
}

export interface POLineItem {
  id: string
  po_id: string
  line_number: number
  description: string
  quantity_ordered: number
  unit_price: number
  line_total: number
  quantity_received: number
  quantity_invoiced: number
}

export interface GoodsReceipt {
  id: string
  grn_number: string
  po_id: string
  vendor_id: string
  vendor?: Vendor
  receipt_date: string
  warehouse?: string
  line_items: GRNLineItem[]
  created_at: string
  updated_at: string
}

export interface GRNLineItem {
  id: string
  grn_id: string
  po_line_id: string
  quantity_received: number
  condition_notes?: string
}

export interface MatchResult {
  id: string
  invoice_id: string
  match_type: MatchType
  match_status: MatchStatus
  overall_score: number
  details?: Record<string, unknown>
  matched_po_id?: string
  matched_grn_ids?: string[]
  tolerance_applied: boolean
  tolerance_config_id?: string
  created_at: string
}

export interface Exception_ {
  id: string
  invoice_id: string
  exception_type: ExceptionType
  severity: ExceptionSeverity
  status: ExceptionStatus
  assigned_to?: string
  resolution_type?: ResolutionType
  resolution_notes?: string
  resolved_at?: string
  resolved_by?: string
  ai_suggested_resolution?: string
  ai_severity_reasoning?: string
  comments: ExceptionComment[]
  created_at: string
  updated_at: string
}

export interface ExceptionComment {
  id: string
  exception_id: string
  user_id: string
  comment_text: string
  mentions?: string[]
  created_at: string
}

export interface ApprovalTask {
  id: string
  invoice_id: string
  approver_id: string
  approval_level: number
  approval_order: number
  status: ApprovalStatus
  ai_recommendation?: AIRecommendation
  ai_recommendation_reason?: string
  decision_at?: string
  comments?: string
  created_at: string
  updated_at: string
}

export interface AuditLog {
  id: string
  timestamp: string
  entity_type: string
  entity_id: string
  action: string
  actor_type: ActorType
  actor_id?: string
  actor_name?: string
  changes?: Record<string, unknown>
  evidence?: Record<string, unknown>
}

export interface User {
  id: string
  email: string
  name: string
  role: UserRole
  department?: string
  cost_center_id?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

// ============================================================
// Dashboard / Analytics — aligned with backend schemas
// ============================================================

export interface DashboardKPI {
  total_invoices: number
  pending_approval: number
  open_exceptions: number
  total_amount_pending: number
  avg_processing_time_hours: number
  match_rate_pct: number
  straight_through_rate_pct: number
  overdue_invoices: number
}

export interface FunnelStage {
  stage: string
  count: number
  amount: number
}

export interface FunnelData {
  stages: FunnelStage[]
}

export interface TrendPoint {
  date: string
  value: number
  label?: string
}

export interface TrendData {
  series_name: string
  data_points: TrendPoint[]
}

export interface VendorSummary {
  vendor_id: string
  vendor_name: string
  invoice_count: number
  total_amount: number
  exception_count: number
  avg_processing_days: number
}

export interface AgingBucket {
  bucket: string
  count: number
  amount: number
}

export interface AgingData {
  buckets: AgingBucket[]
}

export interface ExceptionBreakdown {
  exception_type: string
  count: number
  percentage: number
}

export interface VendorRiskDistribution {
  risk_level: string
  count: number
  percentage: number
}

export interface MonthlyComparison {
  month: string
  invoice_count: number
  total_amount: number
}

export interface ApprovalTurnaround {
  level: number
  avg_hours: number
  total_tasks: number
}

// ============================================================
// API Response Wrapper
// ============================================================

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ApiError {
  detail: string
  status_code: number
}

// ============================================================
// Import / Upload
// ============================================================

export interface ImportJob {
  id: string
  import_type: "purchase_orders" | "goods_receipts" | "vendors"
  status: "pending" | "processing" | "completed" | "failed"
  total_records: number
  imported_records: number
  failed_records: number
  error_details?: string
  created_at: string
  completed_at?: string
}

// ============================================================
// Notification
// ============================================================

export interface Notification {
  id: string
  user_id: string
  title: string
  message: string
  type: string
  related_entity_type?: string
  related_entity_id?: string
  is_read: boolean
  created_at: string
}

// ============================================================
// AI Chat
// ============================================================

export interface AIChatMessage {
  role: "user" | "assistant"
  content: string
  timestamp: string
}

export interface AIChatResponse {
  response: string
  conversation_id: string
}

// ============================================================
// Compliance & Optimization types
// ============================================================

export interface TouchlessRate {
  rate: number
  total_invoices: number
  touchless_count: number
  cycle_time_avg_hours: number
}

export interface ControlMapping {
  control_id: string
  control_name: string
  policy_section: string
  description: string
  implementation_status: "active" | "partial" | "planned"
  automated: boolean
  last_tested: string
  test_result: "pass" | "fail" | "not_tested"
}

export interface ComplianceGap {
  gap_id: string
  control_id: string
  finding: string
  severity: "high" | "medium" | "low"
  status: "open" | "remediation" | "closed"
  recommendation: string
  evidence_count: number
}

export interface RootCauseItem {
  category: string
  issue: string
  occurrence_count: number
  affected_invoices: number
  impact_amount: number
  suggested_fix: string
}

export interface OptimizationProposal {
  id: string
  title: string
  description: string
  category: string
  priority: "high" | "medium" | "low"
  projected_impact: string
  effort: "low" | "medium" | "high"
  status: "proposed" | "approved" | "implemented"
}
