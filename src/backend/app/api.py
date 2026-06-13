from fastapi import APIRouter, HTTPException

from app.models import (
    AssistantAnswer,
    AssistantBootstrap,
    CareRecommendation,
    DailyBriefing,
    AssistantRules,
    BiomarkerConfirmImportInput,
    BiomarkerConfirmImportResult,
    BiomarkerCsvImportInput,
    BiomarkerImportDraftBatch,
    BiomarkerObservation,
    BiomarkerPriorityConfig,
    BiomarkerPriorityMarker,
    BiomarkerReport,
    BiomarkerTrendSnapshot,
    ChatMessage,
    ChatRespondInput,
    ChatRespondOutput,
    Conversation,
    CreateDailyCheckInInput,
    CreateHealthSignalInput,
    CreateMealEntryInput,
    CreateConversationInput,
    CreateCareRecommendationInput,
    DailyCheckIn,
    EvidenceKnowledgeSearchResponse,
    EvidenceKnowledgeSyncResponse,
    FollowUpSuggestion,
    GeneticImportDraft,
    GeneticImportDraftInput,
    GeneticPriorityConfig,
    GeneticProfile,
    GeneticPriorityMarker,
    HealthSignal,
    MealEntry,
    MovementBlock,
    NotionSyncResult,
    NotionSyncStatus,
    NotionSyncHistoryEntry,
    NotionMappingPreview,
    RoutineDefinition,
    UpsertGeneticProfileInput,
    UzbKnowledgeSearchResponse,
    UzbKnowledgeSyncResponse,
    UserProfile,
)
from app.services.care_recommendation_service import (
    create_care_recommendation,
    list_care_recommendations,
)
from app.services.biomarker_confirm_service import (
    confirm_biomarker_import,
    list_biomarker_observations,
    list_biomarker_reports,
    list_biomarker_trends,
)
from app.services.biomarker_priority_service import list_priority_biomarkers
from app.services.biomarker_priority_service import replace_priority_biomarkers
from app.services.biomarker_service import build_biomarker_import_draft_from_csv
from app.services.conversation_service import (
    add_message,
    create_conversation,
    get_conversation,
    list_conversations,
    list_messages,
)
from app.services.daily_check_in_service import create_daily_check_in, list_daily_check_ins
from app.services.evidence_knowledge_service import (
    search_evidence_knowledge,
    sync_evidence_documents_from_notion,
)
from app.services.genetics_service import (
    build_genetic_import_draft,
    get_genetic_profile,
    upsert_genetic_profile,
)
from app.services.genetic_priority_service import (
    list_priority_genetic_markers,
    replace_priority_genetic_markers,
)
from app.services.guidance_service import (
    build_answer_for_message,
    build_daily_briefing,
    get_sample_answer,
)
from app.services.follow_up_service import (
    create_follow_up_for_care_recommendation,
    create_follow_up_for_check_in,
    create_follow_up_for_meal,
    create_follow_up_for_signal,
    list_due_follow_ups,
    list_follow_ups,
    list_today_follow_ups,
    mark_follow_up_done,
)
from app.services.health_signal_service import (
    create_health_signal,
    delete_health_signal,
    list_health_signals,
)
from app.services.meal_service import create_meal_entry, delete_meal_entry, list_meal_entries
from app.services.notion_sync_service import (
    notion_mapping_preview,
    notion_sync_history,
    notion_sync_status,
    sync_source_to_outbox,
)
from app.services.profile_service import get_default_profile
from app.services.rules_service import get_assistant_rules
from app.services.routine_service import list_movement_blocks, list_routines
from app.services.ubz_knowledge_service import (
    search_ubz_knowledge,
    sync_ubz_documents_from_notion,
)

router = APIRouter()


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/profile", response_model=UserProfile)
def read_profile() -> UserProfile:
    return get_default_profile()


@router.get("/routines", response_model=list[RoutineDefinition])
def read_routines() -> list[RoutineDefinition]:
    return list_routines()


@router.get("/movement-blocks", response_model=list[MovementBlock])
def read_movement_blocks() -> list[MovementBlock]:
    return list_movement_blocks()


@router.get("/care-recommendations", response_model=list[CareRecommendation])
def read_care_recommendations() -> list[CareRecommendation]:
    return list_care_recommendations()


@router.post("/care-recommendations", response_model=CareRecommendation)
def create_care_recommendation_entry(
    payload: CreateCareRecommendationInput,
) -> CareRecommendation:
    return create_care_recommendation(payload)


@router.get("/genetics/profile", response_model=GeneticProfile | None)
def read_genetic_profile() -> GeneticProfile | None:
    return get_genetic_profile()


@router.put("/genetics/profile", response_model=GeneticProfile)
def write_genetic_profile(payload: UpsertGeneticProfileInput) -> GeneticProfile:
    return upsert_genetic_profile(payload)


@router.post("/genetics/import-draft", response_model=GeneticImportDraft)
def create_genetic_import_draft(payload: GeneticImportDraftInput) -> GeneticImportDraft:
    return build_genetic_import_draft(payload)


@router.get("/genetics/priorities", response_model=list[GeneticPriorityMarker])
def read_genetic_priorities() -> list[GeneticPriorityMarker]:
    return list_priority_genetic_markers()


@router.put("/genetics/priorities", response_model=list[GeneticPriorityMarker])
def write_genetic_priorities(
    payload: GeneticPriorityConfig,
) -> list[GeneticPriorityMarker]:
    return replace_priority_genetic_markers(payload.markers)


@router.post("/biomarkers/import-draft", response_model=BiomarkerImportDraftBatch)
def create_biomarker_import_draft(payload: BiomarkerCsvImportInput) -> BiomarkerImportDraftBatch:
    return build_biomarker_import_draft_from_csv(payload)


@router.post("/biomarkers/confirm-import", response_model=BiomarkerConfirmImportResult)
def confirm_biomarkers(payload: BiomarkerConfirmImportInput) -> BiomarkerConfirmImportResult:
    return confirm_biomarker_import(payload)


@router.get("/biomarkers/reports", response_model=list[BiomarkerReport])
def read_biomarker_reports() -> list[BiomarkerReport]:
    return list_biomarker_reports()


@router.get("/biomarkers/observations", response_model=list[BiomarkerObservation])
def read_biomarker_observations() -> list[BiomarkerObservation]:
    return list_biomarker_observations()


@router.get("/biomarkers/trends", response_model=list[BiomarkerTrendSnapshot])
def read_biomarker_trends() -> list[BiomarkerTrendSnapshot]:
    return list_biomarker_trends()


@router.get("/biomarkers/priorities", response_model=list[BiomarkerPriorityMarker])
def read_biomarker_priorities() -> list[BiomarkerPriorityMarker]:
    return list_priority_biomarkers()


@router.put("/biomarkers/priorities", response_model=list[BiomarkerPriorityMarker])
def write_biomarker_priorities(
    payload: BiomarkerPriorityConfig,
) -> list[BiomarkerPriorityMarker]:
    return replace_priority_biomarkers(payload.markers)


@router.get("/assistant/rules", response_model=AssistantRules)
def read_rules() -> AssistantRules:
    return get_assistant_rules()


@router.get("/assistant/bootstrap", response_model=AssistantBootstrap)
def read_bootstrap() -> AssistantBootstrap:
    conversations = list_conversations()
    answer = get_sample_answer()
    if conversations:
        conversation = conversations[0]
        messages = list_messages(conversation.id)
    else:
        conversation = create_conversation("Denni vedeni")
        assistant_message = add_message(conversation.id, "assistant", answer.summary)
        messages = [assistant_message]

    return AssistantBootstrap(
        profile=get_default_profile(),
        rules=get_assistant_rules(),
        conversation=get_conversation(conversation.id),
        messages=messages,
        answer=answer,
    )


@router.get("/conversations", response_model=list[Conversation])
def read_conversations() -> list[Conversation]:
    return list_conversations()


@router.post("/conversations", response_model=Conversation)
def create_new_conversation(payload: CreateConversationInput) -> Conversation:
    return create_conversation(payload.title)


@router.get("/conversations/{conversation_id}/messages", response_model=list[ChatMessage])
def read_messages(conversation_id: str) -> list[ChatMessage]:
    return list_messages(conversation_id)


@router.get("/assistant/today", response_model=AssistantAnswer)
def get_today_guidance() -> AssistantAnswer:
    return get_sample_answer()


@router.get("/assistant/briefing", response_model=DailyBriefing)
def get_daily_briefing() -> DailyBriefing:
    return build_daily_briefing()


@router.get("/knowledge/ubz/search", response_model=UzbKnowledgeSearchResponse)
def search_ubz(query: str) -> UzbKnowledgeSearchResponse:
    return UzbKnowledgeSearchResponse(query=query, hits=search_ubz_knowledge(query))


@router.post("/knowledge/ubz/sync", response_model=UzbKnowledgeSyncResponse)
def sync_ubz() -> UzbKnowledgeSyncResponse:
    return sync_ubz_documents_from_notion()


@router.get("/knowledge/evidence/search", response_model=EvidenceKnowledgeSearchResponse)
def search_evidence(query: str) -> EvidenceKnowledgeSearchResponse:
    return EvidenceKnowledgeSearchResponse(
        query=query,
        hits=search_evidence_knowledge(query),
    )


@router.post("/knowledge/evidence/sync", response_model=EvidenceKnowledgeSyncResponse)
def sync_evidence() -> EvidenceKnowledgeSyncResponse:
    return sync_evidence_documents_from_notion()


@router.get("/integrations/notion/status", response_model=NotionSyncStatus)
def read_notion_sync_status() -> NotionSyncStatus:
    return notion_sync_status()


@router.get("/integrations/notion/history", response_model=list[NotionSyncHistoryEntry])
def read_notion_sync_history() -> list[NotionSyncHistoryEntry]:
    return notion_sync_history()


@router.get(
    "/integrations/notion/preview/{source_type}",
    response_model=NotionMappingPreview,
)
def read_notion_mapping_preview(source_type: str) -> NotionMappingPreview:
    return notion_mapping_preview(source_type)  # type: ignore[arg-type]


@router.get("/daily-check-ins", response_model=list[DailyCheckIn])
def read_daily_check_ins() -> list[DailyCheckIn]:
    return list_daily_check_ins()


@router.post("/daily-check-ins", response_model=DailyCheckIn)
def create_check_in(payload: CreateDailyCheckInInput) -> DailyCheckIn:
    return create_daily_check_in(payload)


@router.post("/integrations/notion/sync/daily-check-ins", response_model=NotionSyncResult)
def sync_daily_check_ins_to_notion() -> NotionSyncResult:
    return sync_source_to_outbox("daily_check_ins")


@router.get("/meals", response_model=list[MealEntry])
def read_meals() -> list[MealEntry]:
    return list_meal_entries()


@router.post("/meals", response_model=MealEntry)
def create_meal(payload: CreateMealEntryInput) -> MealEntry:
    return create_meal_entry(payload)


@router.delete("/meals/{meal_id}", response_model=MealEntry)
def remove_meal(meal_id: str) -> MealEntry:
    removed = delete_meal_entry(meal_id)
    if removed is None:
        raise HTTPException(status_code=404, detail="Meal not found.")
    return removed


@router.get("/health-signals", response_model=list[HealthSignal])
def read_health_signals() -> list[HealthSignal]:
    return list_health_signals()


@router.post("/health-signals", response_model=HealthSignal)
def create_signal(payload: CreateHealthSignalInput) -> HealthSignal:
    return create_health_signal(payload)


@router.delete("/health-signals/{signal_id}", response_model=HealthSignal)
def remove_signal(signal_id: str) -> HealthSignal:
    removed = delete_health_signal(signal_id)
    if removed is None:
        raise HTTPException(status_code=404, detail="Health signal not found.")
    return removed


@router.post("/integrations/notion/sync/health-signals", response_model=NotionSyncResult)
def sync_health_signals_to_notion() -> NotionSyncResult:
    return sync_source_to_outbox("health_signals")


@router.get("/follow-ups", response_model=list[FollowUpSuggestion])
def read_follow_ups() -> list[FollowUpSuggestion]:
    return list_follow_ups()


@router.post("/integrations/notion/sync/follow-ups", response_model=NotionSyncResult)
def sync_follow_ups_to_notion() -> NotionSyncResult:
    return sync_source_to_outbox("follow_ups")


@router.post("/integrations/notion/sync/daily-summary", response_model=NotionSyncResult)
def sync_daily_summary_to_notion() -> NotionSyncResult:
    return sync_source_to_outbox("daily_summary")


@router.post("/integrations/notion/sync/care-recommendations", response_model=NotionSyncResult)
def sync_care_recommendations_to_notion() -> NotionSyncResult:
    return sync_source_to_outbox("care_recommendations")


@router.post("/integrations/notion/sync/biomarker-reports", response_model=NotionSyncResult)
def sync_biomarker_reports_to_notion() -> NotionSyncResult:
    return sync_source_to_outbox("biomarker_reports")


@router.post("/integrations/notion/sync/biomarker-trends", response_model=NotionSyncResult)
def sync_biomarker_trends_to_notion() -> NotionSyncResult:
    return sync_source_to_outbox("biomarker_trends")


@router.post("/integrations/notion/sync/genetic-profile", response_model=NotionSyncResult)
def sync_genetic_profile_to_notion() -> NotionSyncResult:
    return sync_source_to_outbox("genetic_profile")


@router.post("/integrations/notion/sync/genetic-markers", response_model=NotionSyncResult)
def sync_genetic_markers_to_notion() -> NotionSyncResult:
    return sync_source_to_outbox("genetic_markers")


@router.get("/follow-ups/due", response_model=list[FollowUpSuggestion])
def read_due_follow_ups() -> list[FollowUpSuggestion]:
    return list_due_follow_ups()


@router.get("/follow-ups/today", response_model=list[FollowUpSuggestion])
def read_today_follow_ups() -> list[FollowUpSuggestion]:
    return list_today_follow_ups()


@router.post("/meals/{meal_id}/follow-up", response_model=FollowUpSuggestion)
def create_meal_follow_up(meal_id: str) -> FollowUpSuggestion:
    return create_follow_up_for_meal(meal_id)


@router.post("/health-signals/{signal_id}/follow-up", response_model=FollowUpSuggestion)
def create_signal_follow_up(signal_id: str) -> FollowUpSuggestion:
    return create_follow_up_for_signal(signal_id)


@router.post("/daily-check-ins/{check_in_id}/follow-up", response_model=FollowUpSuggestion)
def create_check_in_follow_up(check_in_id: str) -> FollowUpSuggestion:
    return create_follow_up_for_check_in(check_in_id)


@router.post("/care-recommendations/{recommendation_id}/follow-up", response_model=FollowUpSuggestion)
def create_care_follow_up(recommendation_id: str) -> FollowUpSuggestion:
    return create_follow_up_for_care_recommendation(recommendation_id)


@router.post("/follow-ups/{follow_up_id}/complete", response_model=FollowUpSuggestion)
def complete_follow_up(follow_up_id: str) -> FollowUpSuggestion:
    return mark_follow_up_done(follow_up_id)


@router.post("/chat/respond", response_model=ChatRespondOutput)
def respond_in_chat(payload: ChatRespondInput) -> ChatRespondOutput:
    conversation_id = payload.conversation_id
    user_message = add_message(conversation_id, "user", payload.message)
    answer = build_answer_for_message(payload.message)
    assistant_message = add_message(conversation_id, "assistant", answer.summary)
    conversations = list_conversations()
    conversation = next(
        item for item in conversations if item.id == user_message.conversation_id
    )

    return ChatRespondOutput(
        conversation=conversation,
        userMessage=user_message,
        assistantMessage=assistant_message,
        answer=answer,
    )
