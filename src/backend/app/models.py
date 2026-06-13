from pydantic import BaseModel, Field


class SourceScopeSelection(BaseModel):
    mode: str
    groups: list[str]
    locked: bool
    reason: str | None = None


class AnswerSection(BaseModel):
    kind: str
    title: str
    content: str


class AnswerSource(BaseModel):
    label: str
    type: str
    reference: str | None = None
    authority_tier: str = Field(default="supporting_context", alias="authorityTier")

    model_config = {"populate_by_name": True}


class CareRecommendation(BaseModel):
    id: str
    title: str
    source: str
    category: str
    priority: str
    recommendation: str
    active_from: str | None = Field(default=None, alias="activeFrom")
    review_frequency: str | None = Field(default=None, alias="reviewFrequency")
    next_due: str | None = Field(default=None, alias="nextDue")
    related_markers: list[str] = Field(default_factory=list, alias="relatedMarkers")
    notes: str | None = None
    status: str = "active"

    model_config = {"populate_by_name": True}


class CreateCareRecommendationInput(BaseModel):
    title: str
    source: str
    category: str
    priority: str
    recommendation: str
    active_from: str | None = Field(default=None, alias="activeFrom")
    review_frequency: str | None = Field(default=None, alias="reviewFrequency")
    next_due: str | None = Field(default=None, alias="nextDue")
    related_markers: list[str] = Field(default_factory=list, alias="relatedMarkers")
    notes: str | None = None

    model_config = {"populate_by_name": True}


class RoutineStep(BaseModel):
    id: str
    title: str
    purpose: str
    duration_label: str = Field(alias="durationLabel")
    required: bool
    fallback: str | None = None

    model_config = {"populate_by_name": True}


class RoutineDefinition(BaseModel):
    id: str
    title: str
    category: str
    goal: str
    timing: str
    variants: list[str]
    steps: list[RoutineStep]

    model_config = {"populate_by_name": True}


class MovementBlock(BaseModel):
    id: str
    title: str
    area: str
    frequency: str
    duration_label: str = Field(alias="durationLabel")
    benefit: str
    caution: str | None = None
    examples: list[str]
    minimum_variant: list[str] = Field(default_factory=list, alias="minimumVariant")
    full_variant: list[str] = Field(default_factory=list, alias="fullVariant")
    sequence_steps: list[str] = Field(default_factory=list, alias="sequenceSteps")

    model_config = {"populate_by_name": True}


class UzbKnowledgeHit(BaseModel):
    id: str
    title: str
    notion_path: str = Field(alias="notionPath")
    summary: str
    guidance: str
    themes: list[str]
    score: int
    excerpt: str | None = None
    source_mode: str = Field(default="seed", alias="sourceMode")
    notion_page_id: str | None = Field(default=None, alias="notionPageId")
    authority_tier: str = Field(default="ubz_primary", alias="authorityTier")

    model_config = {"populate_by_name": True}


class UzbKnowledgeSearchResponse(BaseModel):
    query: str
    hits: list[UzbKnowledgeHit]


class UzbKnowledgeSyncItem(BaseModel):
    id: str
    title: str
    notion_path: str = Field(alias="notionPath")
    notion_page_id: str | None = Field(default=None, alias="notionPageId")
    synced: bool
    source_mode: str = Field(alias="sourceMode")
    excerpt: str | None = None
    error: str | None = None
    authority_tier: str = Field(default="ubz_primary", alias="authorityTier")

    model_config = {"populate_by_name": True}


class UzbKnowledgeSyncResponse(BaseModel):
    synced_at: str = Field(alias="syncedAt")
    synced_count: int = Field(alias="syncedCount")
    items: list[UzbKnowledgeSyncItem]

    model_config = {"populate_by_name": True}


class EvidenceKnowledgeHit(BaseModel):
    id: str
    title: str
    notion_path: str = Field(alias="notionPath")
    summary: str
    guidance: str
    themes: list[str]
    score: int
    excerpt: str | None = None
    source_mode: str = Field(default="seed", alias="sourceMode")
    notion_page_id: str | None = Field(default=None, alias="notionPageId")
    authority_tier: str = Field(default="evidence_primary", alias="authorityTier")

    model_config = {"populate_by_name": True}


class EvidenceKnowledgeSearchResponse(BaseModel):
    query: str
    hits: list[EvidenceKnowledgeHit]


class EvidenceKnowledgeSyncItem(BaseModel):
    id: str
    title: str
    notion_path: str = Field(alias="notionPath")
    notion_page_id: str | None = Field(default=None, alias="notionPageId")
    synced: bool
    source_mode: str = Field(alias="sourceMode")
    excerpt: str | None = None
    error: str | None = None
    authority_tier: str = Field(default="evidence_primary", alias="authorityTier")

    model_config = {"populate_by_name": True}


class EvidenceKnowledgeSyncResponse(BaseModel):
    synced_at: str = Field(alias="syncedAt")
    synced_count: int = Field(alias="syncedCount")
    items: list[EvidenceKnowledgeSyncItem]

    model_config = {"populate_by_name": True}


class AssistantAnswer(BaseModel):
    summary: str
    selected_scope: SourceScopeSelection = Field(alias="selectedScope")
    sections: list[AnswerSection]
    next_steps: list[str] = Field(alias="nextSteps")
    sources: list[AnswerSource]

    model_config = {"populate_by_name": True}


class UserProfile(BaseModel):
    id: str
    display_name: str = Field(alias="displayName")
    age_group: str = Field(alias="ageGroup")
    health_goals: list[str] = Field(alias="healthGoals")
    constraints: list[str]
    preferences: list[str]
    trusted_sources: list[str] = Field(alias="trustedSources")
    guidance_style: str | None = Field(default=None, alias="guidanceStyle")
    daily_rhythm: str | None = Field(default=None, alias="dailyRhythm")
    dna_usage_policy: str | None = Field(default=None, alias="dnaUsagePolicy")

    model_config = {"populate_by_name": True}


class AssistantRules(BaseModel):
    profile_id: str = Field(alias="profileId")
    assistant_identity: str = Field(alias="assistantIdentity")
    voice_mode: str = Field(alias="voiceMode")
    source_scope_default: str = Field(alias="sourceScopeDefault")
    ubz_priority: str = Field(alias="ubzPriority")
    notebooklm_role: str = Field(alias="notebookLmRole")
    dna_policy: str = Field(alias="dnaPolicy")
    warning_tone: str = Field(alias="warningTone")

    model_config = {"populate_by_name": True}


class Conversation(BaseModel):
    id: str
    title: str
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")

    model_config = {"populate_by_name": True}


class ChatMessage(BaseModel):
    id: str
    conversation_id: str = Field(alias="conversationId")
    role: str
    content: str
    created_at: str = Field(alias="createdAt")

    model_config = {"populate_by_name": True}


class CreateConversationInput(BaseModel):
    title: str | None = None


class ChatRespondInput(BaseModel):
    conversation_id: str = Field(alias="conversationId")
    message: str

    model_config = {"populate_by_name": True}


class ChatRespondOutput(BaseModel):
    conversation: Conversation
    user_message: ChatMessage = Field(alias="userMessage")
    assistant_message: ChatMessage = Field(alias="assistantMessage")
    answer: AssistantAnswer

    model_config = {"populate_by_name": True}


class MealEntry(BaseModel):
    id: str
    meal_type: str = Field(alias="mealType")
    title: str
    notes: str | None = None
    tags: list[str]
    occurred_at: str = Field(alias="occurredAt")

    model_config = {"populate_by_name": True}


class CreateMealEntryInput(BaseModel):
    meal_type: str = Field(alias="mealType")
    title: str
    notes: str | None = None
    tags: list[str] = []
    occurred_at: str | None = Field(default=None, alias="occurredAt")

    model_config = {"populate_by_name": True}


class HealthSignal(BaseModel):
    id: str
    category: str
    title: str
    severity: str
    notes: str | None = None
    observed_at: str = Field(alias="observedAt")

    model_config = {"populate_by_name": True}


class CreateHealthSignalInput(BaseModel):
    category: str
    title: str
    severity: str
    notes: str | None = None
    observed_at: str | None = Field(default=None, alias="observedAt")

    model_config = {"populate_by_name": True}


class DailyCheckIn(BaseModel):
    id: str
    check_in_type: str = Field(alias="checkInType")
    energy: int
    stress: int
    sleep_quality: int = Field(alias="sleepQuality")
    notes: str | None = None
    created_at: str = Field(alias="createdAt")

    model_config = {"populate_by_name": True}


class CreateDailyCheckInInput(BaseModel):
    check_in_type: str = Field(alias="checkInType")
    energy: int
    stress: int
    sleep_quality: int = Field(alias="sleepQuality")
    notes: str | None = None
    created_at: str | None = Field(default=None, alias="createdAt")

    model_config = {"populate_by_name": True}


class GeneticMarker(BaseModel):
    id: str
    key: str
    label: str
    category: str
    genotype: str | None = None
    interpretation: str
    recommendation_strength: str = Field(alias="recommendationStrength")
    confidence: str
    source_ref: str | None = Field(default=None, alias="sourceRef")
    related_domains: list[str] = Field(alias="relatedDomains")

    model_config = {"populate_by_name": True}


class GeneticProfile(BaseModel):
    id: str
    source_type: str = Field(alias="sourceType")
    source_label: str = Field(alias="sourceLabel")
    imported_at: str = Field(alias="importedAt")
    summary: str
    markers: list[GeneticMarker]

    model_config = {"populate_by_name": True}


class UpsertGeneticProfileInput(BaseModel):
    source_type: str = Field(alias="sourceType")
    source_label: str = Field(alias="sourceLabel")
    summary: str
    markers: list[GeneticMarker]

    model_config = {"populate_by_name": True}


class GeneticImportDraftInput(BaseModel):
    source_type: str = Field(alias="sourceType")
    source_label: str = Field(alias="sourceLabel")
    raw_text: str = Field(alias="rawText")

    model_config = {"populate_by_name": True}


class GeneticImportDraft(BaseModel):
    source_type: str = Field(alias="sourceType")
    source_label: str = Field(alias="sourceLabel")
    summary: str
    markers: list[GeneticMarker]
    unresolved_notes: list[str] = Field(alias="unresolvedNotes")

    model_config = {"populate_by_name": True}


class BiomarkerReport(BaseModel):
    id: str
    profile_id: str = Field(alias="profileId")
    source_type: str = Field(alias="sourceType")
    source_label: str = Field(alias="sourceLabel")
    source_ref: str | None = Field(default=None, alias="sourceRef")
    lab_name: str | None = Field(default=None, alias="labName")
    collected_at: str | None = Field(default=None, alias="collectedAt")
    reported_at: str | None = Field(default=None, alias="reportedAt")
    fasting_state: str = Field(default="unknown", alias="fastingState")
    notes: str | None = None
    raw_text: str | None = Field(default=None, alias="rawText")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")

    model_config = {"populate_by_name": True}


class BiomarkerObservation(BaseModel):
    id: str
    report_id: str = Field(alias="reportId")
    marker_key: str = Field(alias="markerKey")
    marker_label: str = Field(alias="markerLabel")
    category: str
    value: float | None = None
    unit: str | None = None
    comparator: str = "exact"
    reference_low: float | None = Field(default=None, alias="referenceLow")
    reference_high: float | None = Field(default=None, alias="referenceHigh")
    reference_text: str | None = Field(default=None, alias="referenceText")
    status: str = "unknown"
    measurement_context: str = Field(default="unknown", alias="measurementContext")
    observed_at: str = Field(alias="observedAt")
    source_line: str | None = Field(default=None, alias="sourceLine")
    confidence: str = "parsed_medium"

    model_config = {"populate_by_name": True}


class BiomarkerMarkerDefinition(BaseModel):
    key: str
    label: str
    category: str
    default_unit: str | None = Field(default=None, alias="defaultUnit")
    aliases: list[str]
    canonical_source: str | None = Field(default=None, alias="canonicalSource")
    description: str | None = None

    model_config = {"populate_by_name": True}


class BiomarkerTrendSnapshot(BaseModel):
    marker_key: str = Field(alias="markerKey")
    latest_value: float | None = Field(default=None, alias="latestValue")
    latest_unit: str | None = Field(default=None, alias="latestUnit")
    latest_observed_at: str | None = Field(default=None, alias="latestObservedAt")
    previous_value: float | None = Field(default=None, alias="previousValue")
    delta_absolute: float | None = Field(default=None, alias="deltaAbsolute")
    delta_percent: float | None = Field(default=None, alias="deltaPercent")
    trend_direction: str = Field(default="unknown", alias="trendDirection")
    sample_count: int = Field(default=0, alias="sampleCount")

    model_config = {"populate_by_name": True}


class BiomarkerPriorityMarker(BaseModel):
    marker_key: str = Field(alias="markerKey")
    title: str
    category: str
    priority_rank: int = Field(alias="priorityRank")
    why_it_matters: str = Field(alias="whyItMatters")
    watch_for: list[str] = Field(default_factory=list, alias="watchFor")
    link_with: list[str] = Field(default_factory=list, alias="linkWith")
    alert_when: list[str] = Field(default_factory=list, alias="alertWhen")

    model_config = {"populate_by_name": True}


class BiomarkerPriorityConfig(BaseModel):
    markers: list[BiomarkerPriorityMarker]

    model_config = {"populate_by_name": True}


class GeneticPriorityMarker(BaseModel):
    marker_key: str = Field(alias="markerKey")
    title: str
    category: str
    priority_rank: int = Field(alias="priorityRank")
    why_it_matters: str = Field(alias="whyItMatters")
    watch_for: list[str] = Field(default_factory=list, alias="watchFor")
    link_with: list[str] = Field(default_factory=list, alias="linkWith")
    alert_when: list[str] = Field(default_factory=list, alias="alertWhen")
    confidence: str
    recommendation_strength: str = Field(alias="recommendationStrength")
    genotype: str | None = None
    interpretation: str

    model_config = {"populate_by_name": True}


class GeneticPriorityConfig(BaseModel):
    markers: list[GeneticPriorityMarker]

    model_config = {"populate_by_name": True}


class BiomarkerImportDraftInput(BaseModel):
    source_type: str = Field(alias="sourceType")
    source_label: str = Field(alias="sourceLabel")
    raw_text: str = Field(alias="rawText")
    profile_id: str = Field(default="profile-frantisek", alias="profileId")

    model_config = {"populate_by_name": True}


class BiomarkerImportDraft(BaseModel):
    report: BiomarkerReport
    observations: list[BiomarkerObservation]
    unresolved_notes: list[str] = Field(alias="unresolvedNotes")

    model_config = {"populate_by_name": True}


class BiomarkerCsvImportInput(BaseModel):
    source_type: str = Field(alias="sourceType")
    source_label: str = Field(alias="sourceLabel")
    file_path: str = Field(alias="filePath")
    profile_id: str = Field(default="profile-frantisek", alias="profileId")

    model_config = {"populate_by_name": True}


class BiomarkerImportDraftBatch(BaseModel):
    profile_id: str = Field(alias="profileId")
    source_type: str = Field(alias="sourceType")
    source_label: str = Field(alias="sourceLabel")
    file_path: str = Field(alias="filePath")
    imported_at: str = Field(alias="importedAt")
    report_count: int = Field(alias="reportCount")
    observation_count: int = Field(alias="observationCount")
    reports: list[BiomarkerImportDraft]
    unresolved_notes: list[str] = Field(alias="unresolvedNotes")

    model_config = {"populate_by_name": True}


class BiomarkerConfirmImportInput(BaseModel):
    draft_path: str | None = Field(default=None, alias="draftPath")
    replace_existing: bool = Field(default=True, alias="replaceExisting")

    model_config = {"populate_by_name": True}


class BiomarkerConfirmImportResult(BaseModel):
    confirmed_at: str = Field(alias="confirmedAt")
    draft_path: str = Field(alias="draftPath")
    replaced_existing: bool = Field(alias="replacedExisting")
    report_count: int = Field(alias="reportCount")
    observation_count: int = Field(alias="observationCount")
    trend_count: int = Field(alias="trendCount")

    model_config = {"populate_by_name": True}


class FollowUpSuggestion(BaseModel):
    id: str
    trigger_type: str = Field(alias="triggerType")
    related_id: str = Field(alias="relatedId")
    title: str
    message: str
    delay_label: str = Field(alias="delayLabel")
    suggested_at: str = Field(alias="suggestedAt")
    due_at: str = Field(alias="dueAt")
    status: str

    model_config = {"populate_by_name": True}


class AssistantBootstrap(BaseModel):
    profile: UserProfile
    rules: AssistantRules
    conversation: Conversation
    messages: list[ChatMessage]
    answer: AssistantAnswer

    model_config = {"populate_by_name": True}


class DailyBriefing(BaseModel):
    generated_at: str = Field(alias="generatedAt")
    headline: str
    summary: str
    priorities: list[str]
    due_today_count: int = Field(alias="dueTodayCount")
    due_now_count: int = Field(alias="dueNowCount")
    latest_check_in_type: str | None = Field(default=None, alias="latestCheckInType")
    latest_check_in_energy: int | None = Field(default=None, alias="latestCheckInEnergy")
    flagged_biomarker_count: int = Field(default=0, alias="flaggedBiomarkerCount")
    biomarker_highlights: list[str] = Field(default_factory=list, alias="biomarkerHighlights")
    active_care_recommendation_count: int = Field(default=0, alias="activeCareRecommendationCount")
    care_highlights: list[str] = Field(default_factory=list, alias="careHighlights")
    routine_highlights: list[str] = Field(default_factory=list, alias="routineHighlights")
    movement_highlights: list[str] = Field(default_factory=list, alias="movementHighlights")
    movement_guardrails: list[str] = Field(default_factory=list, alias="movementGuardrails")

    model_config = {"populate_by_name": True}


class NotionSyncResult(BaseModel):
    source_type: str = Field(alias="sourceType")
    synced_count: int = Field(alias="syncedCount")
    attempted_count: int = Field(alias="attemptedCount")
    created_count: int = Field(default=0, alias="createdCount")
    updated_count: int = Field(default=0, alias="updatedCount")
    skipped_count: int = Field(default=0, alias="skippedCount")
    outbox_path: str = Field(alias="outboxPath")
    database_label: str = Field(alias="databaseLabel")
    mode: str
    delivery_state: str = Field(alias="deliveryState")
    synced_ids: list[str] = Field(alias="syncedIds")
    synced_at: str = Field(alias="syncedAt")
    error_message: str | None = Field(default=None, alias="errorMessage")

    model_config = {"populate_by_name": True}


class NotionSyncSourceState(BaseModel):
    source_type: str = Field(alias="sourceType")
    mode: str
    delivery_state: str = Field(alias="deliveryState")
    synced_count: int = Field(alias="syncedCount")
    attempt_count: int = Field(alias="attemptCount")
    failure_count: int = Field(alias="failureCount")
    consecutive_failures: int = Field(alias="consecutiveFailures")
    last_attempt_at: str | None = Field(default=None, alias="lastAttemptAt")
    last_success_at: str | None = Field(default=None, alias="lastSuccessAt")
    last_error: str | None = Field(default=None, alias="lastError")

    model_config = {"populate_by_name": True}


class NotionSyncStatus(BaseModel):
    available_sources: list[str] = Field(alias="availableSources")
    last_sync_at: str | None = Field(default=None, alias="lastSyncAt")
    sync_counts: dict[str, int] = Field(alias="syncCounts")
    outbox_dir: str = Field(alias="outboxDir")
    source_states: dict[str, NotionSyncSourceState] = Field(alias="sourceStates")

    model_config = {"populate_by_name": True}


class NotionSyncHistoryEntry(BaseModel):
    source_type: str = Field(alias="sourceType")
    synced_count: int = Field(alias="syncedCount")
    attempted_count: int = Field(alias="attemptedCount")
    created_count: int = Field(default=0, alias="createdCount")
    updated_count: int = Field(default=0, alias="updatedCount")
    skipped_count: int = Field(default=0, alias="skippedCount")
    outbox_path: str = Field(alias="outboxPath")
    synced_at: str = Field(alias="syncedAt")
    mode: str
    delivery_state: str = Field(alias="deliveryState")
    attempt_number: int = Field(default=1, alias="attemptNumber")
    error_message: str | None = Field(default=None, alias="errorMessage")

    model_config = {"populate_by_name": True}


class NotionMappingPreview(BaseModel):
    source_type: str = Field(alias="sourceType")
    database_label: str = Field(alias="databaseLabel")
    property_names: list[str] = Field(alias="propertyNames")
    sample_records: list[dict[str, str | int | None]] = Field(alias="sampleRecords")
    total_records: int = Field(alias="totalRecords")

    model_config = {"populate_by_name": True}
