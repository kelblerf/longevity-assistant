export const SOURCE_GROUPS = [
  "profile",
  "app_health_data",
  "app_genetics_data",
  "app_nutrition_data",
  "notion_structured",
  "notion_extended",
  "onenote_reflection",
  "local_files",
  "external_drive_files",
  "ubz_framework",
  "notebooklm_research",
  "web_evidence",
  "model_interpretation",
] as const;

export type SourceGroup = (typeof SOURCE_GROUPS)[number];

export type SourceScopeMode =
  | "core_only"
  | "core_plus_domain"
  | "core_plus_extended"
  | "full_research";

export interface SourceScopeSelection {
  mode: SourceScopeMode;
  groups: SourceGroup[];
  locked: boolean;
  reason?: string | null;
}

export interface CareRecommendation {
  id: string;
  title: string;
  source: string;
  category: string;
  priority: string;
  recommendation: string;
  activeFrom?: string | null;
  reviewFrequency?: string | null;
  nextDue?: string | null;
  relatedMarkers: string[];
  notes?: string | null;
  status: string;
}

export interface CreateCareRecommendationInput {
  title: string;
  source: string;
  category: string;
  priority: string;
  recommendation: string;
  activeFrom?: string | null;
  reviewFrequency?: string | null;
  nextDue?: string | null;
  relatedMarkers?: string[];
  notes?: string | null;
}

export interface RoutineStep {
  id: string;
  title: string;
  purpose: string;
  durationLabel: string;
  required: boolean;
  fallback?: string | null;
}

export interface RoutineDefinition {
  id: string;
  title: string;
  category: string;
  goal: string;
  timing: string;
  variants: string[];
  steps: RoutineStep[];
}

export interface MovementBlock {
  id: string;
  title: string;
  area: string;
  frequency: string;
  durationLabel: string;
  benefit: string;
  caution?: string | null;
  examples: string[];
  minimumVariant: string[];
  fullVariant: string[];
  sequenceSteps: string[];
}

export interface UserProfile {
  id: string;
  displayName: string;
  ageGroup: string;
  healthGoals: string[];
  constraints: string[];
  preferences: string[];
  trustedSources: string[];
  guidanceStyle?: string;
  dailyRhythm?: string | null;
  dnaUsagePolicy?: string;
}

export interface AssistantRules {
  profileId: string;
  assistantIdentity: string;
  voiceMode: "text_first" | "voice_optional";
  sourceScopeDefault: SourceScopeMode;
  ubzPriority: "primary_behavioral_layer";
  notebookLmRole: "evidence_research_layer";
  dnaPolicy: "recommendation_only";
  warningTone: "calm_explanatory";
}

export interface Conversation {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
}

export interface ChatMessage {
  id: string;
  conversationId: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
}

export interface AssistantAnswerSection {
  kind:
    | "profile_context"
    | "workflow_context"
    | "biomarker_insight"
    | "food_biomarker_context"
    | "care_biomarker_context"
    | "dna_biomarker_context"
    | "routine_basis"
    | "evidence_basis"
    | "ubz_basis"
    | "ubz_context"
    | "dna_signal"
    | "extended_context"
    | "model_interpretation";
  title: string;
  content: string;
}

export interface AssistantAnswerSource {
  label: string;
  type: SourceGroup | string;
  reference?: string | null;
  authorityTier: string;
}

export interface AssistantAnswer {
  summary: string;
  selectedScope: SourceScopeSelection;
  sections: AssistantAnswerSection[];
  nextSteps: string[];
  sources: AssistantAnswerSource[];
}

export interface UzbKnowledgeHit {
  id: string;
  title: string;
  notionPath: string;
  summary: string;
  guidance: string;
  themes: string[];
  score: number;
  excerpt?: string | null;
  sourceMode: "seed" | "notion_live" | string;
  notionPageId?: string | null;
  authorityTier: string;
}

export interface UzbKnowledgeSearchResponse {
  query: string;
  hits: UzbKnowledgeHit[];
}

export interface UzbKnowledgeSyncItem {
  id: string;
  title: string;
  notionPath: string;
  notionPageId?: string | null;
  synced: boolean;
  sourceMode: "seed" | "notion_live" | string;
  excerpt?: string | null;
  error?: string | null;
  authorityTier: string;
}

export interface UzbKnowledgeSyncResponse {
  syncedAt: string;
  syncedCount: number;
  items: UzbKnowledgeSyncItem[];
}

export interface EvidenceKnowledgeHit {
  id: string;
  title: string;
  notionPath: string;
  summary: string;
  guidance: string;
  themes: string[];
  score: number;
  excerpt?: string | null;
  sourceMode: "seed" | "notion_live" | string;
  notionPageId?: string | null;
  authorityTier: string;
}

export interface EvidenceKnowledgeSearchResponse {
  query: string;
  hits: EvidenceKnowledgeHit[];
}

export interface EvidenceKnowledgeSyncItem {
  id: string;
  title: string;
  notionPath: string;
  notionPageId?: string | null;
  synced: boolean;
  sourceMode: "seed" | "notion_live" | string;
  excerpt?: string | null;
  error?: string | null;
  authorityTier: string;
}

export interface EvidenceKnowledgeSyncResponse {
  syncedAt: string;
  syncedCount: number;
  items: EvidenceKnowledgeSyncItem[];
}

export interface CreateConversationInput {
  title?: string;
}

export interface ChatRespondInput {
  conversationId: string;
  message: string;
}

export interface ChatRespondOutput {
  conversation: Conversation;
  userMessage: ChatMessage;
  assistantMessage: ChatMessage;
  answer: AssistantAnswer;
}

export interface MealEntry {
  id: string;
  mealType: string;
  title: string;
  notes?: string | null;
  tags: string[];
  occurredAt: string;
}

export interface CreateMealEntryInput {
  mealType: string;
  title: string;
  notes?: string | null;
  tags?: string[];
  occurredAt?: string | null;
}

export interface HealthSignal {
  id: string;
  category: string;
  title: string;
  severity: "low" | "medium" | "high";
  notes?: string | null;
  observedAt: string;
}

export interface CreateHealthSignalInput {
  category: string;
  title: string;
  severity: "low" | "medium" | "high";
  notes?: string | null;
  observedAt?: string | null;
}

export interface DailyCheckIn {
  id: string;
  checkInType: "morning" | "evening";
  energy: number;
  stress: number;
  sleepQuality: number;
  notes?: string | null;
  createdAt: string;
}

export interface CreateDailyCheckInInput {
  checkInType: "morning" | "evening";
  energy: number;
  stress: number;
  sleepQuality: number;
  notes?: string | null;
  createdAt?: string | null;
}

export interface GeneticMarker {
  id: string;
  key: string;
  label: string;
  category: string;
  genotype?: string | null;
  interpretation: string;
  recommendationStrength: string;
  confidence: string;
  sourceRef?: string | null;
  relatedDomains: string[];
}

export interface GeneticProfile {
  id: string;
  sourceType: string;
  sourceLabel: string;
  importedAt: string;
  summary: string;
  markers: GeneticMarker[];
}

export interface UpsertGeneticProfileInput {
  sourceType: string;
  sourceLabel: string;
  summary: string;
  markers: GeneticMarker[];
}

export interface GeneticImportDraftInput {
  sourceType: string;
  sourceLabel: string;
  rawText: string;
}

export interface GeneticImportDraft {
  sourceType: string;
  sourceLabel: string;
  summary: string;
  markers: GeneticMarker[];
  unresolvedNotes: string[];
}

export interface BiomarkerReport {
  id: string;
  profileId: string;
  sourceType: string;
  sourceLabel: string;
  sourceRef?: string | null;
  labName?: string | null;
  collectedAt?: string | null;
  reportedAt?: string | null;
  fastingState: "fasting" | "non_fasting" | "unknown" | string;
  notes?: string | null;
  rawText?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface BiomarkerObservation {
  id: string;
  reportId: string;
  markerKey: string;
  markerLabel: string;
  category: string;
  value?: number | null;
  unit?: string | null;
  comparator: "exact" | "lt" | "lte" | "gt" | "gte" | string;
  referenceLow?: number | null;
  referenceHigh?: number | null;
  referenceText?: string | null;
  status: "low" | "optimal" | "high" | "out_of_range" | "unknown" | string;
  measurementContext: "fasting" | "non_fasting" | "supplementing" | "unknown" | string;
  observedAt: string;
  sourceLine?: string | null;
  confidence: "manual_confirmed" | "parsed_high" | "parsed_medium" | "parsed_low" | string;
}

export interface BiomarkerMarkerDefinition {
  key: string;
  label: string;
  category: string;
  defaultUnit?: string | null;
  aliases: string[];
  canonicalSource?: string | null;
  description?: string | null;
}

export interface BiomarkerTrendSnapshot {
  markerKey: string;
  latestValue?: number | null;
  latestUnit?: string | null;
  latestObservedAt?: string | null;
  previousValue?: number | null;
  deltaAbsolute?: number | null;
  deltaPercent?: number | null;
  trendDirection: "up" | "down" | "stable" | "unknown" | string;
  sampleCount: number;
}

export interface BiomarkerPriorityMarker {
  markerKey: string;
  title: string;
  category: string;
  priorityRank: number;
  whyItMatters: string;
  watchFor: string[];
  linkWith: string[];
  alertWhen: string[];
}

export interface BiomarkerPriorityConfig {
  markers: BiomarkerPriorityMarker[];
}

export interface GeneticPriorityMarker {
  markerKey: string;
  title: string;
  category: string;
  priorityRank: number;
  whyItMatters: string;
  watchFor: string[];
  linkWith: string[];
  alertWhen: string[];
  confidence: string;
  recommendationStrength: string;
  genotype?: string | null;
  interpretation: string;
}

export interface GeneticPriorityConfig {
  markers: GeneticPriorityMarker[];
}

export interface BiomarkerImportDraftInput {
  sourceType: string;
  sourceLabel: string;
  rawText: string;
  profileId?: string;
}

export interface BiomarkerImportDraft {
  report: BiomarkerReport;
  observations: BiomarkerObservation[];
  unresolvedNotes: string[];
}

export interface FollowUpSuggestion {
  id: string;
  triggerType: "meal" | "health_signal" | "daily_check_in" | "care_recommendation";
  relatedId: string;
  title: string;
  message: string;
  delayLabel: string;
  suggestedAt: string;
  dueAt: string;
  status: "pending" | "done";
}

export interface DailyBriefing {
  generatedAt: string;
  headline: string;
  summary: string;
  priorities: string[];
  dueTodayCount: number;
  dueNowCount: number;
  latestCheckInType?: string | null;
  latestCheckInEnergy?: number | null;
  flaggedBiomarkerCount: number;
  biomarkerHighlights: string[];
  activeCareRecommendationCount: number;
  careHighlights: string[];
  routineHighlights: string[];
  movementHighlights: string[];
  movementGuardrails: string[];
}

export interface NotionSyncResult {
  sourceType:
    | "daily_check_ins"
    | "health_signals"
    | "follow_ups"
    | "daily_summary"
    | "care_recommendations"
    | "biomarker_reports"
    | "biomarker_trends"
    | "genetic_profile"
    | "genetic_markers";
  syncedCount: number;
  attemptedCount: number;
  createdCount: number;
  updatedCount: number;
  skippedCount: number;
  outboxPath: string;
  databaseLabel: string;
  mode: "outbox" | "direct";
  deliveryState: "queued" | "synced" | "failed" | string;
  syncedIds: string[];
  syncedAt: string;
  errorMessage?: string | null;
}

export interface NotionSyncSourceState {
  sourceType:
    | "daily_check_ins"
    | "health_signals"
    | "follow_ups"
    | "daily_summary"
    | "care_recommendations"
    | "biomarker_reports"
    | "biomarker_trends"
    | "genetic_profile"
    | "genetic_markers";
  mode: "outbox" | "direct" | string;
  deliveryState: "idle" | "queued" | "synced" | "failed" | string;
  syncedCount: number;
  attemptCount: number;
  failureCount: number;
  consecutiveFailures: number;
  lastAttemptAt?: string | null;
  lastSuccessAt?: string | null;
  lastError?: string | null;
}

export interface NotionSyncStatus {
  availableSources: string[];
  lastSyncAt?: string | null;
  syncCounts: Record<string, number>;
  outboxDir: string;
  sourceStates: Record<string, NotionSyncSourceState>;
}

export interface NotionSyncHistoryEntry {
  sourceType:
    | "daily_check_ins"
    | "health_signals"
    | "follow_ups"
    | "daily_summary"
    | "care_recommendations"
    | "biomarker_reports"
    | "biomarker_trends"
    | "genetic_profile"
    | "genetic_markers";
  syncedCount: number;
  attemptedCount: number;
  createdCount: number;
  updatedCount: number;
  skippedCount: number;
  outboxPath: string;
  syncedAt: string;
  mode: "outbox" | "direct";
  deliveryState: "queued" | "synced" | "failed" | string;
  attemptNumber: number;
  errorMessage?: string | null;
}

export interface NotionMappingPreview {
  sourceType:
    | "daily_check_ins"
    | "health_signals"
    | "follow_ups"
    | "daily_summary"
    | "care_recommendations"
    | "biomarker_reports"
    | "biomarker_trends"
    | "genetic_profile"
    | "genetic_markers";
  databaseLabel: string;
  propertyNames: string[];
  sampleRecords: Record<string, string | number | null>[];
  totalRecords: number;
}
