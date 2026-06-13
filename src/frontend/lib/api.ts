import type {
  AssistantAnswer,
  AssistantRules,
  BiomarkerObservation,
  BiomarkerPriorityConfig,
  BiomarkerPriorityMarker,
  BiomarkerTrendSnapshot,
  CareRecommendation,
  ChatMessage,
  ChatRespondOutput,
  Conversation,
  CreateDailyCheckInInput,
  CreateHealthSignalInput,
  CreateMealEntryInput,
  DailyBriefing,
  GeneticPriorityMarker,
  GeneticPriorityConfig,
  DailyCheckIn,
  EvidenceKnowledgeSearchResponse,
  EvidenceKnowledgeSyncResponse,
  FollowUpSuggestion,
  HealthSignal,
  MealEntry,
  MovementBlock,
  NotionMappingPreview,
  NotionSyncResult,
  NotionSyncHistoryEntry,
  NotionSyncStatus,
  UzbKnowledgeSearchResponse,
  UzbKnowledgeSyncResponse,
  UserProfile,
} from "@shared/contracts/types";
import { normalizeTextTree } from "@/lib/text-normalization";

export type AssistantBootstrap = {
  profile: UserProfile;
  rules: AssistantRules;
  conversation: Conversation;
  messages: ChatMessage[];
  answer: AssistantAnswer;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return normalizeTextTree((await response.json()) as T);
}

export function fetchBootstrap(): Promise<AssistantBootstrap> {
  return requestJson<AssistantBootstrap>("/assistant/bootstrap");
}

export function fetchDailyBriefing(): Promise<DailyBriefing> {
  return requestJson<DailyBriefing>("/assistant/briefing");
}

export function fetchBiomarkerTrends(): Promise<BiomarkerTrendSnapshot[]> {
  return requestJson<BiomarkerTrendSnapshot[]>("/biomarkers/trends");
}

export function fetchBiomarkerObservations(): Promise<BiomarkerObservation[]> {
  return requestJson<BiomarkerObservation[]>("/biomarkers/observations");
}

export function fetchBiomarkerPriorities(): Promise<BiomarkerPriorityMarker[]> {
  return requestJson<BiomarkerPriorityMarker[]>("/biomarkers/priorities");
}

export function fetchGeneticPriorities(): Promise<GeneticPriorityMarker[]> {
  return requestJson<GeneticPriorityMarker[]>("/genetics/priorities");
}

export function updateGeneticPriorities(
  payload: GeneticPriorityConfig,
): Promise<GeneticPriorityMarker[]> {
  return requestJson<GeneticPriorityMarker[]>("/genetics/priorities", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function updateBiomarkerPriorities(
  payload: BiomarkerPriorityConfig,
): Promise<BiomarkerPriorityMarker[]> {
  return requestJson<BiomarkerPriorityMarker[]>("/biomarkers/priorities", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function fetchMovementBlocks(): Promise<MovementBlock[]> {
  return requestJson<MovementBlock[]>("/movement-blocks");
}

export function fetchCareRecommendations(): Promise<CareRecommendation[]> {
  return requestJson<CareRecommendation[]>("/care-recommendations");
}

export function fetchUzbKnowledge(query: string): Promise<UzbKnowledgeSearchResponse> {
  return requestJson<UzbKnowledgeSearchResponse>(
    `/knowledge/ubz/search?query=${encodeURIComponent(query)}`,
  );
}

export function syncUzbKnowledge(): Promise<UzbKnowledgeSyncResponse> {
  return requestJson<UzbKnowledgeSyncResponse>("/knowledge/ubz/sync", {
    method: "POST",
  });
}

export function fetchEvidenceKnowledge(query: string): Promise<EvidenceKnowledgeSearchResponse> {
  return requestJson<EvidenceKnowledgeSearchResponse>(
    `/knowledge/evidence/search?query=${encodeURIComponent(query)}`,
  );
}

export function syncEvidenceKnowledge(): Promise<EvidenceKnowledgeSyncResponse> {
  return requestJson<EvidenceKnowledgeSyncResponse>("/knowledge/evidence/sync", {
    method: "POST",
  });
}

export function fetchNotionSyncStatus(): Promise<NotionSyncStatus> {
  return requestJson<NotionSyncStatus>("/integrations/notion/status");
}

export function fetchNotionSyncHistory(): Promise<NotionSyncHistoryEntry[]> {
  return requestJson<NotionSyncHistoryEntry[]>("/integrations/notion/history");
}

export function fetchNotionMappingPreview(
  sourceType:
    | "daily_check_ins"
    | "health_signals"
    | "follow_ups"
    | "daily_summary"
    | "care_recommendations"
    | "biomarker_reports"
    | "biomarker_trends"
    | "genetic_profile"
    | "genetic_markers",
): Promise<NotionMappingPreview> {
  return requestJson<NotionMappingPreview>(`/integrations/notion/preview/${sourceType}`);
}

export function sendChatMessage(
  conversationId: string,
  message: string,
): Promise<ChatRespondOutput> {
  return requestJson<ChatRespondOutput>("/chat/respond", {
    method: "POST",
    body: JSON.stringify({
      conversationId,
      message,
    }),
  });
}

export function fetchMeals(): Promise<MealEntry[]> {
  return requestJson<MealEntry[]>("/meals");
}

export function createMeal(payload: CreateMealEntryInput): Promise<MealEntry> {
  return requestJson<MealEntry>("/meals", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteMeal(mealId: string): Promise<MealEntry> {
  return requestJson<MealEntry>(`/meals/${mealId}`, {
    method: "DELETE",
  });
}

export function syncDailyCheckInsToNotion(): Promise<NotionSyncResult> {
  return requestJson<NotionSyncResult>("/integrations/notion/sync/daily-check-ins", {
    method: "POST",
  });
}

export function syncDailySummaryToNotion(): Promise<NotionSyncResult> {
  return requestJson<NotionSyncResult>("/integrations/notion/sync/daily-summary", {
    method: "POST",
  });
}

export function syncCareRecommendationsToNotion(): Promise<NotionSyncResult> {
  return requestJson<NotionSyncResult>("/integrations/notion/sync/care-recommendations", {
    method: "POST",
  });
}

export function syncBiomarkerReportsToNotion(): Promise<NotionSyncResult> {
  return requestJson<NotionSyncResult>("/integrations/notion/sync/biomarker-reports", {
    method: "POST",
  });
}

export function syncBiomarkerTrendsToNotion(): Promise<NotionSyncResult> {
  return requestJson<NotionSyncResult>("/integrations/notion/sync/biomarker-trends", {
    method: "POST",
  });
}

export function syncGeneticProfileToNotion(): Promise<NotionSyncResult> {
  return requestJson<NotionSyncResult>("/integrations/notion/sync/genetic-profile", {
    method: "POST",
  });
}

export function syncGeneticMarkersToNotion(): Promise<NotionSyncResult> {
  return requestJson<NotionSyncResult>("/integrations/notion/sync/genetic-markers", {
    method: "POST",
  });
}

export function fetchHealthSignals(): Promise<HealthSignal[]> {
  return requestJson<HealthSignal[]>("/health-signals");
}

export function createHealthSignal(payload: CreateHealthSignalInput): Promise<HealthSignal> {
  return requestJson<HealthSignal>("/health-signals", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteHealthSignal(signalId: string): Promise<HealthSignal> {
  return requestJson<HealthSignal>(`/health-signals/${signalId}`, {
    method: "DELETE",
  });
}

export function syncHealthSignalsToNotion(): Promise<NotionSyncResult> {
  return requestJson<NotionSyncResult>("/integrations/notion/sync/health-signals", {
    method: "POST",
  });
}

export function fetchDailyCheckIns(): Promise<DailyCheckIn[]> {
  return requestJson<DailyCheckIn[]>("/daily-check-ins");
}

export function createDailyCheckIn(payload: CreateDailyCheckInInput): Promise<DailyCheckIn> {
  return requestJson<DailyCheckIn>("/daily-check-ins", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchFollowUps(): Promise<FollowUpSuggestion[]> {
  return requestJson<FollowUpSuggestion[]>("/follow-ups");
}

export function syncFollowUpsToNotion(): Promise<NotionSyncResult> {
  return requestJson<NotionSyncResult>("/integrations/notion/sync/follow-ups", {
    method: "POST",
  });
}

export function fetchDueFollowUps(): Promise<FollowUpSuggestion[]> {
  return requestJson<FollowUpSuggestion[]>("/follow-ups/due");
}

export function fetchTodayFollowUps(): Promise<FollowUpSuggestion[]> {
  return requestJson<FollowUpSuggestion[]>("/follow-ups/today");
}

export function createMealFollowUp(mealId: string): Promise<FollowUpSuggestion> {
  return requestJson<FollowUpSuggestion>(`/meals/${mealId}/follow-up`, {
    method: "POST",
  });
}

export function createHealthSignalFollowUp(signalId: string): Promise<FollowUpSuggestion> {
  return requestJson<FollowUpSuggestion>(`/health-signals/${signalId}/follow-up`, {
    method: "POST",
  });
}

export function createDailyCheckInFollowUp(checkInId: string): Promise<FollowUpSuggestion> {
  return requestJson<FollowUpSuggestion>(`/daily-check-ins/${checkInId}/follow-up`, {
    method: "POST",
  });
}

export function createCareRecommendationFollowUp(
  recommendationId: string,
): Promise<FollowUpSuggestion> {
  return requestJson<FollowUpSuggestion>(`/care-recommendations/${recommendationId}/follow-up`, {
    method: "POST",
  });
}

export function completeFollowUp(followUpId: string): Promise<FollowUpSuggestion> {
  return requestJson<FollowUpSuggestion>(`/follow-ups/${followUpId}/complete`, {
    method: "POST",
  });
}
