"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import {
  completeFollowUp,
  createCareRecommendationFollowUp,
  createDailyCheckIn,
  createDailyCheckInFollowUp,
  createHealthSignal,
  createHealthSignalFollowUp,
  createMeal,
  createMealFollowUp,
  deleteHealthSignal,
  deleteMeal,
  fetchBiomarkerObservations,
  fetchBiomarkerTrends,
  fetchBiomarkerPriorities,
  fetchGeneticPriorities,
  fetchBootstrap,
  fetchCareRecommendations,
  fetchDailyBriefing,
  fetchDailyCheckIns,
  fetchDueFollowUps,
  fetchEvidenceKnowledge,
  fetchFollowUps,
  fetchHealthSignals,
  fetchMeals,
  fetchMovementBlocks,
  fetchNotionMappingPreview,
  fetchNotionSyncStatus,
  fetchNotionSyncHistory,
  fetchTodayFollowUps,
  fetchUzbKnowledge,
  sendChatMessage,
  syncEvidenceKnowledge,
  syncUzbKnowledge,
  syncDailyCheckInsToNotion,
  syncCareRecommendationsToNotion,
  syncBiomarkerReportsToNotion,
  syncBiomarkerTrendsToNotion,
  syncGeneticProfileToNotion,
  syncGeneticMarkersToNotion,
  syncDailySummaryToNotion,
  syncFollowUpsToNotion,
  syncHealthSignalsToNotion,
} from "@/lib/api";
import { exampleAnswer } from "@/lib/example-answer";
import type {
  AssistantRules,
  BiomarkerObservation,
  BiomarkerPriorityMarker,
  BiomarkerTrendSnapshot,
  CareRecommendation,
  ChatRespondOutput,
  ChatMessage,
  Conversation,
  DailyBriefing,
  DailyCheckIn,
  EvidenceKnowledgeHit,
  EvidenceKnowledgeSyncResponse,
  GeneticPriorityMarker,
  FollowUpSuggestion,
  HealthSignal,
  MealEntry,
  MovementBlock,
  NotionMappingPreview,
  NotionSyncResult,
  NotionSyncHistoryEntry,
  NotionSyncStatus,
  UzbKnowledgeHit,
  UzbKnowledgeSyncResponse,
  UserProfile,
} from "@shared/contracts/types";

type LocalState = {
  profile: UserProfile | null;
  rules: AssistantRules | null;
  conversation: Conversation;
  messages: ChatMessage[];
  answer: ChatRespondOutput["answer"];
};

const initialConversation: Conversation = {
  id: "conv-local-demo",
  title: "Denní vedení",
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
};

const BIOMARKER_DISPLAY_NAMES: Record<string, string> = {
  crp: "CRP",
  ferritin: "Ferritin",
  folate: "Folat",
  ft3: "FT3",
  ft4: "FT4",
  ggt: "GGT",
  glucose_fasting: "Glukoza nalacno",
  hba1c: "HbA1c",
  hdl_c: "HDL cholesterol",
  homocysteine: "Homocystein",
  iron_serum: "Zelezo v seru",
  ldl_c: "LDL cholesterol",
  platelets: "Trombocyty",
  plth: "PLTh (specializovany trombocytarni marker)",
  total_cholesterol: "Celkovy cholesterol",
  transferrin: "Transferin",
  triglycerides: "Triglyceridy",
  tsh: "TSH",
  vitamin_b12: "Vitamin B12",
  vitamin_d_25oh: "Vitamin D 25-OH",
};

const NOTION_SYNC_SOURCE_LABELS: Record<string, string> = {
  daily_check_ins: "Daily check-ins",
  health_signals: "Health signals",
  follow_ups: "Follow-ups",
  daily_summary: "Daily summary",
  care_recommendations: "Doporučení péče",
  biomarker_reports: "Biomarker reports",
  biomarker_trends: "Biomarker trendy",
  genetic_profile: "DNA profil",
  genetic_markers: "DNA markery",
};

const NOTION_SOURCE_EXPLAINERS: Record<
  string,
  {
    localMeaning: string;
    syncMeaning: string;
  }
> = {
  daily_check_ins: {
    localMeaning: "Ranni a vecerni check-in je denni operativni kotva pro energii, stres a spanek.",
    syncMeaning: "Do Notion jde jako strukturovany denni zaznam, ne jako nahrada lokalniho chodu aplikace.",
  },
  health_signals: {
    localMeaning: "Health signal se zapisuje lokalne jako aktualni pozorovani nebo problem dne.",
    syncMeaning: "Do Notion se posila jako sdileny prehled signalu a navaznych souvislosti.",
  },
  follow_ups: {
    localMeaning: "Follow-up drzi lokalni reminder logiku a navazuje na konkretni udalosti.",
    syncMeaning: "Do Notion jde jen jako synchronizovany stav ukolu a navaznych pripominek.",
  },
  daily_summary: {
    localMeaning: "Denni souhrn vznika nad lokalnimi daty a je urceny pro rychle shrnuti dne.",
    syncMeaning: "Do Notion se uklada jako sdileny vystup nebo archiv dne.",
  },
  care_recommendations: {
    localMeaning: "Vrstva pece drzi lokalne aktivni doporuceni a jejich vazby na biomarkery a follow-upy.",
    syncMeaning: "Do Notion se posila jako strukturovany care prehled s prioritami a dalsi kontrolou.",
  },
  biomarker_reports: {
    localMeaning: "Lokalne drzime potvrzene reporty jako zdroj syrovych laboratornich dat.",
    syncMeaning: "Do Notion jde jako strukturovany prepis potvrzenych reportu.",
  },
  biomarker_trends: {
    localMeaning: "Lokalne je to hlavni behova pravda pro trendove cteni biomarkeru v chatu.",
    syncMeaning: "Do Notion se posila jako trendova projekce nad potvrzenymi reporty.",
  },
  genetic_profile: {
    localMeaning: "DNA profil drzi lokalni doporucujici vrstvu nad genetickymi predispozicemi.",
    syncMeaning: "Do Notion jde jako integracni prehled profilu, ne jako primarni runtime databaze.",
  },
  genetic_markers: {
    localMeaning: "DNA markery lokalne propojuji predispozice s biomarkerovym a behavioralnim fokusem.",
    syncMeaning: "Do Notion se posilaji jako strukturovane markerove uzly pro dalsi praci.",
  },
};

const CHAT_QUICK_PROMPTS = [
  {
    label: "Jidlo a den",
    prompt: "Dal jsem si hovezi maso se spenatem a trochou ryze. Je to pro me dnes v pohode a na co si dat pozor?",
  },
  {
    label: "Jidlo a biomarkery",
    prompt: "Jak souvisi moje posledni jidlo s B12, homocysteinem a ferritinem?",
  },
  {
    label: "Prakticky dalsi krok",
    prompt: "Co je pro me dnes nejpraktictejsi dalsi krok podle aktualniho stavu dne?",
  },
  {
    label: "UBZ a evidence",
    prompt: "Vysvetli mi tohle pres UBZ a evidence vrstvu, ale prakticky a bez zbytecne obecnych formulaci.",
  },
] as const;

const MEAL_TEST_SCENARIOS = [
  {
    label: "Losos a avokado",
    title: "Losos s avokadem",
    mealType: "dinner",
    tags: "omega3, protein, fat",
    notes: "Produkční test jídla pro vazbu na B12, homocystein a ferritin.",
    followUpPrompt:
      "Dal jsem si lososa s avokadem. Je to pro me dnes v pohode? Jak souvisi moje posledni jidlo s B12, homocysteinem a ferritinem?",
  },
  {
    label: "Jogurt a ovoce",
    title: "Jogurt s ovocem",
    mealType: "breakfast",
    tags: "lactose, protein, sugar",
    notes: "Produkční test jídla pro trávení a energii.",
    followUpPrompt:
      "Dal jsem si jogurt s ovocem. Je to pro me dnes v pohode a na co si dat pozor z pohledu traveni a energie?",
  },
] as const;

const SIGNAL_TEST_SCENARIOS = [
  {
    label: "Nadymani po jidle",
    title: "Nadymani po jidle",
    category: "digestion",
    severity: "medium" as const,
    notes: "Produkční test signálu pro trávení a vazbu na poslední jídlo.",
    followUpPrompt:
      "Mam nadymani po jidle. Jak to dnes cist pres traveni, posledni jidlo a biomarkerovou vrstvu?",
  },
  {
    label: "Napeti v tele",
    title: "Napeti v tele",
    category: "stress",
    severity: "medium" as const,
    notes: "Produkční test signálu pro stres, regeneraci a další praktický krok.",
    followUpPrompt:
      "Citim dnes napeti v tele. Co je nejpraktictejsi dalsi krok podle stresu, regenerace a aktualniho stavu dne?",
  },
] as const;

const CHECK_IN_TEST_SCENARIOS = [
  {
    label: "Rano nizsi energie",
    type: "morning" as const,
    energy: 4,
    stress: 6,
    sleepQuality: 5,
    notes: "Produkční test ranního check-inu pro energii, stres a fokus dne.",
    followUpPrompt:
      "Udelal jsem ranni check-in s nizsi energii a vyssim stresem. Co je pro me dnes nejpraktictejsi dalsi krok?",
  },
  {
    label: "Vecer po narocnem dni",
    type: "evening" as const,
    energy: 3,
    stress: 7,
    sleepQuality: 4,
    notes: "Produkční test večerního check-inu pro regeneraci a další den.",
    followUpPrompt:
      "Udelal jsem vecerni check-in po narocnem dni. Jak mam dnes uzavrit den a co si z toho vzit do zitrka?",
  },
] as const;

function normalizeMealTitleInput(title: string) {
  const trimmed = title.trim().replace(/[.!?]+$/, "");
  const lowered = trimmed.toLowerCase();
  const prefixes = [
    "dal jsem si ",
    "dala jsem si ",
    "snedl jsem ",
    "sne dl jsem ",
    "jedl jsem ",
    "jedla jsem ",
  ];
  for (const prefix of prefixes) {
    if (lowered.startsWith(prefix)) {
      return trimmed.slice(prefix.length).trim().replace(/[.!?]+$/, "");
    }
  }
  return trimmed;
}

function isSameLocalCalendarDay(value: string, reference: Date = new Date()) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return false;

  return (
    parsed.getFullYear() === reference.getFullYear() &&
    parsed.getMonth() === reference.getMonth() &&
    parsed.getDate() === reference.getDate()
  );
}

function formatTimeLabel(value?: string | null) {
  if (!value) return "cas neznamy";

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "cas neznamy";

  return parsed.toLocaleTimeString("cs-CZ", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getSyncDeliveryStateMeta(deliveryState?: string | null) {
  switch (deliveryState) {
    case "synced":
      return { label: "Synced", tone: "optimal" as const };
    case "queued":
      return { label: "Queued", tone: "soft" as const };
    case "failed":
      return { label: "Failed", tone: "danger" as const };
    default:
      return { label: "Idle", tone: "muted" as const };
  }
}

const SOURCE_EXPLAINERS: Record<string, { layer: string; meaning: string; storage: string }> = {
  profile: {
    layer: "Lokální profil",
    meaning: "Osobní nastavení a identita uživatele, ze kterých se řídí tón a priorita odpovědí.",
    storage: "Běží lokálně jako aplikační profil.",
  },
  app_health_data: {
    layer: "Lokální runtime data",
    meaning: "Check-iny, health signály, follow-upy a další provozní data zapsaná v aplikaci.",
    storage: "Zapisuje se lokálně, do Notion jde až přes ruční synchronizaci.",
  },
  app_genetics_data: {
    layer: "Lokální runtime data",
    meaning: "DNA profil a navázané genetické markery používané jako doporučující vrstva.",
    storage: "Zapisuje se lokálně, do Notion jde až přes ruční synchronizaci.",
  },
  app_nutrition_data: {
    layer: "Lokální runtime data",
    meaning: "Jídla a navázané výživové souvislosti pro praktickou interpretaci dne.",
    storage: "Zapisuje se lokálně, do Notion jde až přes ruční synchronizaci souvisejících vrstev.",
  },
  notion_structured: {
    layer: "Notion sync vrstva",
    meaning: "Strukturované záznamy synchronizované mezi lokální aplikací a Notion databázemi.",
    storage: "Primárně vzniká lokálně, Notion slouží jako integrační a sdílená vrstva.",
  },
  notion_extended: {
    layer: "Notion rozšířený kontext",
    meaning: "Doplňující obsah z Notionu mimo čistě operativní běhová data.",
    storage: "Používá se jako doplněk kontextu, ne jako hlavní runtime aplikace.",
  },
  onenote_reflection: {
    layer: "Externí reflexe",
    meaning: "Vedlejší osobní poznámková vrstva, pokud je zapojená do širšího source scope.",
    storage: "Není core runtime aplikace.",
  },
  local_files: {
    layer: "Lokální soubory",
    meaning: "Ruční soubory nebo dokumenty dostupné jen na tomto zařízení.",
    storage: "Zůstává lokálně mimo Notion sync pipeline.",
  },
  external_drive_files: {
    layer: "Externí soubory",
    meaning: "Doplňkové materiály mimo core truth aplikace.",
    storage: "Mimo standardní lokální runtime i Notion sync.",
  },
  ubz_framework: {
    layer: "Knowledge vrstva",
    meaning: "UBZ behaviorální rámec pro rytmus, regeneraci a interpretaci souvislostí.",
    storage: "Slouží jako znalostní podklad; seed nebo live sync z Notion, ne provozní log.",
  },
  notebooklm_research: {
    layer: "Evidence vrstva",
    meaning: "Research a biomarker podklady pro kvalifikovanější zdravotní a laboratorní odpovědi.",
    storage: "Slouží jako znalostní podklad; seed nebo live sync z Notion, ne provozní log.",
  },
  web_evidence: {
    layer: "Externí evidence",
    meaning: "Rozšířená evidence mimo interní knowledge databázi.",
    storage: "Doplňkový zdroj mimo lokální runtime data.",
  },
  model_interpretation: {
    layer: "Modelová interpretace",
    meaning: "Finální syntéza asistenta nad provozními daty a znalostními vrstvami.",
    storage: "Nevzniká jako samostatný zdroj dat; je to výsledný výklad.",
  },
};

function getSourceExplainer(type: string) {
  return (
    SOURCE_EXPLAINERS[type] ?? {
      layer: "Doplňkový zdroj",
      meaning: "Zdroj je zapojený do odpovědi, ale zatím pro něj chybí detailní workflow popis.",
      storage: "Chování závisí na konkrétní integrační vrstvě.",
    }
  );
}

function formatSourceTypeLabel(type: string) {
  return type.replaceAll("_", " ");
}

function getNotionSourceExplainer(type: string) {
  return (
    NOTION_SOURCE_EXPLAINERS[type] ?? {
      localMeaning: "Vrstva vznika nejdriv lokalne v aplikaci.",
      syncMeaning: "Do Notion jde jen tehdy, kdyz ji explicitne synchronizujete.",
    }
  );
}

function getBiomarkerDisplayName(markerKey?: string | null, fallbackLabel?: string | null) {
  if (markerKey && BIOMARKER_DISPLAY_NAMES[markerKey]) {
    return BIOMARKER_DISPLAY_NAMES[markerKey];
  }
  if (fallbackLabel?.trim()) return fallbackLabel;
  return markerKey ?? "Neznámý marker";
}

function repairMojibakeText(value: string): string {
  if (!value) return value;

  let next = value;

  for (let i = 0; i < 3; i += 1) {
    if (!/[\u00C3\u00C5\u00C4\u00C2]/.test(next)) break;

    try {
      const repaired = decodeURIComponent(
        Array.from(next, (char) => `%${char.charCodeAt(0).toString(16).padStart(2, "0")}`).join(""),
      );

      if (repaired === next) break;
      next = repaired;
    } catch {
      break;
    }
  }

  return next
    .replace(/Nezn\u0103\u02c7m\u0103\u02dd/g, "Nezn\u00e1m\u00fd")
    .replace(/stabiln\?/g, "stabiln\u00ed")
    .replace(/v\?\?e/g, "v\u00fd\u0161e")
    .replace(/n\?\?e/g, "n\u00ed\u017ee")
    .replace(/p\?edchoz\?/g, "p\u0159edchoz\u00ed")
    .replace(/m\?\?en\?/g, "m\u011b\u0159en\u00ed")
    .replace(/v\?sledek/g, "v\u00fdsledek")
    .replace(/p\?ijateln\?m/g, "p\u0159ijateln\u00e9m")
    .replace(/p\?smu/g, "p\u00e1smu")
    .replace(/sp\?\?/g, "sp\u00ed\u0161")
    .replace(/ni\?\?\?/g, "ni\u017e\u0161\u00ed")
    .replace(/zv\?\?enou/g, "zv\u00fd\u0161enou")
    .replace(/tak\?e/g, "tak\u017ee")
    .replace(/d\?le\?it\?/g, "d\u016fle\u017eit\u00e9")
    .replace(/hl\?dat/g, "hl\u00eddat")
    .replace(/\?\?douc\?/g, "\u017e\u00e1douc\u00ed")
    .replace(/dol\?/g, "dol\u016f")
    .replace(/dobr\?/g, "dobr\u00e9")
    .replace(/\?\?st/g, "\u010d\u00edst")
    .replace(/zlep\?en\?/g, "zlep\u0161en\u00ed")
    .replace(/hlavn\?/g, "hlavn\u011b")
    .replace(/pozornost\?/g, "pozornost\u00ed")
    .replace(/j\?dlo/g, "j\u00eddlo")
    .replace(/relevantn\?/g, "relevantn\u00ed")
    .replace(/m\? smysl/g, "m\u00e1 smysl")
    .replace(/energi\?/g, "energi\u00ed")
    .replace(/fol\?tovou/g, "fol\u00e1tovou")
    .replace(/metyla\?n\?/g, "metyla\u010dn\u00ed")
    .replace(/\?asem/g, "\u010dasem")
    .replace(/laboratorn\?m/g, "laboratorn\u00edm")
    .replace(/ulo\?it/g, "ulo\u017eit")
    .replace(/ozna\?it/g, "ozna\u010dit")
    .replace(/hotov\?/g, "hotov\u00fd")
    .replace(/vytvo\?it/g, "vytvo\u0159it")
    .replace(/doporu\?en\?/g, "doporu\u010den\u00ed")
    .replace(/P\?ipraven/g, "P\u0159ipraven")
    .replace(/pohybov\?/g, "pohybov\u00e9")
    .replace(/Pln\?/g, "Pln\u00e1")
    .replace(/P\?ehled/g, "P\u0159ehled")
    .replace(/prvn\? bod/g, "prvn\u00ed bod")
    .replace(/Referen\?n\? p\?smo/g, "Referen\u010dn\u00ed p\u00e1smo")
    .replace(/Zdroj \?\?dku/g, "Zdroj \u0159\u00e1dku")
    .replace(/Kontext m\?\?en\?/g, "Kontext m\u011b\u0159en\u00ed")
    .replace(/znamen\?/g, "znamen\u00e1")
    .replace(/ud\?lat/g, "ud\u011blat")
    .replace(/odpov\?di/g, "odpov\u011bdi")
    .replace(/zdroj\?/g, "zdroj\u016f")
    .replace(/Vybran\?/g, "Vybran\u00fd")
    .replace(/Aktivn\?/g, "Aktivn\u00ed")
    .replace(/Uzam\?eno/g, "Uzam\u010deno")
    .replace(/Sm\?r/g, "Sm\u011br")
    .replace(/Po\?et vzork\?/g, "Po\u010det vzork\u016f")
    .replace(/zpozorn\?t/g, "zpozorn\u011bt")
    .replace(/S \?\?m/g, "S \u010d\u00edm")
    .replace(/S\?la/g, "S\u00edla")
    .replace(/Nav\?zan\?/g, "Nav\u00e1zan\u00fd")
    .replace(/Posledn\?/g, "Posledn\u00ed")
    .replace(/Rann\?/g, "Rann\u00ed")
    .replace(/Ve\?ern\?/g, "Ve\u010dern\u00ed")
    .replace(/sp\?nku/g, "sp\u00e1nku")
    .replace(/Pozn\?mka/g, "Pozn\u00e1mka")
    .replace(/vy\?\?zen\?/g, "vy\u0159\u00edzen\u00ed")
    .replace(/kter\?/g, "kter\u00e9")
    .replace(/dr\?\?/g, "dr\u017e\u00ed")
    .replace(/navazuj\?/g, "navazuj\u00ed")
    .replace(/zapsan\?/g, "zapsan\u00e9")
    .replace(/ud\?losti/g, "ud\u00e1losti")
    .replace(/Zat\?m/g, "Zat\u00edm")
    .replace(/akutn\?ho/g, "akutn\u00edho")
    .replace(/pos\?lat/g, "pos\u00edlat")
    .replace(/sign\?l\?/g, "sign\u00e1l\u016f")
    .replace(/Zachy\?te/g, "Zachy\u0165te")
    .replace(/biomarkerov\?m/g, "biomarkerov\u00fdm")
    .replace(/Nap\?\?klad/g, "Nap\u0159\u00edklad")
    .replace(/Sn\?dan\?/g, "Sn\u00eddan\u011b")
    .replace(/Ob\?d/g, "Ob\u011bd")
    .replace(/Ve\?e\?e/g, "Ve\u010de\u0159e")
    .replace(/Sva\?ina/g, "Sva\u010dina")
    .replace(/Tr\?ven\?/g, "Tr\u00e1ven\u00ed")
    .replace(/Sp\?nek/g, "Sp\u00e1nek")
    .replace(/N\?zk\?/g, "N\u00edzk\u00e1")
    .replace(/St\?edn\?/g, "St\u0159edn\u00ed")
    .replace(/Vysok\?/g, "Vysok\u00e1");
}

function repairRenderedContent(root: HTMLElement | null) {
  if (!root) return;

  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const textNodes: Text[] = [];

  while (walker.nextNode()) {
    const current = walker.currentNode;
    if (current instanceof Text) {
      textNodes.push(current);
    }
  }

  for (const node of textNodes) {
    const original = node.nodeValue ?? "";
    const repaired = repairMojibakeText(original);
    if (repaired !== original) {
      node.nodeValue = repaired;
    }
  }

  const elements = root.querySelectorAll("input[placeholder], textarea[placeholder], option");
  for (const element of elements) {
    if (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement) {
      const repaired = repairMojibakeText(element.placeholder);
      if (repaired !== element.placeholder) {
        element.placeholder = repaired;
      }
    }

    if (element instanceof HTMLOptionElement) {
      const repaired = repairMojibakeText(element.text);
      if (repaired !== element.text) {
        element.text = repaired;
      }
    }
  }
}

export default function ChatPage() {
  const rootRef = useRef<HTMLElement | null>(null);
  const dashboardPanelRef = useRef<HTMLElement | null>(null);
  const integrationPanelRef = useRef<HTMLDetailsElement | null>(null);
  const responseSidebarRef = useRef<HTMLElement | null>(null);
  const carePanelRef = useRef<HTMLDivElement | null>(null);
  const biomarkerPanelRef = useRef<HTMLDivElement | null>(null);
  const checkInPanelRef = useRef<HTMLElement | null>(null);
  const chatInputRef = useRef<HTMLTextAreaElement | null>(null);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSavingMeal, setIsSavingMeal] = useState(false);
  const [isSavingSignal, setIsSavingSignal] = useState(false);
  const [isSavingCheckIn, setIsSavingCheckIn] = useState(false);
  const [deletingMealId, setDeletingMealId] = useState<string | null>(null);
  const [deletingSignalId, setDeletingSignalId] = useState<string | null>(null);
  const [isCreatingCareFollowUp, setIsCreatingCareFollowUp] = useState<string | null>(null);
  const [isSavingDailySummary, setIsSavingDailySummary] = useState(false);
  const [syncingSource, setSyncingSource] = useState<string | null>(null);
  const [lastSyncAllResults, setLastSyncAllResults] = useState<NotionSyncResult[]>([]);
  const [isSyncingKnowledgeAll, setIsSyncingKnowledgeAll] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [mealTitle, setMealTitle] = useState("");
  const [mealType, setMealType] = useState("breakfast");
  const [mealNotes, setMealNotes] = useState("");
  const [mealTags, setMealTags] = useState("");

  const [signalTitle, setSignalTitle] = useState("");
  const [signalCategory, setSignalCategory] = useState("digestion");
  const [signalSeverity, setSignalSeverity] = useState<"low" | "medium" | "high">("medium");
  const [signalNotes, setSignalNotes] = useState("");

  const [checkInType, setCheckInType] = useState<"morning" | "evening">("morning");
  const [energy, setEnergy] = useState(6);
  const [stress, setStress] = useState(4);
  const [sleepQuality, setSleepQuality] = useState(7);
  const [checkInNotes, setCheckInNotes] = useState("");

  const [meals, setMeals] = useState<MealEntry[]>([]);
  const [signals, setSignals] = useState<HealthSignal[]>([]);
  const [checkIns, setCheckIns] = useState<DailyCheckIn[]>([]);
  const [careRecommendations, setCareRecommendations] = useState<CareRecommendation[]>([]);
  const [biomarkerPriorities, setBiomarkerPriorities] = useState<BiomarkerPriorityMarker[]>([]);
  const [geneticPriorities, setGeneticPriorities] = useState<GeneticPriorityMarker[]>([]);
  const [biomarkerObservations, setBiomarkerObservations] = useState<BiomarkerObservation[]>([]);
  const [biomarkerTrends, setBiomarkerTrends] = useState<BiomarkerTrendSnapshot[]>([]);
  const [selectedBiomarkerKey, setSelectedBiomarkerKey] = useState<string | null>(null);
  const [selectedObservationId, setSelectedObservationId] = useState<string | null>(null);
  const [selectedGeneticKey, setSelectedGeneticKey] = useState<string | null>(null);
  const [movementBlocks, setMovementBlocks] = useState<MovementBlock[]>([]);
  const [followUps, setFollowUps] = useState<FollowUpSuggestion[]>([]);
  const [dueFollowUps, setDueFollowUps] = useState<FollowUpSuggestion[]>([]);
  const [todayFollowUps, setTodayFollowUps] = useState<FollowUpSuggestion[]>([]);
  const [briefing, setBriefing] = useState<DailyBriefing | null>(null);
  const [notionSyncStatus, setNotionSyncStatus] = useState<NotionSyncStatus | null>(null);
  const [lastSyncResult, setLastSyncResult] = useState<NotionSyncResult | null>(null);
  const [notionSyncHistory, setNotionSyncHistory] = useState<NotionSyncHistoryEntry[]>([]);
  const [previewSource, setPreviewSource] = useState<
    | "daily_check_ins"
    | "health_signals"
    | "follow_ups"
    | "daily_summary"
    | "care_recommendations"
    | "biomarker_reports"
    | "biomarker_trends"
    | "genetic_profile"
    | "genetic_markers"
  >("daily_check_ins");
  const [mappingPreview, setMappingPreview] = useState<NotionMappingPreview | null>(null);
  const [completingId, setCompletingId] = useState<string | null>(null);
  const [ubzHits, setUbzHits] = useState<UzbKnowledgeHit[]>([]);
  const [ubzSyncResult, setUbzSyncResult] = useState<UzbKnowledgeSyncResponse | null>(null);
  const [evidenceHits, setEvidenceHits] = useState<EvidenceKnowledgeHit[]>([]);
  const [evidenceSyncResult, setEvidenceSyncResult] = useState<EvidenceKnowledgeSyncResponse | null>(null);

  const [state, setState] = useState<LocalState>({
    profile: null,
    rules: null,
    conversation: initialConversation,
    messages: [
      {
        id: "msg-local-assistant",
        conversationId: initialConversation.id,
        role: "assistant",
        content: exampleAnswer.summary,
        createdAt: new Date().toISOString(),
      },
    ],
    answer: exampleAnswer,
  });

  useEffect(() => {
    repairRenderedContent(rootRef.current);
  });

  const getObservationStatusMeta = (status?: string | null) => {
    switch (status) {
      case "low":
        return { label: "Nízké", tone: "low" };
      case "optimal":
        return { label: "Optimální", tone: "optimal" };
      case "high":
        return { label: "Vysoké", tone: "high" };
      case "out_of_range":
        return { label: "Mimo pásmo", tone: "danger" };
      default:
        return { label: "Neznámé", tone: "muted" };
    }
  };

  const getTrendDirectionMeta = (direction?: string | null) => {
    switch (direction) {
      case "up":
        return { arrow: "↑", label: "Roste" };
      case "down":
        return { arrow: "↓", label: "Klesá" };
      case "stable":
        return { arrow: "→", label: "Stabilní" };
      default:
        return { arrow: "•", label: "Nejasný" };
    }
  };

  const formatMetricValue = (value?: number | null, unit?: string | null) => {
    if (value === null || value === undefined) return "bez hodnoty";
    return `${value} ${unit ?? ""}`.trim();
  };

  const getTimelineKindMeta = (
    kind: "check_in" | "meal" | "signal" | "follow_up" | "care",
  ) => {
    switch (kind) {
      case "check_in":
        return { icon: "◐", label: "Check-in", tone: "checkin" };
      case "meal":
        return { icon: "●", label: "Jídlo", tone: "meal" };
      case "signal":
        return { icon: "▲", label: "Signál", tone: "signal" };
      case "follow_up":
        return { icon: "◆", label: "Follow-up", tone: "followup" };
      case "care":
        return { icon: "■", label: "Care", tone: "care" };
      default:
        return { icon: "•", label: "Událost", tone: "default" };
    }
  };

  const groupedSources = useMemo(() => state.answer.sources, [state.answer.sources]);
  const sourceWorkflowSummary = useMemo(() => {
    const summary = {
      localRuntimeCount: 0,
      notionContextCount: 0,
      knowledgeCount: 0,
      modelCount: 0,
    };

    groupedSources.forEach((source) => {
      if (
        source.type === "app_health_data" ||
        source.type === "app_genetics_data" ||
        source.type === "app_nutrition_data" ||
        source.type === "profile"
      ) {
        summary.localRuntimeCount += 1;
        return;
      }
      if (source.type === "notion_structured" || source.type === "notion_extended") {
        summary.notionContextCount += 1;
        return;
      }
      if (
        source.type === "ubz_framework" ||
        source.type === "notebooklm_research" ||
        source.type === "web_evidence"
      ) {
        summary.knowledgeCount += 1;
        return;
      }
      if (source.type === "model_interpretation") {
        summary.modelCount += 1;
      }
    });

    return summary;
  }, [groupedSources]);
  const operationalSyncItems = useMemo(() => {
    if (!notionSyncStatus) return [];
    return notionSyncStatus.availableSources.map((sourceType) => ({
      sourceType,
      label: NOTION_SYNC_SOURCE_LABELS[sourceType] ?? formatSourceTypeLabel(sourceType),
      syncedCount: notionSyncStatus.syncCounts[sourceType] ?? 0,
      sourceState: notionSyncStatus.sourceStates[sourceType] ?? null,
    }));
  }, [notionSyncStatus]);
  const activeWorkflowCards = useMemo(
    () => [
      {
        title: "1. Lokální běh aplikace",
        badge: `${meals.length + signals.length + checkIns.length} aktivních záznamů`,
        body:
          "Check-iny, jídla, signály, biomarkerové trendy i follow-upy vznikají nejdřív lokálně v aplikaci a odtud vstupují do chatu.",
        footer:
          "Tohle je hlavní běhová pravda pro denní práci. Notion není potřeba k tomu, aby aplikace fungovala.",
      },
      {
        title: "2. Sync do Notion",
        badge: `${operationalSyncItems.length} připravených zdrojů`,
        body:
          "Do Notion se posílají jen vybrané strukturované runtime vrstvy. Sync je explicitní krok, ne automatická náhrada lokálního běhu.",
        footer:
          operationalSyncItems.length
            ? `Nejvíc synchronizované teď jsou: ${operationalSyncItems
                .slice(0, 3)
                .map((item) => `${item.label} (${item.syncedCount})`)
                .join(" | ")}.`
            : "Zatím bez načteného sync statusu.",
      },
      {
        title: "3. Knowledge a evidence",
        badge: `${ubzHits.length + evidenceHits.length} aktivních hitů`,
        body:
          "UBZ a evidence vrstva slouží jako znalostní podklad pro odpověď. Nepíšou se do nich denní záznamy uživatele jako do provozního logu.",
        footer:
          "Notion tu funguje jako knowledge a integrační vrstva: seed/live obsah pro UBZ a evidence, ne jako hlavní runtime databáze aplikace.",
      },
    ],
    [
      checkIns.length,
      meals.length,
      signals.length,
      operationalSyncItems,
      ubzHits.length,
      evidenceHits.length,
    ],
  );
  const selectedPreviewExplainer = useMemo(
    () => getNotionSourceExplainer(previewSource),
    [previewSource],
  );
  const syncWorkflowSteps = useMemo(
    () => [
      "1. Zapisujte denni realitu lokalne: check-in, jidlo, signal nebo care zaznam.",
      "2. Nechte chat pracovat nad runtime daty a primichat UBZ nebo evidence podle typu dotazu.",
      "3. Do Notion synchronizujte jen vrstvy, ktere chcete sdilet, archivovat nebo dal zpracovavat.",
      "4. UBZ a evidence synchronizujte zvlast, protoze slouzi jako knowledge podklad, ne jako denni log.",
    ],
    [],
  );
  const practicalWorkflowBuckets = useMemo(
    () => [
      {
        title: "Kam zapisovat hned",
        badge: `${checkIns.length + meals.length + signals.length + followUps.length} lokalnich zaznamu`,
        items: [
          "Check-in, jidlo, health signal a follow-up patri nejdriv sem do lokalni aplikace.",
          "Biomarker trendy, DNA vrstva a care doporuceni se tady ctou jako aktivni runtime kontext.",
          "Tohle je hlavni denni pravda, nad kterou odpovida chat i briefing.",
        ],
      },
      {
        title: "Kdy pouzit Notion sync",
        badge: `${operationalSyncItems.length} runtime vrstev`,
        items: [
          "Spoustejte ho az kdyz chcete sdilet vystup, archivovat stav nebo zpracovat data i mimo appku.",
          operationalSyncItems.length
            ? `Nejcasteji ted dava smysl sync pro: ${operationalSyncItems
                .slice(0, 3)
                .map((item) => item.label)
                .join(", ")}.`
            : "Runtime sync funguje, ale zatim tu neni nacteny aktualni prehled poctu.",
          "Notion sync neni podminka behu aplikace, jen navazna integracni vrstva.",
        ],
      },
      {
        title: "Co nepsat jako denni log",
        badge: `${ubzHits.length + evidenceHits.length} knowledge hitu`,
        items: [
          "UBZ a evidence vrstva neslouzi pro zapis denni reality, ale pro kvalifikovane vysvetleni odpovedi.",
          "Kdyz se ptate chatu na dech, biomarkery nebo souvislosti, tyto vrstvy se primichaji automaticky podle dotazu.",
          "Synchronizace knowledge vrstvy z Notion resi obsah pro vyklad, ne bezny provozni zaznam dne.",
        ],
      },
    ],
    [
      checkIns.length,
      meals.length,
      signals.length,
      followUps.length,
      operationalSyncItems,
      ubzHits.length,
      evidenceHits.length,
    ],
  );
  const practicalDayFlow = useMemo(
    () => [
      "Rano nebo pri zmene stavu zapište check-in a pripadne i signal dne.",
      "Behem dne pridejte jidlo, follow-up nebo care navaznost; chat pak odpovida nad realnym stavem.",
      "Kdyz chcete shrnuti nebo kvalifikovanou radu, ptejte se chatu; UBZ a evidence se pridaji samy.",
      "Do Notion posilejte az to, co ma byt sdilene, archivovane nebo navazane na dalsi externi praci.",
    ],
    [],
  );
  const compactWorkflowCards = useMemo(
    () => [
      {
        title: "1. Jen lokalne",
        badge: `${meals.length + signals.length + checkIns.length + followUps.length} runtime zaznamu`,
        body: "Check-in, jidlo, signal a follow-up vznika nejdriv tady v appce.",
        footer: "Tohle je hlavni bezna pravda dne. Chat i briefing ctou nejdriv tuhle vrstvu.",
      },
      {
        title: "2. Notion sync",
        badge: `${operationalSyncItems.length} zdroju`,
        body: "Do Notion jde jen vybrana strukturovana vrstva a jen kdyz to sami spustite.",
        footer:
          operationalSyncItems.length
            ? `Ted nejvic: ${operationalSyncItems
                .slice(0, 3)
                .map((item) => `${item.label} (${item.syncedCount})`)
                .join(" | ")}.`
            : "Zatim bez nacteneho sync statusu, ale aplikace bezi i bez nej.",
      },
      {
        title: "3. Knowledge vrstva",
        badge: `${ubzHits.length + evidenceHits.length} hitu`,
        body: "UBZ a evidence zlepsuji odpovedi, ale neslouzi jako denni zapis reality.",
        footer: "Notion tu drzi znalostni obsah pro vyklad, ne hlavni runtime databazi.",
      },
    ],
    [
      checkIns.length,
      meals.length,
      signals.length,
      followUps.length,
      operationalSyncItems,
      ubzHits.length,
      evidenceHits.length,
    ],
  );
  const workflowBoundaryCards = useMemo(
    () => [
      {
        title: "Jen lokalne",
        tone: "local",
        badge: `${sourceWorkflowSummary.localRuntimeCount} runtime zdroju`,
        headline: "Sem patri bezny denni provoz",
        body:
          "Check-in, jidlo, signal, follow-up i aktivni care kontext drzte nejdriv lokalne, aby chat pracoval nad realnym stavem dne.",
        actionLabel: "Otevrit check-in niz",
        actionStateLabel: "Otevrit check-in niz",
        onClick: scrollToCheckInPanel,
        disabled: false,
      },
      {
        title: "Sync do Notion",
        tone: "notion",
        badge: `${operationalSyncItems.length} pripravenych vrstev`,
        headline: "Jen to, co chcete sdilet nebo archivovat",
        body:
          "Notion je integracni vrstva. Posilejte tam az vybrane vystupy, souhrny a runtime vrstvy, ktere maji zit i mimo aplikaci.",
        actionLabel: "Ulozit denni souhrn",
        actionStateLabel: "Ukladam denni souhrn",
        onClick: handleSaveDailySummaryToNotion,
        disabled: isSavingDailySummary,
      },
      {
        title: "Knowledge vrstva",
        tone: "knowledge",
        badge: `${sourceWorkflowSummary.knowledgeCount} knowledge zdroju`,
        headline: "Slouzi pro kvalifikovanou odpoved, ne pro log dne",
        body:
          "UBZ a evidence vrstva doplnuje souvislosti, interpretaci a vysvetleni. Nezapisujte sem bezny provoz, ale osvezujte ji pro lepsi odpovedi.",
        actionLabel: "Synchronizovat knowledge vrstvu",
        actionStateLabel: "Synchronizuji knowledge vrstvu",
        onClick: handleKnowledgeSyncAll,
        disabled: isSyncingKnowledgeAll,
      },
    ],
    [
      handleKnowledgeSyncAll,
      handleSaveDailySummaryToNotion,
      isSavingDailySummary,
      isSyncingKnowledgeAll,
      operationalSyncItems.length,
      scrollToCheckInPanel,
      sourceWorkflowSummary.knowledgeCount,
      sourceWorkflowSummary.localRuntimeCount,
    ],
  );
  const layerClarityCards = useMemo(
    () => [
      {
        id: "runtime",
        tone: "local",
        eyebrow: "1. Lokalni runtime",
        headline: "Tady vznika denni realita aplikace",
        badge: `${checkIns.length + meals.length + signals.length + followUps.length} aktivnich zaznamu`,
        belongs: [
          "Check-in, jidlo, health signal a follow-up zapisujte nejdriv sem.",
          "Chat, briefing a dashboard ctou nejdriv tuhle vrstvu.",
        ],
        avoid: [
          "Nepresouvejte sem knowledge obsah misto bezneho denniho zapisu.",
        ],
      },
      {
        id: "notion",
        tone: "notion",
        eyebrow: "2. Notion sync",
        headline: "Jen sdileny nebo archivni vystup",
        badge: `${operationalSyncItems.length} pripravenych sync vrstev`,
        belongs: [
          "Daily summary a vybrane strukturovane runtime vrstvy posilejte sem az ve chvili, kdy maji zit i mimo appku.",
          "Notion je integracni vrstva pro sdileni, archiv a dalsi navaznou praci.",
        ],
        avoid: [
          "Neni to primarni runtime databaze aplikace.",
          "Bez syncu ma aplikace porad fungovat plne lokalne.",
        ],
      },
      {
        id: "knowledge",
        tone: "knowledge",
        eyebrow: "3. Knowledge-only",
        headline: "Podklad pro vyklad, ne denni log",
        badge: `${ubzHits.length + evidenceHits.length} knowledge hitu`,
        belongs: [
          "UBZ a evidence pomahaji s vysvetlenim souvislosti, biomarkeru a dalsich dopadu.",
          "Refresh knowledge vrstvy dava smysl pred hlubsim chat dotazem nebo po zmene obsahu v Notion.",
        ],
        avoid: [
          "Nezapisujte sem bezny provozni stav dne misto check-inu, jidla nebo signalu.",
        ],
      },
    ],
    [
      checkIns.length,
      meals.length,
      signals.length,
      followUps.length,
      operationalSyncItems.length,
      ubzHits.length,
      evidenceHits.length,
    ],
  );
  const layerClarityRules = useMemo(
    () => [
      "Kdyz nevite kam neco patri, zacnete lokalnim zapisem dne.",
      "Notion pouzijte az ve chvili, kdy ma vystup byt sdileny, archivovany nebo zpracovany dal.",
      "Knowledge vrstvu obnovujte kvuli lepsimu vykladu, ne kvuli beznemu provoznimu logu.",
    ],
    [],
  );
  const compactWorkflowSteps = useMemo(
    () => [
      "1. Zapisujte den sem: check-in, jidlo, signal, follow-up.",
      "2. Na radu se ptejte chatu, ten si primicha runtime i knowledge kontext.",
      "3. Do Notion posilejte jen to, co chcete sdilet nebo archivovat.",
      "4. UBZ a evidence refreshujte zvlast jako knowledge vrstvu.",
    ],
    [],
  );
  const compactWorkflowBuckets = useMemo(
    () => [
      {
        title: "Kam zapisovat hned",
        badge: `${checkIns.length + meals.length + signals.length + followUps.length} lokalnich zaznamu`,
        items: [
          "Check-in, jidlo, signal a follow-up patri nejdriv sem.",
          "Biomarkery, DNA a care se tu ctou jako aktivni kontext dne.",
          "Chat i briefing vychazi hlavne z teto vrstvy.",
        ],
      },
      {
        title: "Kdy pouzit Notion sync",
        badge: `${operationalSyncItems.length} runtime vrstev`,
        items: [
          "Poustejte ho az kdyz chcete sdilet, archivovat nebo navazat dalsi praci.",
          operationalSyncItems.length
            ? `Ted nejcasteji: ${operationalSyncItems
                .slice(0, 3)
                .map((item) => item.label)
                .join(", ")}.`
            : "Sync funguje, ale zatim tu neni nacteny aktualni prehled.",
          "Notion sync neni podminka behu appky.",
        ],
      },
      {
        title: "Co nepsat jako denni log",
        badge: `${ubzHits.length + evidenceHits.length} knowledge hitu`,
        items: [
          "UBZ a evidence nejsou zapis dne, ale podklad pro odpoved.",
          "Pri dotazu na dech, biomarkery nebo souvislosti se primichaji automaticky.",
          "Knowledge sync z Notion obnovuje vyklad, ne provozni log.",
        ],
      },
    ],
    [
      checkIns.length,
      meals.length,
      signals.length,
      followUps.length,
      operationalSyncItems,
      ubzHits.length,
      evidenceHits.length,
    ],
  );
  const compactDayFlow = useMemo(
    () => [
      "Rano nebo pri zmene stavu zapište check-in a pripadne signal.",
      "Behem dne pridejte jidlo, follow-up nebo care navaznost.",
      "Kdyz chcete radu nebo shrnuti, ptejte se chatu.",
      "Do Notion posilejte az sdileny nebo archivni vystup.",
    ],
    [],
  );
  const executivePulseCards = useMemo(
    () => [
      {
        id: "day",
        label: "Dnes rozhoduje",
        value: briefing?.priorities?.[0] ?? "Drz rytmus dne",
        detail: `${briefing?.dueTodayCount ?? 0} otevrenych follow-upu`,
        tone: "focus",
      },
      {
        id: "biomarker",
        label: "Biomarker fokus",
        value: briefing?.biomarkerHighlights?.[0] ?? "Bez hlavni odchylky",
        detail: `${briefing?.flaggedBiomarkerCount ?? 0} aktivnich odchylek`,
        tone: (briefing?.flaggedBiomarkerCount ?? 0) > 0 ? "danger" : "optimal",
      },
      {
        id: "care",
        label: "Péče",
        value: careRecommendations[0]?.title ?? "Bez aktivni priority",
        detail:
          careRecommendations[0]?.nextDue
            ? `Kontrola ${new Date(careRecommendations[0].nextDue).toLocaleDateString("cs-CZ")}`
            : "Zatim bez terminu",
        tone: careRecommendations[0]?.priority === "high" ? "warm" : "muted",
      },
      {
        id: "sync",
        label: "Notion / knowledge",
        value: notionSyncStatus?.lastSyncAt ? "Sync pripraven" : "Zatim bez syncu",
        detail: `${ubzHits.length + evidenceHits.length} knowledge hitu`,
        tone: ubzHits.length + evidenceHits.length > 0 ? "soft" : "muted",
      },
    ],
    [briefing, careRecommendations, notionSyncStatus, ubzHits.length, evidenceHits.length],
  );
  const biomarkerInsightSection = useMemo(
    () => state.answer.sections.find((section) => section.kind === "biomarker_insight") ?? null,
    [state.answer.sections],
  );
  const foodBiomarkerSection = useMemo(
    () => state.answer.sections.find((section) => section.kind === "food_biomarker_context") ?? null,
    [state.answer.sections],
  );
  const careBiomarkerSection = useMemo(
    () => state.answer.sections.find((section) => section.kind === "care_biomarker_context") ?? null,
    [state.answer.sections],
  );
  const dnaBiomarkerSection = useMemo(
    () => state.answer.sections.find((section) => section.kind === "dna_biomarker_context") ?? null,
    [state.answer.sections],
  );
  const priorityBiomarkerTrends = useMemo(() => {
    const priorityKeys = biomarkerPriorities.map((item) => item.markerKey);
    const presentPriority = priorityKeys
      .map((key) => biomarkerTrends.find((trend) => trend.markerKey === key))
      .filter((trend): trend is BiomarkerTrendSnapshot => Boolean(trend));
    const fallback = biomarkerTrends.filter(
      (trend) => !priorityKeys.includes(trend.markerKey),
    );
    return [...presentPriority, ...fallback].slice(0, 8);
  }, [biomarkerPriorities, biomarkerTrends]);
  const selectedBiomarkerTrend = useMemo(() => {
    if (!priorityBiomarkerTrends.length) return null;
    if (!selectedBiomarkerKey) return priorityBiomarkerTrends[0];
    return (
      priorityBiomarkerTrends.find((trend) => trend.markerKey === selectedBiomarkerKey) ??
      priorityBiomarkerTrends[0]
    );
  }, [priorityBiomarkerTrends, selectedBiomarkerKey]);
  const selectedBiomarkerPriority = useMemo(() => {
    if (!selectedBiomarkerTrend) return null;
    return (
      biomarkerPriorities.find((item) => item.markerKey === selectedBiomarkerTrend.markerKey) ?? null
    );
  }, [biomarkerPriorities, selectedBiomarkerTrend]);
  const latestBiomarkerObservationByKey = useMemo(() => {
    const map = new Map<string, BiomarkerObservation>();
    const sorted = [...biomarkerObservations].sort((a, b) => a.observedAt.localeCompare(b.observedAt));
    sorted.forEach((item) => {
      if (item.value === null || item.value === undefined) return;
      map.set(item.markerKey, item);
    });
    return map;
  }, [biomarkerObservations]);
  const selectedBiomarkerObservations = useMemo(() => {
    if (!selectedBiomarkerTrend) return [];
    return biomarkerObservations
      .filter(
        (item) =>
          item.markerKey === selectedBiomarkerTrend.markerKey &&
          item.value !== null &&
          item.value !== undefined,
      )
      .sort((a, b) => a.observedAt.localeCompare(b.observedAt))
      .slice(-8);
  }, [biomarkerObservations, selectedBiomarkerTrend]);
  const selectedBiomarkerTrendChart = useMemo(() => {
    if (selectedBiomarkerObservations.length < 2) return null;

    const getStatusColor = (status: string) => {
      switch (status) {
        case "low":
          return { fill: "#6f8faa", label: "Nizko" };
        case "optimal":
          return { fill: "#546a4f", label: "Optimalni" };
        case "high":
          return { fill: "#c78d52", label: "Vysoko" };
        case "out_of_range":
          return { fill: "#a4523f", label: "Mimo pasmo" };
        default:
          return { fill: "#8a8475", label: "Nezname" };
      }
    };

    const values = selectedBiomarkerObservations.map((item) => item.value ?? 0);
    const referenceLows = selectedBiomarkerObservations
      .map((item) => item.referenceLow)
      .filter((value): value is number => value !== null && value !== undefined);
    const referenceHighs = selectedBiomarkerObservations
      .map((item) => item.referenceHigh)
      .filter((value): value is number => value !== null && value !== undefined);
    const min = Math.min(...values, ...(referenceLows.length ? referenceLows : [Math.min(...values)]));
    const max = Math.max(...values, ...(referenceHighs.length ? referenceHighs : [Math.max(...values)]));
    const width = 320;
    const height = 96;
    const pad = 10;
    const range = max - min || 1;
    const toY = (value: number) =>
      height - pad - ((value - min) / range) * (height - pad * 2);

    const points = selectedBiomarkerObservations.map((item, index) => {
      const x =
        pad +
        (index * (width - pad * 2)) /
          Math.max(selectedBiomarkerObservations.length - 1, 1);
      const y = toY(item.value ?? min);
      const statusColor = getStatusColor(item.status);
      return { x, y, item, color: statusColor.fill, statusLabel: statusColor.label };
    });

    const latestObservation = selectedBiomarkerObservations[selectedBiomarkerObservations.length - 1];
    const referenceLow = latestObservation?.referenceLow ?? referenceLows[referenceLows.length - 1] ?? null;
    const referenceHigh = latestObservation?.referenceHigh ?? referenceHighs[referenceHighs.length - 1] ?? null;
    const referenceBand =
      referenceLow !== null && referenceHigh !== null
        ? {
            yTop: toY(referenceHigh),
            yBottom: toY(referenceLow),
            low: referenceLow,
            high: referenceHigh,
          }
        : null;

    return {
      width,
      height,
      points,
      polyline: points.map((point) => `${point.x},${point.y}`).join(" "),
      min,
      max,
      referenceBand,
      legend: [
        getStatusColor("optimal"),
        getStatusColor("low"),
        getStatusColor("high"),
        getStatusColor("out_of_range"),
        getStatusColor("unknown"),
      ],
    };
  }, [selectedBiomarkerObservations]);
  const selectedBiomarkerObservationDetail = useMemo(() => {
    if (!selectedBiomarkerTrendChart?.points.length) return null;
    return (
      selectedBiomarkerTrendChart.points.find((point) => point.item.id === selectedObservationId) ??
      selectedBiomarkerTrendChart.points[selectedBiomarkerTrendChart.points.length - 1]
    );
  }, [selectedBiomarkerTrendChart, selectedObservationId]);
  const selectedBiomarkerObservationComparison = useMemo(() => {
    if (!selectedBiomarkerTrendChart?.points.length || !selectedBiomarkerObservationDetail) return null;
    const pointIndex = selectedBiomarkerTrendChart.points.findIndex(
      (point) => point.item.id === selectedBiomarkerObservationDetail.item.id,
    );
    if (pointIndex <= 0) return null;

    const previousPoint = selectedBiomarkerTrendChart.points[pointIndex - 1];
    const currentValue = selectedBiomarkerObservationDetail.item.value;
    const previousValue = previousPoint.item.value;
    if (
      currentValue === null ||
      currentValue === undefined ||
      previousValue === null ||
      previousValue === undefined
    ) {
      return null;
    }

    const delta = currentValue - previousValue;
    const absDelta = Math.abs(delta);
    const unit = selectedBiomarkerObservationDetail.item.unit ?? previousPoint.item.unit ?? "";
    const direction =
      absDelta < 0.0001 ? "stabiln?" : delta > 0 ? "v??e" : "n??e";
    const summary =
      absDelta < 0.0001
        ? `Proti p?edchoz?mu m??en? je marker stabiln?.`
        : `Proti predchozimu mereni je marker ${direction} o ${absDelta.toFixed(2)} ${unit}`.trim();

    return {
      summary,
      previousDate: previousPoint.item.observedAt,
      previousValue,
      currentValue,
      delta,
      unit,
    };
  }, [selectedBiomarkerObservationDetail, selectedBiomarkerTrendChart]);
  const selectedBiomarkerFirstObservation = useMemo(() => {
    if (!selectedBiomarkerObservations.length) return null;
    return selectedBiomarkerObservations[0];
  }, [selectedBiomarkerObservations]);
  const selectedBiomarkerSnapshotItems = useMemo(() => {
    if (!selectedBiomarkerTrend || !selectedBiomarkerObservationDetail) return [];

    const latestStatusMeta = getObservationStatusMeta(selectedBiomarkerObservationDetail.item.status);
    const trendMeta = getTrendDirectionMeta(selectedBiomarkerTrend.trendDirection);
    const baseline = selectedBiomarkerFirstObservation;
    const comparison = selectedBiomarkerObservationComparison;

    return [
      {
        label: "Posledn? v?sledek",
        value: formatMetricValue(
          selectedBiomarkerTrend.latestValue,
          selectedBiomarkerTrend.latestUnit,
        ),
        detail: selectedBiomarkerTrend.latestObservedAt
          ? new Date(selectedBiomarkerTrend.latestObservedAt).toLocaleDateString("cs-CZ")
          : "nezn\u00e1m\u00fd termin",
        tone: latestStatusMeta.tone,
      },
      {
        label: "Trend proti minule",
        value: `${trendMeta.arrow} ${trendMeta.label}`,
        detail: comparison?.summary ?? "Zatím chybí srovnatelný předchozí bod",
        tone:
          selectedBiomarkerTrend.trendDirection === "up"
            ? "high"
            : selectedBiomarkerTrend.trendDirection === "down"
              ? "low"
              : "muted",
      },
      {
        label: "Baseline",
        value: baseline ? formatMetricValue(baseline.value, baseline.unit) : "bez baseline",
        detail: baseline
          ? new Date(baseline.observedAt).toLocaleDateString("cs-CZ")
          : "chybi",
        tone: "soft",
      },
      {
        label: "Vzorky v trendu",
        value: `${selectedBiomarkerTrend.sampleCount}`,
        detail: `Status dnes: ${latestStatusMeta.label}`,
        tone: "optimal",
      },
    ];
  }, [
    selectedBiomarkerFirstObservation,
    selectedBiomarkerObservationComparison,
    selectedBiomarkerObservationDetail,
    selectedBiomarkerTrend,
  ]);
  const selectedBiomarkerObservationMeaning = useMemo(() => {
    if (!selectedBiomarkerObservationDetail || !selectedBiomarkerTrend) return null;

    const priority = selectedBiomarkerPriority;
    const status = selectedBiomarkerObservationDetail.item.status;
    const trendDirection = selectedBiomarkerTrend.trendDirection;

    const statusLead =
      status === "optimal"
        ? "Dnes marker vypad? v p?ijateln?m p?smu."
        : status === "low"
          ? "Dnes marker pad? sp?? do ni??? oblasti."
          : status === "high" || status === "out_of_range"
            ? "Dnes marker zasluhuje zv??enou pozornost."
            : "Dnes je marker potreba cist hlavne v souvislostech.";

    const trendLead =
      trendDirection === "up"
        ? "Trend jde nahoru, tak?e je d?le?it? hl?dat, jestli je to pro tento marker ??douc?."
        : trendDirection === "down"
          ? "Trend jde dol?, tak?e je dobr? ??st, jestli jde o zlep?en? nebo propad."
          : trendDirection === "stable"
            ? "Trend je zat?m pom?rn? stabiln?."
            : "Trend zatím neni dost jasny.";

    const watchFor =
      priority?.watchFor?.length
        ? `Hl?dat hlavn?: ${priority.watchFor.slice(0, 2).join(" | ")}.`
        : null;
    const linkWith =
      priority?.linkWith?.length
        ? `??st spolu s: ${priority.linkWith.slice(0, 3).join(" | ")}.`
        : null;

    return [statusLead, trendLead, watchFor, linkWith].filter(Boolean).join(" ");
  }, [selectedBiomarkerObservationDetail, selectedBiomarkerPriority, selectedBiomarkerTrend]);
  const selectedBiomarkerCareRecommendations = useMemo(() => {
    if (!selectedBiomarkerTrend) return [];
    const key = selectedBiomarkerTrend.markerKey;
    const title = (
      biomarkerPriorities.find((item) => item.markerKey === key)?.title ?? key
    ).toLowerCase();
    return careRecommendations.filter((item) => {
      if (item.relatedMarkers.includes(key)) return true;
      const haystack = [
        item.title,
        item.recommendation,
        item.relatedMarkers.join(" "),
        item.notes ?? "",
      ]
        .join(" ")
        .toLowerCase();
      if (["ldl_c", "total_cholesterol", "hdl_c", "triglycerides"].includes(key)) {
        return (
          haystack.includes("cholesterol") ||
          haystack.includes("lipid") ||
          haystack.includes("triglycer") ||
          haystack.includes("ldl") ||
          haystack.includes("hdl")
        );
      }
      if (["glucose_fasting", "hba1c"].includes(key)) {
        return haystack.includes("gluk") || haystack.includes("glykem") || haystack.includes("cukr");
      }
      if (["vitamin_b12", "homocysteine", "folate"].includes(key)) {
        return haystack.includes("b12") || haystack.includes("homocyst") || haystack.includes("folat");
      }
      if (["ferritin", "iron_serum", "transferrin"].includes(key)) {
        return haystack.includes("ferritin") || haystack.includes("zelezo") || haystack.includes("iron");
      }
      if (key === "crp") {
        return haystack.includes("crp") || haystack.includes("zanet");
      }
      if (["tsh", "ft4", "ft3"].includes(key)) {
        return haystack.includes("stit") || haystack.includes("thyroid") || haystack.includes(title);
      }
      return false;
    });
  }, [biomarkerPriorities, careRecommendations, selectedBiomarkerTrend]);
  const selectedBiomarkerCareSummary = useMemo(() => {
    if (!selectedBiomarkerTrend || !selectedBiomarkerCareRecommendations.length) return null;
    const first = selectedBiomarkerCareRecommendations[0];
    const markerTitle = selectedBiomarkerPriority?.title ??
      getBiomarkerDisplayName(selectedBiomarkerTrend.markerKey);
    return `Pro marker ${markerTitle} ted nejvic drzi care doporuceni '${first.title}'.`;
  }, [
    selectedBiomarkerCareRecommendations,
    selectedBiomarkerPriority,
    selectedBiomarkerTrend,
  ]);
  const selectedBiomarkerObservationAction = useMemo(() => {
    if (!selectedBiomarkerObservationDetail || !selectedBiomarkerTrend) return null;

    const markerTitle = selectedBiomarkerPriority?.title ??
      getBiomarkerDisplayName(selectedBiomarkerTrend.markerKey);
    const status = selectedBiomarkerObservationDetail.item.status;
    const latestMeal = meals[0] ?? null;
    const careLead = selectedBiomarkerCareRecommendations[0] ?? null;
    const actionParts: string[] = [];

    if (status === "high" || status === "out_of_range") {
      actionParts.push(`Dnes ?ti ${markerTitle} jako oblast se zv??enou pozornost?.`);
    } else if (status === "low") {
      actionParts.push(`Dnes ?ti ${markerTitle} jako oblast, kde ma smysl hlidat nizsi hodnoty a souvislosti.`);
    } else {
      actionParts.push(`Dnes u ${markerTitle} drz hlavne stabilitu a kontext, ne unahlene zavery.`);
    }

    if (careLead) {
      actionParts.push(`Opiraj to o care doporuceni '${careLead.title}'.`);
    }

    if (latestMeal) {
      actionParts.push(`Posledn? j?dlo '${latestMeal.title}' cti spolu s timto markerem.`);
    }

    if (selectedBiomarkerPriority?.watchFor?.length) {
      actionParts.push(`Nejvic dnes hlidej: ${selectedBiomarkerPriority.watchFor.slice(0, 2).join(" | ")}.`);
    }

    return actionParts.join(" ");
  }, [
    meals,
    selectedBiomarkerCareRecommendations,
    selectedBiomarkerObservationDetail,
    selectedBiomarkerPriority,
    selectedBiomarkerTrend,
  ]);
  const selectedBiomarkerCareIds = useMemo(
    () => new Set(selectedBiomarkerCareRecommendations.map((item) => item.id)),
    [selectedBiomarkerCareRecommendations],
  );
  const selectedGeneticPriority = useMemo(() => {
    if (!geneticPriorities.length) return null;
    if (!selectedGeneticKey) return geneticPriorities[0];
    return geneticPriorities.find((marker) => marker.markerKey === selectedGeneticKey) ?? geneticPriorities[0];
  }, [geneticPriorities, selectedGeneticKey]);
  const selectedGeneticLinkedBiomarkerTrends = useMemo(() => {
    if (!selectedGeneticPriority) return [];
    const linkedKeys = new Set(
      selectedGeneticPriority.linkWith.filter((value) =>
        biomarkerTrends.some((trend) => trend.markerKey === value),
      ),
    );
    return biomarkerTrends.filter((trend) => linkedKeys.has(trend.markerKey)).slice(0, 3);
  }, [biomarkerTrends, selectedGeneticPriority]);
  const selectedGeneticLinkedBiomarkerTitles = useMemo(
    () =>
      selectedGeneticLinkedBiomarkerTrends.map((trend) => {
        return (
          biomarkerPriorities.find((item) => item.markerKey === trend.markerKey)?.title ??
          getBiomarkerDisplayName(trend.markerKey)
        );
      }),
    [biomarkerPriorities, selectedGeneticLinkedBiomarkerTrends],
  );
  const selectedGeneticCareHighlights = useMemo(() => {
    if (!selectedGeneticPriority) return [];
    const normalized = selectedGeneticPriority.markerKey.toLowerCase();
    return careRecommendations
      .filter((item) => {
        const haystack = [
          item.title,
          item.recommendation,
          item.relatedMarkers.join(" "),
          item.notes ?? "",
        ]
          .join(" ")
          .toLowerCase();
        if (normalized.includes("lipid") || normalized.includes("salt_pressure")) {
          return (
            haystack.includes("cholesterol") ||
            haystack.includes("lipid") ||
            haystack.includes("triglycer") ||
            haystack.includes("tlak")
          );
        }
        if (normalized.includes("insulin")) {
          return haystack.includes("gluk") || haystack.includes("metabol");
        }
        if (normalized.includes("methylation") || normalized.includes("b12")) {
          return haystack.includes("b12") || haystack.includes("homocyst") || haystack.includes("folat");
        }
        return false;
      })
      .slice(0, 2)
      .map((item) => item.title);
  }, [careRecommendations, selectedGeneticPriority]);
  const selectedGeneticMealContext = useMemo(() => {
    if (!selectedGeneticPriority || !meals[0]) return null;
    const title = meals[0].title.toLowerCase();
    const tags = meals[0].tags.join(" ").toLowerCase();
    const haystack = `${title} ${tags}`;
    if (selectedGeneticPriority.markerKey === "lipid_regulation") {
      return "Posledn? j?dlo ?ti hlavn? p?es kvalitu tuku, uzeniny a celkovou metabolickou z?t??.";
    }
    if (selectedGeneticPriority.markerKey === "insulin_sensitivity") {
      return "Posledn? j?dlo ?ti p?es glykemickou odezvu, energii po j?dle a souvislost s triglyceridy.";
    }
    if (selectedGeneticPriority.markerKey === "methylation_folate") {
      return "Posledn? j?dlo ?ti p?es fol?tovou a metyla?n? podporu, ne jen p?es kalorie.";
    }
    if (selectedGeneticPriority.markerKey === "b12_absorption") {
      return haystack.includes("maso") || haystack.includes("vej")
        ? "Posledn? j?dlo je relevantn? i pro B12 vrstvu, tak?e m? smysl ??st ho spolu s energi? a biomarkery."
        : "Posledn? j?dlo ?ti i p?es B12 vrstvu a ?asem porovnej s energi? a laboratorn?m B12.";
    }
    return null;
  }, [meals, selectedGeneticPriority]);
  const selectedMealId = useMemo(() => meals[0]?.id ?? null, [meals]);
  const activeFocusPath = useMemo(() => {
    const parts: string[] = [];

    const selectedMeal = meals.find((meal) => meal.id === selectedMealId) ?? meals[0] ?? null;
    if (selectedMeal) {
      parts.push(`Jídlo: ${selectedMeal.title}`);
    }

    if (selectedBiomarkerPriority) {
      parts.push(`Biomarker: ${selectedBiomarkerPriority.title}`);
    } else if (selectedBiomarkerTrend) {
      parts.push(`Biomarker: ${getBiomarkerDisplayName(selectedBiomarkerTrend.markerKey)}`);
    }

    if (selectedGeneticPriority) {
      parts.push(`DNA: ${selectedGeneticPriority.title}`);
    }

    if (selectedBiomarkerCareRecommendations.length) {
      parts.push(`Care: ${selectedBiomarkerCareRecommendations[0].title}`);
    } else if (careRecommendations[0]) {
      parts.push(`Care: ${careRecommendations[0].title}`);
    }

    return parts;
  }, [
    careRecommendations,
    meals,
    selectedBiomarkerCareRecommendations,
    selectedBiomarkerPriority,
    selectedBiomarkerTrend,
    selectedGeneticPriority,
    selectedMealId,
  ]);
  const dashboardCards = useMemo(() => {
    return [
      {
        id: "focus",
        label: "Prvn\u00ed krok",
        value: briefing?.priorities?.[0] ?? "Dr\u017e rytmus dne",
        detail: briefing?.summary ?? "Briefing se na\u010d\u00edt\u00e1.",
        tone: "focus",
      },
      {
        id: "biomarker",
        label: "Co hl\u00eddat v biomarkerech",
        value:
          selectedBiomarkerPriority?.title ??
          briefing?.biomarkerHighlights?.[0] ??
          "Zat\u00edm bez hlavn\u00edho markeru",
        detail: `${briefing?.flaggedBiomarkerCount ?? 0} aktivn\u00edch odchylek`,
        tone: (briefing?.flaggedBiomarkerCount ?? 0) > 0 ? "danger" : "optimal",
      },
      {
        id: "care",
        label: "P\u00e9\u010de a kontrola",
        value:
          careRecommendations[0]?.title ??
          briefing?.careHighlights?.[0] ??
          "Bez aktivn\u00ed priority p\u00e9\u010de",
        detail:
          careRecommendations[0]?.nextDue
            ? `Dal\u0161\u00ed kontrola ${new Date(careRecommendations[0].nextDue).toLocaleDateString("cs-CZ")}`
            : careRecommendations[0]?.recommendation ?? "Zat\u00edm bez dal\u0161\u00edho term\u00ednu",
        tone: careRecommendations[0]?.priority === "high" ? "warm" : "muted",
      },
      {
        id: "routine",
        label: "Re\u017eim dne",
        value:
          briefing?.routineHighlights?.[0] ??
          briefing?.movementHighlights?.[0] ??
          "Dech, hydratace, kr\u00e1tk\u00e1 ch\u016fze",
        detail:
          briefing?.movementGuardrails?.[0] ??
          "Dr\u017eet minimum i v hor\u0161\u00edm dni a netla\u010dit na v\u00fdkon.",
        tone: "soft",
      },
    ];
  }, [briefing, careRecommendations, selectedBiomarkerPriority]);
  const immediateActions = useMemo(() => {
    const items = briefing?.priorities?.slice(0, 3) ?? [];
    return items.length
      ? items
      : [
          "Za\u010dn\u011bte kr\u00e1tk\u00fdm rann\u00edm check-inem.",
          "Zapi\u0161te hlavn\u00ed sign\u00e1l dne nebo j\u00eddlo, kter\u00e9 chcete sledovat.",
          "Dr\u017ete minimum: dech, hydratace, kr\u00e1tk\u00e1 ch\u016fze.",
        ];
  }, [briefing]);
  const dashboardDecisionSummary = useMemo(
    () => ({
      headline: briefing?.priorities?.[0] ?? "Nejdřív ukotvěte rytmus dne",
      support:
        activeFocusPath.length > 0
          ? activeFocusPath.join(" -> ")
          : "Fokus dne se skládá z check-inu, biomarkerů, péče a dalších aktivních vrstev.",
      context:
        briefing?.summary ??
        "Jakmile doplníte první záznam dne, cockpit i chat začnou odpovídat nad konkrétní realitou.",
      actions: immediateActions.slice(0, 3),
    }),
    [activeFocusPath, briefing, immediateActions],
  );
  const operationalSnapshotItems = useMemo(
    () => [
      {
        label: "Otevřené follow-upy",
        value: `${dueFollowUps.length}`,
        detail: todayFollowUps.length ? `${todayFollowUps.length} splatné dnes` : "Dnes bez splatných položek",
        tone: dueFollowUps.length > 0 ? "warm" : "calm",
      },
      {
        label: "Biomarker fokus",
        value: `${briefing?.flaggedBiomarkerCount ?? 0}`,
        detail:
          selectedBiomarkerPriority?.title ??
          briefing?.biomarkerHighlights?.[0] ??
          "Zatím bez hlavní odchylky",
        tone: (briefing?.flaggedBiomarkerCount ?? 0) > 0 ? "alert" : "calm",
      },
      {
        label: "Péče",
        value: `${briefing?.activeCareRecommendationCount ?? careRecommendations.length}`,
        detail: careRecommendations[0]?.title ?? "Bez aktivní priority péče",
        tone: careRecommendations[0]?.priority === "high" ? "warm" : "calm",
      },
      {
        label: "Poslední vstup",
        value: checkIns[0] ? "Check-in" : meals[0] ? "Jídlo" : signals[0] ? "Signál" : "Čeká na záznam",
        detail:
          checkIns[0]?.checkInType === "morning"
            ? "Ranní check-in uložen"
            : checkIns[0]?.checkInType === "evening"
              ? "Večerní check-in uložen"
              : meals[0]?.title ?? signals[0]?.title ?? "Začněte prvním zápisem dne",
        tone: checkIns[0] || meals[0] || signals[0] ? "calm" : "muted",
      },
    ],
    [
      briefing,
      careRecommendations,
      checkIns,
      dueFollowUps.length,
      meals,
      selectedBiomarkerPriority,
      signals,
      todayFollowUps.length,
    ],
  );
  const productionTestStatus = useMemo(() => {
    const todayMeals = meals.filter((item) => isSameLocalCalendarDay(item.occurredAt));
    const todaySignals = signals.filter((item) => isSameLocalCalendarDay(item.observedAt));
    const todayCheckIns = checkIns.filter((item) => isSameLocalCalendarDay(item.createdAt));

    const latestMeal = todayMeals[0] ?? null;
    const latestSignal = todaySignals[0] ?? null;
    const latestCheckIn = todayCheckIns[0] ?? null;

    const items = [
      {
        id: "check-in",
        label: "Check-in flow",
        status: latestCheckIn ? "Otestovano dnes" : "Chybi dnesni test",
        detail: latestCheckIn
          ? `${latestCheckIn.checkInType === "morning" ? "Ranni" : "Vecerni"} check-in v ${formatTimeLabel(latestCheckIn.createdAt)}`
          : "Zatim tu dnes neni ulozeny check-in zapis.",
        tone: latestCheckIn ? "optimal" : "danger",
      },
      {
        id: "meal",
        label: "Meal flow",
        status: latestMeal ? "Otestovano dnes" : "Chybi dnesni test",
        detail: latestMeal
          ? `${latestMeal.title} v ${formatTimeLabel(latestMeal.occurredAt)}`
          : "Zatim tu dnes neni ulozene testovaci jidlo.",
        tone: latestMeal ? "optimal" : "danger",
      },
      {
        id: "signal",
        label: "Health signal flow",
        status: latestSignal ? "Otestovano dnes" : "Chybi dnesni test",
        detail: latestSignal
          ? `${latestSignal.title} v ${formatTimeLabel(latestSignal.observedAt)}`
          : "Zatim tu dnes neni ulozeny health signal.",
        tone: latestSignal ? "optimal" : "danger",
      },
    ] as const;

    return {
      completedCount: items.filter((item) => item.tone === "optimal").length,
      items,
    };
  }, [checkIns, meals, signals]);
  const productionReadinessChecklist = useMemo(() => {
    const syncStates = notionSyncStatus ? Object.values(notionSyncStatus.sourceStates) : [];
    const failingSyncStates = syncStates.filter((state) => state.deliveryState === "failed");
    const hasOutbox = Boolean(notionSyncStatus?.outboxDir?.trim());
    const hasKnowledgeCoverage = ubzHits.length > 0 && evidenceHits.length > 0;
    const hasFreshKnowledgeSync = Boolean(ubzSyncResult?.syncedAt && evidenceSyncResult?.syncedAt);

    const items = [
      {
        id: "runtime",
        label: "Operativni runtime flow",
        status:
          productionTestStatus.completedCount === productionTestStatus.items.length
            ? "Ready"
            : "Chybi denni overeni",
        detail:
          productionTestStatus.completedCount === productionTestStatus.items.length
            ? "Check-in, meal i health signal maji dnesni zapis a appka ma realny denni zaklad."
            : "Pred releasem overte vsechny tri zakladni denni flow primo nad dnesnim runtime stavem.",
        tone:
          productionTestStatus.completedCount === productionTestStatus.items.length ? "optimal" : "danger",
        actionLabel: "Otevrit operativu",
        onClick: scrollToCheckInPanel,
      },
      {
        id: "sync",
        label: "Notion sync audit",
        status:
          failingSyncStates.length === 0 && hasOutbox
            ? "Ready"
            : failingSyncStates.length > 0
              ? "Blokuje sync chyba"
              : "Chybi outbox vrstva",
        detail:
          failingSyncStates.length > 0
            ? `Posledni problem: ${failingSyncStates[0]?.lastError ?? "neznamy sync error"}.`
            : hasOutbox
              ? "Outbox je pripraveny a audit nevykazuje aktivni failed source state."
              : "Bez pripraveného outboxu neni jasna produkcni cesta pro bezpecne doruceni syncu.",
        tone: failingSyncStates.length === 0 && hasOutbox ? "optimal" : "danger",
        actionLabel: "Otevrit sync akce",
        onClick: () => integrationPanelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }),
      },
      {
        id: "knowledge",
        label: "UBZ + evidence vrstva",
        status:
          hasKnowledgeCoverage && hasFreshKnowledgeSync
            ? "Ready"
            : hasKnowledgeCoverage
              ? "Nacteno, ale bez fresh syncu"
              : "Chybi knowledge coverage",
        detail:
          hasKnowledgeCoverage && hasFreshKnowledgeSync
            ? "UBZ i evidence jsou nactene a po poslednim refreshi pripravené pro produkcni interpretaci."
            : hasKnowledgeCoverage
              ? "Obsah je nacteny, ale pred releasem je lepsi jeste udelat explicitni refresh znalostni vrstvy."
              : "Pred releasem osvezte UBZ i evidence, aby chat nestal jen na seedu nebo stare vrstve.",
        tone: hasKnowledgeCoverage && hasFreshKnowledgeSync ? "optimal" : "soft",
        actionLabel: "Synchronizovat knowledge",
        onClick: handleKnowledgeSyncAll,
      },
      {
        id: "eval",
        label: "Production eval suite",
        status: "Manual gate",
        detail: "Pred releasem spustte `npm run eval:production` a puste ven jen PASS build.",
        tone: "notion",
      },
    ] as const;

    return {
      autoReadyCount: items.filter((item) => item.id !== "eval" && item.tone === "optimal").length,
      autoItemCount: items.filter((item) => item.id !== "eval").length,
      items,
    };
  }, [
    evidenceHits.length,
    evidenceSyncResult?.syncedAt,
    handleKnowledgeSyncAll,
    notionSyncStatus,
    productionTestStatus,
    ubzHits.length,
    ubzSyncResult?.syncedAt,
  ]);
  const operationalFlowCards = useMemo(() => {
    const todayCheckIns = checkIns.filter((item) => isSameLocalCalendarDay(item.createdAt));
    const todayMeals = meals.filter((item) => isSameLocalCalendarDay(item.occurredAt));
    const todaySignals = signals.filter((item) => isSameLocalCalendarDay(item.observedAt));
    const todayDueFollowUps = todayFollowUps.filter((item) => isSameLocalCalendarDay(item.dueAt));

    const buildFlowCard = ({
      id,
      label,
      count,
      target,
      latestAt,
      latestLabel,
      emptyLabel,
      tone,
    }: {
      id: string;
      label: string;
      count: number;
      target: number;
      latestAt?: string | null;
      latestLabel: string;
      emptyLabel: string;
      tone: "local" | "meal" | "signal" | "notion";
    }) => {
      const ratio = Math.min(count / Math.max(target, 1), 1);
      const percent = Math.round(ratio * 100);

      return {
        id,
        label,
        count,
        percent,
        tone,
        status:
          count === 0 ? "Zatim prazdne" : count >= target ? "Rytmus drzi" : "Rozjete, ale neplne",
        detail: latestAt ? `${latestLabel} v ${formatTimeLabel(latestAt)}` : emptyLabel,
      };
    };

    return [
      buildFlowCard({
        id: "checkin",
        label: "Check-iny",
        count: todayCheckIns.length,
        target: 2,
        latestAt: todayCheckIns[0]?.createdAt,
        latestLabel: todayCheckIns[0]?.checkInType === "evening" ? "Posledni vecerni check-in" : "Posledni check-in",
        emptyLabel: "Dnes jeste neni zapsany check-in.",
        tone: "local",
      }),
      buildFlowCard({
        id: "meal",
        label: "Jidla",
        count: todayMeals.length,
        target: 3,
        latestAt: todayMeals[0]?.occurredAt,
        latestLabel: todayMeals[0]?.title ? `Posledni: ${todayMeals[0].title}` : "Posledni jidlo",
        emptyLabel: "Dnes jeste neni zapsane jidlo.",
        tone: "meal",
      }),
      buildFlowCard({
        id: "signal",
        label: "Signaly",
        count: todaySignals.length,
        target: 1,
        latestAt: todaySignals[0]?.observedAt,
        latestLabel: todaySignals[0]?.title ? `Posledni: ${todaySignals[0].title}` : "Posledni signal",
        emptyLabel: "Dnes jeste neni zapsany signal.",
        tone: "signal",
      }),
      buildFlowCard({
        id: "followup",
        label: "Dnesni follow-upy",
        count: todayDueFollowUps.length,
        target: 2,
        latestAt: todayDueFollowUps[0]?.dueAt,
        latestLabel: todayDueFollowUps[0]?.title
          ? `Nejblizsi: ${todayDueFollowUps[0].title}`
          : "Nejblizsi follow-up",
        emptyLabel: "Dnes zatim nic neni splatne.",
        tone: "notion",
      }),
    ];
  }, [checkIns, meals, signals, todayFollowUps]);
  const dashboardTrendSummary = useMemo(() => {
    if (selectedBiomarkerTrend) {
      const trendMeta = getTrendDirectionMeta(selectedBiomarkerTrend.trendDirection);
      const title =
        selectedBiomarkerPriority?.title ?? getBiomarkerDisplayName(selectedBiomarkerTrend.markerKey);
      return {
        label: "Trend dne",
        title,
        value: `${trendMeta.arrow} ${trendMeta.label}`,
        detail:
          selectedBiomarkerObservationComparison?.summary ??
          selectedBiomarkerObservationAction ??
          "Trend ještě čeká na srovnatelný předchozí bod, ale marker už je aktivní fokus dne.",
        footer:
          selectedBiomarkerTrend.latestValue !== null && selectedBiomarkerTrend.latestValue !== undefined
            ? `Aktuálně ${selectedBiomarkerTrend.latestValue} ${selectedBiomarkerTrend.latestUnit ?? ""}`.trim()
            : "Aktuální hodnota zatím není k dispozici",
        tone:
          selectedBiomarkerTrend.trendDirection === "up"
            ? "alert"
            : selectedBiomarkerTrend.trendDirection === "down"
              ? "calm"
              : "muted",
        chartLabel: "Mini trend biomarkeru za posledni mereni",
        actionLabel: "Otevrit biomarker fokus",
        onClick: scrollToBiomarkerPanel,
      };
    }

    if (dueFollowUps.length > 0) {
      return {
        label: "Riziko dne",
        title: dueFollowUps[0]?.title ?? "Otevřené follow-upy",
        value: `${dueFollowUps.length} otevrenych`,
        detail:
          todayFollowUps.length > 0
            ? `${todayFollowUps.length} follow-upu je splatných ještě dnes, takže je dobré je vyčistit dřív než další detailní analýzu.`
            : "Zůstávají otevřené follow-upy, i když dnes nemusí být všechny akutně splatné.",
        footer: "Nejdřív zavřete otevřené závazky a až potom rozšiřujte další denní vrstvy.",
        tone: "warm",
        chartLabel: "Mini tlak follow-upu podle nalehavosti",
        actionLabel: "Otevrit pece a reminder panel",
        onClick: scrollToCarePanel,
      };
    }

    return {
      label: "Tok dne",
      title: meals[0]?.title ?? "Klidný režim",
      value: signals[0] ? "Signal zachycen" : "Bez akutni odchylky",
      detail:
        signals[0]?.title ??
        meals[0]?.title ??
        "Den zatím nevykazuje akutní eskalaci, takže držte rytmus, check-in a krátký provozní zápis.",
      footer: "Jakmile přibude biomarker nebo follow-up tlak, trendová karta se přepne na konkrétní riziko.",
      tone: "calm",
      chartLabel: "Mini rytmus dne podle poslednich zaznamu",
      actionLabel: "Otevrit fokus odpovedi",
      onClick: scrollToResponseSidebar,
    };
  }, [
    dueFollowUps,
    meals,
    scrollToBiomarkerPanel,
    scrollToCarePanel,
    scrollToResponseSidebar,
    selectedBiomarkerObservationAction,
    selectedBiomarkerObservationComparison,
    selectedBiomarkerPriority,
    selectedBiomarkerTrend,
    signals,
    todayFollowUps.length,
  ]);
  const dashboardTrendSparkline = useMemo(() => {
    if (selectedBiomarkerTrendChart?.points.length) {
      const width = 132;
      const height = 38;
      const range = selectedBiomarkerTrendChart.max - selectedBiomarkerTrendChart.min || 1;
      const polyline = selectedBiomarkerTrendChart.points
        .map((point, index, all) => {
          const x = (index * width) / Math.max(all.length - 1, 1);
          const value = point.item.value ?? selectedBiomarkerTrendChart.min;
          const y = height - 4 - ((value - selectedBiomarkerTrendChart.min) / range) * (height - 8);
          return `${x},${y}`;
        })
        .join(" ");
      return {
        kind: "line" as const,
        width,
        height,
        polyline,
        bars: [],
      };
    }

    const series =
      dueFollowUps.length > 0
        ? [dueFollowUps.length, todayFollowUps.length, Math.max(dueFollowUps.length - todayFollowUps.length, 0)]
        : [checkIns.length, meals.length, signals.length];
    const max = Math.max(...series, 1);
    const width = 132;
    const height = 38;
    const barWidth = 24;
    const gap = 12;
    const bars = series.map((value, index) => {
      const scaledHeight = Math.max((value / max) * (height - 8), value > 0 ? 8 : 4);
      return {
        x: index * (barWidth + gap) + 6,
        y: height - scaledHeight - 4,
        width: barWidth,
        height: scaledHeight,
      };
    });
    return {
      kind: "bars" as const,
      width,
      height,
      polyline: "",
      bars,
    };
  }, [
    checkIns.length,
    dueFollowUps.length,
    meals.length,
    selectedBiomarkerTrendChart,
    signals.length,
    todayFollowUps.length,
  ]);
  const timelineSummaryItems = useMemo(
    () => [
      { label: "Check-in", value: checkIns.length },
      { label: "Jidla", value: meals.length },
      { label: "Signaly", value: signals.length },
      { label: "Follow-upy", value: todayFollowUps.length },
    ].filter((item) => item.value > 0),
    [checkIns.length, meals.length, signals.length, todayFollowUps.length],
  );
  const healthMapItems = useMemo(() => {
    return [
      {
        id: "routine",
        label: "Routine",
        tone: "routine",
        active: Boolean((briefing?.routineHighlights?.length ?? 0) || (briefing?.movementHighlights?.length ?? 0)),
        detail:
          briefing?.routineHighlights?.[0] ??
          briefing?.movementHighlights?.[0] ??
          "Dr\u017e\u00ed denn\u00ed minimum",
      },
      {
        id: "care",
        label: "Care",
        tone: "care",
        active: careRecommendations.length > 0,
        detail: careRecommendations[0]?.title ?? "Bez aktivn\u00ed priority p\u00e9\u010de",
      },
      {
        id: "biomarker",
        label: "Biomarkery",
        tone: "biomarker",
        active: (briefing?.flaggedBiomarkerCount ?? 0) > 0 || priorityBiomarkerTrends.length > 0,
        detail:
          selectedBiomarkerPriority?.title ??
          briefing?.biomarkerHighlights?.[0] ??
          "Zatím bez fokusního markeru",
      },
      {
        id: "dna",
        label: "DNA",
        tone: "dna",
        active: geneticPriorities.length > 0,
        detail: selectedGeneticPriority?.title ?? geneticPriorities[0]?.title ?? "DNA vrstva připravena",
      },
      {
        id: "meal",
        label: "Jídla",
        tone: "meal",
        active: meals.length > 0,
        detail: meals[0]?.title ?? "Zatím bez posledního jídla",
      },
      {
        id: "signal",
        label: "Signály",
        tone: "signal",
        active: signals.length > 0,
        detail: signals[0]?.title ?? "Zatím bez posledního signálu",
      },
    ];
  }, [
    briefing,
    careRecommendations,
    geneticPriorities,
    meals,
    priorityBiomarkerTrends,
    selectedBiomarkerPriority,
    selectedGeneticPriority,
    signals,
  ]);
  const biomarkerDashboardCards = useMemo(() => {
    return priorityBiomarkerTrends.slice(0, 8).map((trend) => {
      const latestObservation = latestBiomarkerObservationByKey.get(trend.markerKey);
      const statusMeta = getObservationStatusMeta(latestObservation?.status);
      const trendMeta = getTrendDirectionMeta(trend.trendDirection);
      const priority = biomarkerPriorities.find((item) => item.markerKey === trend.markerKey);
      return {
        trend,
        title: priority?.title ?? getBiomarkerDisplayName(trend.markerKey),
        statusMeta,
        trendMeta,
        latestObservation,
        isActive: selectedBiomarkerTrend?.markerKey === trend.markerKey,
      };
    });
  }, [
    biomarkerPriorities,
    latestBiomarkerObservationByKey,
    priorityBiomarkerTrends,
    selectedBiomarkerTrend,
  ]);
  const dailyTimelineItems = useMemo(() => {
    const items = [
      ...checkIns.slice(0, 3).map((item) => ({
        id: `check-in-${item.id}`,
        kind: "check_in" as const,
        title: item.checkInType === "morning" ? "Ranní check-in" : "Večerní check-in",
        detail: `Energie ${item.energy}/10, stres ${item.stress}/10, spánek ${item.sleepQuality}/10`,
        at: item.createdAt,
        linked: false,
        sourceId: item.id,
      })),
      ...meals.slice(0, 3).map((item) => ({
        id: `meal-${item.id}`,
        kind: "meal" as const,
        title: item.title,
        detail: [item.mealType, item.tags.slice(0, 2).join(" | ")].filter(Boolean).join(" • "),
        at: item.occurredAt,
        linked: selectedMealId === item.id,
        sourceId: item.id,
      })),
      ...signals.slice(0, 3).map((item) => ({
        id: `signal-${item.id}`,
        kind: "signal" as const,
        title: item.title,
        detail: `${item.category} • ${item.severity}`,
        at: item.observedAt,
        linked: false,
        sourceId: item.id,
      })),
      ...todayFollowUps.slice(0, 3).map((item) => ({
        id: `follow-up-${item.id}`,
        kind: "follow_up" as const,
        title: item.title,
        detail: item.delayLabel,
        at: item.dueAt,
        linked: false,
        sourceId: item.id,
      })),
      ...careRecommendations.slice(0, 3).map((item) => ({
        id: `care-${item.id}`,
        kind: "care" as const,
        title: item.title,
        detail: item.priority,
        at: item.nextDue ?? item.activeFrom ?? new Date().toISOString(),
        linked: selectedBiomarkerCareIds.has(item.id),
        sourceId: item.id,
      })),
    ];

    return items
      .sort((a, b) => b.at.localeCompare(a.at))
      .slice(0, 6);
  }, [careRecommendations, checkIns, meals, selectedBiomarkerCareIds, selectedMealId, signals, todayFollowUps]);

  function syncFocusFromCareRecommendation(item: CareRecommendation) {
    const linkedBiomarkerKey =
      item.relatedMarkers.find((markerKey) =>
        biomarkerTrends.some((trend) => trend.markerKey === markerKey),
      ) ??
      item.relatedMarkers.find((markerKey) =>
        biomarkerPriorities.some((priority) => priority.markerKey === markerKey),
      ) ??
      null;

    if (linkedBiomarkerKey) {
      setSelectedBiomarkerKey(linkedBiomarkerKey);
    }

    const relatedMarkerSet = new Set(item.relatedMarkers);
    const linkedGeneticKey =
      geneticPriorities.find((marker) => {
        if (marker.markerKey === "lipid_regulation") {
          return ["ldl_c", "total_cholesterol", "hdl_c", "triglycerides"].some((key) =>
            relatedMarkerSet.has(key),
          );
        }
        if (marker.markerKey === "insulin_sensitivity") {
          return ["glucose_fasting", "hba1c", "triglycerides"].some((key) => relatedMarkerSet.has(key));
        }
        if (marker.markerKey === "methylation_folate") {
          return ["homocysteine", "folate"].some((key) => relatedMarkerSet.has(key));
        }
        if (marker.markerKey === "b12_absorption") {
          return ["vitamin_b12", "homocysteine"].some((key) => relatedMarkerSet.has(key));
        }
        if (marker.markerKey === "inflammation_regulation") {
          return relatedMarkerSet.has("crp");
        }
        return false;
      })?.markerKey ?? null;

    if (linkedGeneticKey) {
      setSelectedGeneticKey(linkedGeneticKey);
    }
  }

  function syncFocusFromMealEntry(meal: MealEntry) {
    const haystack = `${meal.title} ${meal.tags.join(" ")} ${meal.notes ?? ""}`.toLowerCase();

    let linkedBiomarkerKey: string | null = null;
    let linkedGeneticKey: string | null = null;

    if (
      ["uzen", "slanina", "klobas", "salam", "mast", "syr", "smetan"].some((key) =>
        haystack.includes(key),
      )
    ) {
      linkedBiomarkerKey = ["ldl_c", "total_cholesterol", "triglycerides"].find((key) =>
        biomarkerTrends.some((trend) => trend.markerKey === key),
      ) ?? "ldl_c";
      linkedGeneticKey = "lipid_regulation";
    } else if (
      ["slad", "cukr", "ovoc", "peciv", "mouka", "med", "dzem", "juice"].some((key) =>
        haystack.includes(key),
      )
    ) {
      linkedBiomarkerKey = ["glucose_fasting", "hba1c", "triglycerides"].find((key) =>
        biomarkerTrends.some((trend) => trend.markerKey === key),
      ) ?? "glucose_fasting";
      linkedGeneticKey = "insulin_sensitivity";
    } else if (
      ["maso", "vejce", "ryba", "jatra", "tvaroh", "kefir", "jogurt"].some((key) =>
        haystack.includes(key),
      )
    ) {
      linkedBiomarkerKey = ["vitamin_b12", "homocysteine", "ferritin"].find((key) =>
        biomarkerTrends.some((trend) => trend.markerKey === key),
      ) ?? "vitamin_b12";
      linkedGeneticKey = "b12_absorption";
    } else if (
      ["listov", "spenat", "brokol", "fazole", "lusten", "zelen"].some((key) =>
        haystack.includes(key),
      )
    ) {
      linkedBiomarkerKey = ["homocysteine", "vitamin_b12", "ferritin"].find((key) =>
        biomarkerTrends.some((trend) => trend.markerKey === key),
      ) ?? "homocysteine";
      linkedGeneticKey = "methylation_folate";
    }

    if (linkedBiomarkerKey) {
      setSelectedBiomarkerKey(linkedBiomarkerKey);
    }
    if (linkedGeneticKey) {
      setSelectedGeneticKey(linkedGeneticKey);
    }
  }

  function syncFocusFromHealthSignal(signal: HealthSignal) {
    const haystack = `${signal.category} ${signal.title} ${signal.notes ?? ""}`.toLowerCase();

    let linkedBiomarkerKey: string | null = null;
    let linkedGeneticKey: string | null = null;

    if (
      signal.category === "digestion" ||
      ["nadym", "trav", "mlec", "lakt", "jogurt", "syr"].some((key) => haystack.includes(key))
    ) {
      linkedBiomarkerKey = ["glucose_fasting", "triglycerides", "vitamin_b12"].find((key) =>
        biomarkerTrends.some((trend) => trend.markerKey === key),
      ) ?? "glucose_fasting";
      linkedGeneticKey = haystack.includes("lakt") || haystack.includes("mlec") ? "lactose_tolerance" : "insulin_sensitivity";
    } else if (
      signal.category === "energy" ||
      ["unav", "energie", "vycerp", "slabost"].some((key) => haystack.includes(key))
    ) {
      linkedBiomarkerKey = ["vitamin_b12", "ferritin", "glucose_fasting", "tsh"].find((key) =>
        biomarkerTrends.some((trend) => trend.markerKey === key),
      ) ?? "vitamin_b12";
      linkedGeneticKey = biomarkerTrends.some((trend) => trend.markerKey === "vitamin_b12")
        ? "b12_absorption"
        : "insulin_sensitivity";
    } else if (
      signal.category === "sleep" ||
      ["span", "nesp", "probu", "unava"].some((key) => haystack.includes(key))
    ) {
      linkedBiomarkerKey = ["crp", "glucose_fasting", "tsh"].find((key) =>
        biomarkerTrends.some((trend) => trend.markerKey === key),
      ) ?? "tsh";
      linkedGeneticKey = "oxidative_stress_response";
    } else if (
      signal.category === "stress" ||
      ["stres", "napeti", "tlak", "neklid"].some((key) => haystack.includes(key))
    ) {
      linkedBiomarkerKey = ["crp", "glucose_fasting", "tsh"].find((key) =>
        biomarkerTrends.some((trend) => trend.markerKey === key),
      ) ?? "crp";
      linkedGeneticKey = "inflammation_regulation";
    }

    if (linkedBiomarkerKey) {
      setSelectedBiomarkerKey(linkedBiomarkerKey);
    }
    if (linkedGeneticKey) {
      setSelectedGeneticKey(linkedGeneticKey);
    }
  }

  useEffect(() => {
    let active = true;

    async function loadData() {
      const partialFailureError =
        "Nepodařilo se načíst část rozšířených dat. Základní chat a lokální běh ale zůstávají dostupné.";

      try {
        const bootstrap = await fetchBootstrap();
        const results = await Promise.allSettled([
          fetchDailyBriefing(),
          fetchMeals(),
          fetchHealthSignals(),
          fetchDailyCheckIns(),
          fetchCareRecommendations(),
          fetchBiomarkerPriorities(),
          fetchGeneticPriorities(),
          fetchBiomarkerObservations(),
          fetchBiomarkerTrends(),
          fetchMovementBlocks(),
          fetchFollowUps(),
          fetchDueFollowUps(),
          fetchTodayFollowUps(),
          fetchNotionSyncStatus(),
          fetchNotionSyncHistory(),
          fetchNotionMappingPreview("daily_check_ins"),
          fetchUzbKnowledge("dech regenerace energie"),
          fetchEvidenceKnowledge("biomarkery energie stres"),
        ]);
        if (!active) return;

        const [
          nextBriefingResult,
          nextMealsResult,
          nextSignalsResult,
          nextCheckInsResult,
          nextCareRecommendationsResult,
          nextBiomarkerPrioritiesResult,
          nextGeneticPrioritiesResult,
          nextBiomarkerObservationsResult,
          nextBiomarkerTrendsResult,
          nextMovementBlocksResult,
          nextFollowUpsResult,
          nextDueFollowUpsResult,
          nextTodayFollowUpsResult,
          nextNotionSyncStatusResult,
          nextNotionSyncHistoryResult,
          nextMappingPreviewResult,
          nextUbzKnowledgeResult,
          nextEvidenceKnowledgeResult,
        ] = results;

        const nextBriefing =
          nextBriefingResult.status === "fulfilled" ? nextBriefingResult.value : null;
        const nextMeals =
          nextMealsResult.status === "fulfilled" ? nextMealsResult.value : [];
        const nextSignals =
          nextSignalsResult.status === "fulfilled" ? nextSignalsResult.value : [];
        const nextCheckIns =
          nextCheckInsResult.status === "fulfilled" ? nextCheckInsResult.value : [];
        const nextCareRecommendations =
          nextCareRecommendationsResult.status === "fulfilled"
            ? nextCareRecommendationsResult.value
            : [];
        const nextBiomarkerPriorities =
          nextBiomarkerPrioritiesResult.status === "fulfilled"
            ? nextBiomarkerPrioritiesResult.value
            : [];
        const nextGeneticPriorities =
          nextGeneticPrioritiesResult.status === "fulfilled"
            ? nextGeneticPrioritiesResult.value
            : [];
        const nextBiomarkerObservations =
          nextBiomarkerObservationsResult.status === "fulfilled"
            ? nextBiomarkerObservationsResult.value
            : [];
        const nextBiomarkerTrends =
          nextBiomarkerTrendsResult.status === "fulfilled"
            ? nextBiomarkerTrendsResult.value
            : [];
        const nextMovementBlocks =
          nextMovementBlocksResult.status === "fulfilled"
            ? nextMovementBlocksResult.value
            : [];
        const nextFollowUps =
          nextFollowUpsResult.status === "fulfilled" ? nextFollowUpsResult.value : [];
        const nextDueFollowUps =
          nextDueFollowUpsResult.status === "fulfilled"
            ? nextDueFollowUpsResult.value
            : [];
        const nextTodayFollowUps =
          nextTodayFollowUpsResult.status === "fulfilled"
            ? nextTodayFollowUpsResult.value
            : [];
        const nextNotionSyncStatus =
          nextNotionSyncStatusResult.status === "fulfilled"
            ? nextNotionSyncStatusResult.value
            : null;
        const nextNotionSyncHistory =
          nextNotionSyncHistoryResult.status === "fulfilled"
            ? nextNotionSyncHistoryResult.value
            : [];
        const nextMappingPreview =
          nextMappingPreviewResult.status === "fulfilled"
            ? nextMappingPreviewResult.value
            : null;
        const nextUbzHits =
          nextUbzKnowledgeResult.status === "fulfilled"
            ? nextUbzKnowledgeResult.value.hits
            : [];
        const nextEvidenceHits =
          nextEvidenceKnowledgeResult.status === "fulfilled"
            ? nextEvidenceKnowledgeResult.value.hits
            : [];

        setState({
          profile: bootstrap.profile,
          rules: bootstrap.rules,
          conversation: bootstrap.conversation,
          messages: bootstrap.messages,
          answer: bootstrap.answer,
        });
        setBriefing(nextBriefing);
        setMeals(nextMeals);
        setSignals(nextSignals);
        setCheckIns(nextCheckIns);
        setCareRecommendations(nextCareRecommendations);
        setBiomarkerPriorities(nextBiomarkerPriorities);
        setGeneticPriorities(nextGeneticPriorities);
        setBiomarkerObservations(nextBiomarkerObservations);
        setBiomarkerTrends(nextBiomarkerTrends);
        setSelectedBiomarkerKey(
          nextBiomarkerPriorities.find((item) =>
            nextBiomarkerTrends.some((trend) => trend.markerKey === item.markerKey),
          )?.markerKey ??
            nextBiomarkerTrends[0]?.markerKey ??
            null,
        );
        setSelectedGeneticKey(nextGeneticPriorities[0]?.markerKey ?? null);
        setMovementBlocks(nextMovementBlocks);
        setFollowUps(nextFollowUps);
        setDueFollowUps(nextDueFollowUps);
        setTodayFollowUps(nextTodayFollowUps);
        setNotionSyncStatus(nextNotionSyncStatus);
        setNotionSyncHistory(nextNotionSyncHistory);
        setMappingPreview(nextMappingPreview);
        setUbzHits(nextUbzHits);
        setEvidenceHits(nextEvidenceHits);
        setError(
          results.some((result) => result.status === "rejected")
            ? partialFailureError
            : null,
        );
        return;
      } catch {
        if (!active) return;
        setError("Backend zatím není dostupný. Zkontrolujte API na 127.0.0.1:8000.");
        setIsLoading(false);
        return;
      }
    }

    loadData();

    return () => {
      active = false;
    };
  }, []);

  async function refreshBriefingAndSyncStatus() {
    const [nextBriefing, nextNotionSyncStatus, nextNotionSyncHistory, nextMappingPreview, nextCareRecommendations, nextFollowUps, nextDueFollowUps, nextTodayFollowUps] = await Promise.all([
      fetchDailyBriefing(),
      fetchNotionSyncStatus(),
      fetchNotionSyncHistory(),
      fetchNotionMappingPreview(previewSource),
      fetchCareRecommendations(),
      fetchFollowUps(),
      fetchDueFollowUps(),
      fetchTodayFollowUps(),
    ]);
    setBriefing(nextBriefing);
    setNotionSyncStatus(nextNotionSyncStatus);
    setNotionSyncHistory(nextNotionSyncHistory);
    setMappingPreview(nextMappingPreview);
    setCareRecommendations(nextCareRecommendations);
    setFollowUps(nextFollowUps);
    setDueFollowUps(nextDueFollowUps);
    setTodayFollowUps(nextTodayFollowUps);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!input.trim() || isSubmitting) return;

    const nextUserMessage: ChatMessage = {
      id: `msg-user-${Date.now()}`,
      conversationId: state.conversation.id,
      role: "user",
      content: input.trim(),
      createdAt: new Date().toISOString(),
    };

    setIsSubmitting(true);
    setError(null);
    setState((current) => ({
      ...current,
      messages: [...current.messages, nextUserMessage],
    }));

    try {
      const result = await sendChatMessage(state.conversation.id, nextUserMessage.content);
      const nextUbzKnowledge = await fetchUzbKnowledge(nextUserMessage.content);
      const nextEvidenceKnowledge = await fetchEvidenceKnowledge(nextUserMessage.content);
      setState((current) => ({
        ...current,
        conversation: result.conversation,
        messages: [...current.messages, result.assistantMessage],
        answer: result.answer,
      }));
      setUbzHits(nextUbzKnowledge.hits);
      setEvidenceHits(nextEvidenceKnowledge.hits);
      setInput("");
    } catch {
      setError("Nepodarilo se spojit s backendem. Zkontrolujte API a zkuste to znovu.");
      setState((current) => ({
        ...current,
        messages: current.messages.filter((message) => message.id !== nextUserMessage.id),
      }));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleMealSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedMealTitle = normalizeMealTitleInput(mealTitle);
    if (!normalizedMealTitle || isSavingMeal) return;

    setIsSavingMeal(true);
    setError(null);
    try {
      const created = await createMeal({
        mealType,
        title: normalizedMealTitle,
        notes: mealNotes.trim() || null,
        tags: mealTags.split(",").map((tag) => tag.trim()).filter(Boolean),
      });
      const suggestion = await createMealFollowUp(created.id);
      setMeals((current) => [created, ...current]);
      setFollowUps((current) => [suggestion, ...current]);
      setTodayFollowUps((current) => [suggestion, ...current]);
      await refreshBriefingAndSyncStatus();
      setMealTitle("");
      setMealNotes("");
      setMealTags("");
    } catch {
      setError("Nepodarilo se ulozit jidlo.");
    } finally {
      setIsSavingMeal(false);
    }
  }

  async function handleSignalSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!signalTitle.trim() || isSavingSignal) return;

    setIsSavingSignal(true);
    setError(null);
    try {
      const created = await createHealthSignal({
        category: signalCategory,
        title: signalTitle.trim(),
        severity: signalSeverity,
        notes: signalNotes.trim() || null,
      });
      const suggestion = await createHealthSignalFollowUp(created.id);
      setSignals((current) => [created, ...current]);
      setFollowUps((current) => [suggestion, ...current]);
      setTodayFollowUps((current) => [suggestion, ...current]);
      if (suggestion.delayLabel.includes("60-90")) {
        setDueFollowUps((current) => [suggestion, ...current]);
      }
      await refreshBriefingAndSyncStatus();
      setSignalTitle("");
      setSignalNotes("");
    } catch {
      setError("Nepodarilo se ulozit zdravotni signal.");
    } finally {
      setIsSavingSignal(false);
    }
  }

  async function handleDeleteMeal(mealId: string) {
    if (deletingMealId) return;

    setDeletingMealId(mealId);
    setError(null);
    try {
      await deleteMeal(mealId);
      setMeals((current) => current.filter((item) => item.id !== mealId));
      setFollowUps((current) =>
        current.filter((item) => !(item.triggerType === "meal" && item.relatedId === mealId)),
      );
      setTodayFollowUps((current) =>
        current.filter((item) => !(item.triggerType === "meal" && item.relatedId === mealId)),
      );
      setDueFollowUps((current) =>
        current.filter((item) => !(item.triggerType === "meal" && item.relatedId === mealId)),
      );
      await refreshBriefingAndSyncStatus();
    } catch {
      setError("Nepodarilo se smazat jidlo.");
    } finally {
      setDeletingMealId(null);
    }
  }

  async function handleDeleteSignal(signalId: string) {
    if (deletingSignalId) return;

    setDeletingSignalId(signalId);
    setError(null);
    try {
      await deleteHealthSignal(signalId);
      setSignals((current) => current.filter((item) => item.id !== signalId));
      setFollowUps((current) =>
        current.filter((item) => !(item.triggerType === "health_signal" && item.relatedId === signalId)),
      );
      setTodayFollowUps((current) =>
        current.filter((item) => !(item.triggerType === "health_signal" && item.relatedId === signalId)),
      );
      setDueFollowUps((current) =>
        current.filter((item) => !(item.triggerType === "health_signal" && item.relatedId === signalId)),
      );
      await refreshBriefingAndSyncStatus();
    } catch {
      setError("Nepodarilo se smazat signal.");
    } finally {
      setDeletingSignalId(null);
    }
  }

  async function handleCheckInSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSavingCheckIn) return;

    setIsSavingCheckIn(true);
    setError(null);
    try {
      const created = await createDailyCheckIn({
        checkInType,
        energy,
        stress,
        sleepQuality,
        notes: checkInNotes.trim() || null,
      });
      const suggestion = await createDailyCheckInFollowUp(created.id);
      setCheckIns((current) => [created, ...current]);
      setFollowUps((current) => [suggestion, ...current]);
      setTodayFollowUps((current) => [suggestion, ...current]);
      await refreshBriefingAndSyncStatus();
      setCheckInNotes("");
    } catch {
      setError("Nepoda?ilo se ulo?it daily check-in.");
    } finally {
      setIsSavingCheckIn(false);
    }
  }

  async function handleCompleteFollowUp(followUpId: string) {
    if (completingId) return;
    setCompletingId(followUpId);
    setError(null);
    try {
      const completed = await completeFollowUp(followUpId);
      setFollowUps((current) => current.map((item) => (item.id === completed.id ? completed : item)));
      setDueFollowUps((current) => current.filter((item) => item.id !== completed.id));
      setTodayFollowUps((current) => current.filter((item) => item.id !== completed.id));
      await refreshBriefingAndSyncStatus();
    } catch {
      setError("Nepoda?ilo se ozna?it follow-up jako hotov?.");
    } finally {
      setCompletingId(null);
    }
  }

  async function handleCreateCareFollowUp(recommendationId: string) {
    if (isCreatingCareFollowUp) return;
    setIsCreatingCareFollowUp(recommendationId);
    setError(null);
    try {
      await createCareRecommendationFollowUp(recommendationId);
      await refreshBriefingAndSyncStatus();
    } catch {
      setError("Nepoda?ilo se vytvo?it reminder k doporu?en? doktorky.");
    } finally {
      setIsCreatingCareFollowUp(null);
    }
  }

  async function handleNotionSync(
    source:
      | "daily_check_ins"
      | "health_signals"
      | "follow_ups"
      | "care_recommendations"
      | "biomarker_reports"
      | "biomarker_trends"
      | "genetic_profile"
      | "genetic_markers",
  ) {
    if (syncingSource) return;
    setSyncingSource(source);
    setError(null);
    try {
      const result =
        source === "daily_check_ins"
          ? await syncDailyCheckInsToNotion()
          : source === "health_signals"
            ? await syncHealthSignalsToNotion()
            : source === "follow_ups"
              ? await syncFollowUpsToNotion()
              : source === "care_recommendations"
                ? await syncCareRecommendationsToNotion()
                : source === "biomarker_reports"
                  ? await syncBiomarkerReportsToNotion()
                  : source === "biomarker_trends"
                    ? await syncBiomarkerTrendsToNotion()
                    : source === "genetic_profile"
                      ? await syncGeneticProfileToNotion()
                      : await syncGeneticMarkersToNotion();
      setLastSyncResult(result);
      const [nextStatus, nextHistory, nextPreview] = await Promise.all([
        fetchNotionSyncStatus(),
        fetchNotionSyncHistory(),
        fetchNotionMappingPreview(previewSource),
      ]);
      setNotionSyncStatus(nextStatus);
      setNotionSyncHistory(nextHistory);
      setMappingPreview(nextPreview);
    } catch {
      setError("Nepodarilo se provest Notion sync.");
    } finally {
      setSyncingSource(null);
    }
  }

  async function handleSyncAllToNotion() {
    if (syncingSource) return;
    setSyncingSource("all");
    setError(null);
    try {
      const results: NotionSyncResult[] = [];
      results.push(await syncDailyCheckInsToNotion());
      results.push(await syncHealthSignalsToNotion());
      results.push(await syncFollowUpsToNotion());
      results.push(await syncDailySummaryToNotion());
      results.push(await syncCareRecommendationsToNotion());
      results.push(await syncBiomarkerReportsToNotion());
      results.push(await syncBiomarkerTrendsToNotion());
      results.push(await syncGeneticProfileToNotion());
      results.push(await syncGeneticMarkersToNotion());
      setLastSyncAllResults(results);
      setLastSyncResult(results[results.length - 1] ?? null);
      const [nextStatus, nextHistory, nextPreview] = await Promise.all([
        fetchNotionSyncStatus(),
        fetchNotionSyncHistory(),
        fetchNotionMappingPreview(previewSource),
      ]);
      setNotionSyncStatus(nextStatus);
      setNotionSyncHistory(nextHistory);
      setMappingPreview(nextPreview);
    } catch {
      setError("Nepodarilo se provest Synchronizovat vše do Notion.");
    } finally {
      setSyncingSource(null);
    }
  }

  async function handleSaveDailySummaryToNotion() {
    if (isSavingDailySummary) return;
    setIsSavingDailySummary(true);
    setError(null);
    try {
      const result = await syncDailySummaryToNotion();
      setLastSyncResult(result);
      const [nextStatus, nextHistory, nextPreview] = await Promise.all([
        fetchNotionSyncStatus(),
        fetchNotionSyncHistory(),
        fetchNotionMappingPreview(previewSource),
      ]);
      setNotionSyncStatus(nextStatus);
      setNotionSyncHistory(nextHistory);
      setMappingPreview(nextPreview);
    } catch {
      setError("Nepodarilo se ulozit daily summary do Notion.");
    } finally {
      setIsSavingDailySummary(false);
    }
  }

  async function handlePreviewSourceChange(
    source:
      | "daily_check_ins"
      | "health_signals"
      | "follow_ups"
      | "daily_summary"
      | "care_recommendations"
      | "biomarker_reports"
      | "biomarker_trends"
      | "genetic_profile"
      | "genetic_markers",
  ) {
    setPreviewSource(source);
    try {
      setMappingPreview(await fetchNotionMappingPreview(source));
    } catch {
      setError("Nepodarilo se nacist mapping preview.");
    }
  }

  async function handleUzbSync() {
    setError(null);
    try {
      const result = await syncUzbKnowledge();
      setUbzSyncResult(result);
      const nextUbzKnowledge = await fetchUzbKnowledge("dech regenerace energie ubz");
      setUbzHits(nextUbzKnowledge.hits);
    } catch {
      setError("Nepodarilo se provest UBZ Notion sync.");
    }
  }

  async function handleEvidenceSync() {
    setError(null);
    try {
      const result = await syncEvidenceKnowledge();
      setEvidenceSyncResult(result);
      const nextEvidenceKnowledge = await fetchEvidenceKnowledge("biomarkery energie stres");
      setEvidenceHits(nextEvidenceKnowledge.hits);
    } catch {
      setError("NepodaÅilo se provÃ©st evidence Notion sync.");
    }
  }

  async function handleKnowledgeSyncAll() {
    if (isSyncingKnowledgeAll) return;
    setIsSyncingKnowledgeAll(true);
    setError(null);
    try {
      const [ubzResult, evidenceResult] = await Promise.all([
        syncUzbKnowledge(),
        syncEvidenceKnowledge(),
      ]);
      setUbzSyncResult(ubzResult);
      setEvidenceSyncResult(evidenceResult);
      const [nextUbzKnowledge, nextEvidenceKnowledge] = await Promise.all([
        fetchUzbKnowledge("dech regenerace energie ubz"),
        fetchEvidenceKnowledge("biomarkery energie stres"),
      ]);
      setUbzHits(nextUbzKnowledge.hits);
      setEvidenceHits(nextEvidenceKnowledge.hits);
    } catch {
      setError("NepodaÅilo se provÃ©st synchronizaci celÃ© znalostnÃ­ vrstvy.");
    } finally {
      setIsSyncingKnowledgeAll(false);
    }
  }

  function scrollToCheckInPanel() {
    checkInPanelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function scrollToDashboardPanel() {
    dashboardPanelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function scrollToResponseSidebar() {
    responseSidebarRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function applyQuickPrompt(prompt: string) {
    setInput(prompt);
    chatInputRef.current?.focus();
  }

  function applyMealTestScenario(scenario: (typeof MEAL_TEST_SCENARIOS)[number]) {
    setMealTitle(scenario.title);
    setMealType(scenario.mealType);
    setMealTags(scenario.tags);
    setMealNotes(scenario.notes);
  }

  function applySignalTestScenario(scenario: (typeof SIGNAL_TEST_SCENARIOS)[number]) {
    setSignalTitle(scenario.title);
    setSignalCategory(scenario.category);
    setSignalSeverity(scenario.severity);
    setSignalNotes(scenario.notes);
  }

  function applyCheckInTestScenario(scenario: (typeof CHECK_IN_TEST_SCENARIOS)[number]) {
    setCheckInType(scenario.type);
    setEnergy(scenario.energy);
    setStress(scenario.stress);
    setSleepQuality(scenario.sleepQuality);
    setCheckInNotes(scenario.notes);
  }

  function askAboutLatestMeal() {
    const latestMealTitle = meals[0]?.title?.trim();
    if (latestMealTitle) {
      applyQuickPrompt(
        `Dal jsem si ${latestMealTitle}. Je to pro me dnes v pohode? Jak souvisi moje posledni jidlo s B12, homocysteinem a ferritinem?`,
      );
      return;
    }

    applyQuickPrompt(MEAL_TEST_SCENARIOS[0].followUpPrompt);
  }

  function askAboutLatestSignal() {
    const latestSignalTitle = signals[0]?.title?.trim();
    if (latestSignalTitle) {
      applyQuickPrompt(
        `Mam dnes signal '${latestSignalTitle}'. Jak to cist pres aktualni stav dne, biomarkery a prakticky dalsi krok?`,
      );
      return;
    }

    applyQuickPrompt(SIGNAL_TEST_SCENARIOS[0].followUpPrompt);
  }

  function askAboutLatestCheckIn() {
    const latestCheckIn = checkIns[0];
    if (latestCheckIn) {
      applyQuickPrompt(
        `Udelal jsem ${latestCheckIn.checkInType === "morning" ? "ranni" : "vecerni"} check-in. Co je pro me ted nejpraktictejsi dalsi krok podle energie, stresu a spanku?`,
      );
      return;
    }

    applyQuickPrompt(CHECK_IN_TEST_SCENARIOS[0].followUpPrompt);
  }

  function scrollToCarePanel() {
    carePanelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function scrollToBiomarkerPanel() {
    biomarkerPanelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function openIntegrationPanel() {
    if (integrationPanelRef.current) {
      integrationPanelRef.current.open = true;
      integrationPanelRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  function handleExecutivePulseClick(cardId: string) {
    if (cardId === "day") {
      scrollToDashboardPanel();
      return;
    }

    if (cardId === "biomarker") {
      if (!selectedBiomarkerKey && priorityBiomarkerTrends[0]) {
        setSelectedBiomarkerKey(priorityBiomarkerTrends[0].markerKey);
      }
      scrollToBiomarkerPanel();
      return;
    }

    if (cardId === "care") {
      if (careRecommendations[0]) {
        syncFocusFromCareRecommendation(careRecommendations[0]);
      }
      scrollToCarePanel();
      return;
    }

    openIntegrationPanel();
  }

  return (
    <main className="page-shell" ref={rootRef}>
      <section className="hero">
        <div className="hero-header">
          <div className="hero-copy">
            <span className="hero-kicker">Longevity cockpit</span>
            <h1>{"Denn\u00ed asisten\u010dn\u00ed kokpit"}</h1>
            <p>
              {"Praktick\u00fd denn\u00ed p\u0159ehled nad biomarkery, DNA, vrstvou p\u00e9\u010de, j\u00eddlem, sign\u00e1ly a follow-upy."}
            </p>
          </div>
          <div className="hero-status">
            <span className="hero-status-label">{"Aktivn\u00ed fokus"}</span>
            <strong>{selectedBiomarkerPriority?.title ?? briefing?.priorities?.[0] ?? "Denn\u00ed rytmus"}</strong>
            <span>{activeFocusPath.length ? activeFocusPath.join(" -> ") : "Fokus se skl\u00e1d\u00e1 z aktivn\u00edch vrstev dne."}</span>
          </div>
        </div>
        <div className="meta-line">
          <span className="meta-pill">{isLoading ? "Na\u010d\u00edt\u00e1m bootstrap" : "Bootstrap na\u010dten"}</span>
          {state.rules ? <span className="meta-pill">{"Režim hlasu: "}{state.rules.voiceMode}</span> : null}
          {state.profile ? <span className="meta-pill">Profil: {state.profile.displayName}</span> : null}
          <span className="meta-pill">{"Jídla: "}{meals.length}</span>
          <span className="meta-pill">{"Signály: "}{signals.length}</span>
          <span className="meta-pill">{"Check-iny: "}{checkIns.length}</span>
          <span className="meta-pill">Dnes: {todayFollowUps.length}</span>
          <span className="meta-pill">{"Te\u010f: "}{dueFollowUps.length}</span>
        </div>
        <div className="dashboard-card-grid executive-pulse-grid">
          {executivePulseCards.map((card) => (
            <button
              key={card.id}
              type="button"
              className={`mini-card dashboard-card dashboard-card-${card.tone} executive-pulse-card executive-pulse-button`}
              onClick={() => handleExecutivePulseClick(card.id)}
            >
              <span className="dashboard-card-label">{card.label}</span>
              <strong>{card.value}</strong>
              <span>{card.detail}</span>
            </button>
          ))}
        </div>
        {error ? <div className="mini-card error-card">{error}</div> : null}
      </section>

      <section className="panel stack dashboard-panel" ref={dashboardPanelRef}>
        <div className="dashboard-heading">
          <div className="stack">
            <span className="hero-kicker">{"Denn\u00ed dashboard"}</span>
            <h2>{briefing?.headline ?? "Denn\u00ed briefing"}</h2>
            <p className="dashboard-summary">{briefing?.summary ?? "Briefing se na\u010d\u00edt\u00e1."}</p>
          </div>
          <div className="chips">
            <button className="chat-button" type="button" onClick={handleSaveDailySummaryToNotion} disabled={isSavingDailySummary}>
              {isSavingDailySummary ? "Ukl\u00e1d\u00e1m denn\u00ed souhrn" : "Ulo\u017eit denn\u00ed souhrn do Notion"}
            </button>
          </div>
        </div>
        <div className="meta-line">
          <span className="meta-pill">Dnes: {briefing?.dueTodayCount ?? 0}</span>
          <span className="meta-pill">{"Te\u010f: "}{briefing?.dueNowCount ?? 0}</span>
          <span className="meta-pill">{"Co hl\u00eddat v biomarkerech: "}{briefing?.flaggedBiomarkerCount ?? 0}</span>
          <span className="meta-pill">{"Doporu\u010den\u00ed p\u00e9\u010de: "}{briefing?.activeCareRecommendationCount ?? 0}</span>
          {briefing?.latestCheckInType ? (
            <span className="meta-pill">
              {"Posledn\u00ed check-in: "}{briefing.latestCheckInType}{" / energie "}{briefing.latestCheckInEnergy ?? "-"}
            </span>
          ) : null}
        </div>
        <div className="dashboard-overview-grid">
          <div className="mini-card dashboard-decision-card">
            <span className="dashboard-card-label">Co dnes rozhoduje</span>
            <strong>{dashboardDecisionSummary.headline}</strong>
            <span>{dashboardDecisionSummary.context}</span>
            <span className="dashboard-decision-path">{dashboardDecisionSummary.support}</span>
            <div className="dashboard-list">
              {dashboardDecisionSummary.actions.map((item) => (
                <span key={item} className="dashboard-list-item">
                  {item}
                </span>
              ))}
            </div>
            <div className="chips">
              <button className="chat-button" type="button" onClick={scrollToResponseSidebar}>
                Otevrit fokus odpovedi
              </button>
              <button className="chat-button" type="button" onClick={scrollToCheckInPanel}>
                Zapsat dalsi stav dne
              </button>
            </div>
          </div>
          <div className="mini-card dashboard-snapshot-card">
            <span className="dashboard-card-label">Operativni snapshot</span>
            <strong>At-a-glance prehled</strong>
            <div className="dashboard-snapshot-grid">
              {operationalSnapshotItems.map((item) => (
                <div key={item.label} className={`dashboard-snapshot-item tone-${item.tone}`}>
                  <span className="dashboard-card-label">{item.label}</span>
                  <strong>{item.value}</strong>
                  <span>{item.detail}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="dashboard-card-grid">
          {dashboardCards.map((card) => (
            <div key={card.id} className={`mini-card dashboard-card dashboard-card-${card.tone}`}>
              <span className="dashboard-card-label">{card.label}</span>
              <strong>{card.value}</strong>
              <span>{card.detail}</span>
            </div>
          ))}
        </div>
        <div className="mini-card production-test-card">
          <div className="production-test-heading">
            <div className="stack">
              <span className="dashboard-card-label">Production sanity check</span>
              <strong>{productionTestStatus.completedCount}/3 flow dnes otestovano</strong>
              <span>
                Rychly prehled nad lokalnimi runtime zaznamy bez nutnosti prochazet cele operativni panely.
              </span>
            </div>
            <button className="chat-button" type="button" onClick={scrollToCheckInPanel}>
              Otevrit operativu
            </button>
          </div>
          <div className="production-test-grid">
            {productionTestStatus.items.map((item) => (
              <div
                key={item.id}
                className={`production-test-item production-test-item-${item.tone}`}
              >
                <span className="dashboard-card-label">{item.label}</span>
                <strong>{item.status}</strong>
                <span>{item.detail}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="mini-card flow-visual-card">
          <div className="flow-visual-heading">
            <div className="stack">
              <span className="dashboard-card-label">Dnesni operativni vrstva</span>
              <strong>Jak je den rozepsany napric vrstvami</strong>
              <span>
                Pocet dnesnich zapisů a follow-upu prevedeny do jednoduche vizualni matice pro rychle cteni rytmu dne.
              </span>
            </div>
          </div>
          <div className="flow-visual-grid">
            {operationalFlowCards.map((card) => (
              <div key={card.id} className={`flow-visual-item tone-${card.tone}`}>
                <span className="dashboard-card-label">{card.label}</span>
                <strong>{card.count}</strong>
                <span>{card.status}</span>
                <div className="flow-visual-meter" aria-hidden="true">
                  <div
                    className={`flow-visual-meter-fill tone-${card.tone}`}
                    style={{ width: `${card.percent}%` }}
                  />
                </div>
                <span>{card.detail}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="mini-card health-map-card">
          <strong>{"Dne\u0161n\u00ed vrstvy"}</strong>
          <div className="health-map-grid">
            {healthMapItems.map((item) => (
              <div
                key={item.id}
                className={`health-map-item health-map-item-${item.tone} ${item.active ? "is-active" : ""}`}
              >
                <span className="dashboard-card-label">{item.label}</span>
                <strong>{item.active ? "Aktivn\u00ed" : "Klidn\u00e9"}</strong>
                <span>{item.detail}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="dashboard-columns">
          <div className="stack">
            <div className="mini-card">
              <strong>{"Te\u010f ud\u011blej"}</strong>
              <div className="dashboard-list">
                {immediateActions.map((priority) => (
                  <span key={priority} className="dashboard-list-item">
                    {priority}
                  </span>
                ))}
              </div>
            </div>
            {(briefing?.biomarkerHighlights?.length ?? 0) > 0 ? (
              <div className="mini-card">
                <strong>{"Co dnes \u010d\u00edst v datech"}</strong>
                <div className="dashboard-list">
                  {briefing?.biomarkerHighlights.slice(0, 4).map((highlight) => (
                    <span key={highlight} className="dashboard-list-item">
                      {highlight}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
            {(briefing?.routineHighlights?.length ?? 0) > 0 || (briefing?.movementGuardrails?.length ?? 0) > 0 ? (
              <div className="mini-card">
                <strong>{"Jak dr\u017eet re\u017eim"}</strong>
                <div className="dashboard-list">
                  {(briefing?.routineHighlights ?? []).slice(0, 2).map((highlight) => (
                    <span key={highlight} className="dashboard-list-item">
                      {highlight}
                    </span>
                  ))}
                  {(briefing?.movementGuardrails ?? []).slice(0, 2).map((guardrail) => (
                    <span key={guardrail} className="dashboard-list-item">
                      {guardrail}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
          <div className="mini-card timeline-card">
            <span className="dashboard-card-label">{dashboardTrendSummary.label}</span>
            <strong>{dashboardTrendSummary.title}</strong>
            <div className={`dashboard-trend-strip tone-${dashboardTrendSummary.tone}`}>
              <strong>{dashboardTrendSummary.value}</strong>
              <span>{dashboardTrendSummary.footer}</span>
            </div>
            <div className="dashboard-trend-visual">
              <svg
                className="dashboard-trend-sparkline"
                viewBox={`0 0 ${dashboardTrendSparkline.width} ${dashboardTrendSparkline.height}`}
                role="img"
                aria-label={dashboardTrendSummary.chartLabel}
              >
                {dashboardTrendSparkline.kind === "line" ? (
                  <polyline
                    className={`dashboard-trend-line tone-${dashboardTrendSummary.tone}`}
                    points={dashboardTrendSparkline.polyline}
                  />
                ) : (
                  dashboardTrendSparkline.bars.map((bar) => (
                    <rect
                      key={`${bar.x}-${bar.height}`}
                      className={`dashboard-trend-bar tone-${dashboardTrendSummary.tone}`}
                      x={bar.x}
                      y={bar.y}
                      width={bar.width}
                      height={bar.height}
                      rx="4"
                    />
                  ))
                )}
              </svg>
            </div>
            <span>{dashboardTrendSummary.detail}</span>
            <div className="chips">
              <button className="chat-button" type="button" onClick={dashboardTrendSummary.onClick}>
                {dashboardTrendSummary.actionLabel}
              </button>
            </div>
            <div className="timeline-summary-row">
              {(timelineSummaryItems.length ? timelineSummaryItems : [{ label: "Zatim", value: 0 }]).map((item) => (
                <span key={item.label} className="timeline-summary-pill">
                  {item.label}: {item.value}
                </span>
              ))}
            </div>
            <strong>Timeline dne</strong>
            <span className="timeline-caption">Poslednich 6 udalosti napric aktivnimi vrstvami dne.</span>
            <div className="timeline-list">
              {dailyTimelineItems.length ? (
                dailyTimelineItems.map((item) => {
                  const meta = getTimelineKindMeta(item.kind);
                  return (
                  <div
                    key={item.id}
                    className={`timeline-item timeline-item-${meta.tone} ${item.linked ? "is-linked" : ""}`}
                  >
                    <div className="timeline-dot" aria-hidden="true">
                      {meta.icon}
                    </div>
                    <div className="timeline-content">
                      <span className="timeline-meta">
                        {new Date(item.at).toLocaleString("cs-CZ")} • {meta.label}
                      </span>
                      <strong>{item.title}</strong>
                      <span>{item.detail}</span>
                      {item.kind === "meal" ? (
                        <button
                          className="chat-button"
                          type="button"
                          onClick={() => {
                            const meal = meals.find((entry) => entry.id === item.sourceId);
                            if (meal) syncFocusFromMealEntry(meal);
                          }}
                        >
                          Otevřít fokus
                        </button>
                      ) : null}
                      {item.kind === "signal" ? (
                        <button
                          className="chat-button"
                          type="button"
                          onClick={() => {
                            const signal = signals.find((entry) => entry.id === item.sourceId);
                            if (signal) syncFocusFromHealthSignal(signal);
                          }}
                        >
                          Otevřít fokus
                        </button>
                      ) : null}
                      {item.kind === "care" ? (
                        <button
                          className="chat-button"
                          type="button"
                          onClick={() => {
                            const recommendation = careRecommendations.find((entry) => entry.id === item.sourceId);
                            if (recommendation) syncFocusFromCareRecommendation(recommendation);
                          }}
                        >
                          Otevřít fokus
                        </button>
                      ) : null}
                    </div>
                  </div>
                )})
              ) : (
                <span>{"Timeline se zaÄne plnit z check-inÅ¯, jÃ­del, signÃ¡lÅ¯ a reminderÅ¯."}</span>
              )}
            </div>
          </div>
        </div>
        {careRecommendations.length > 0 ? (
          <div className="stack" ref={carePanelRef}>
            <div className="mini-card workflow-primary-action-card">
              <span className="dashboard-card-label">Hlavni akce panelu</span>
              <strong>Vytvorit reminder z prvni pece</strong>
              <span>
                Jakmile je doporuceni potvrzene jako relevantni pro dnesek, prevedte ho jednim klikem do follow-upu.
              </span>
              <button
                className="chat-button"
                type="button"
                onClick={() => handleCreateCareFollowUp(careRecommendations[0].id)}
                disabled={isCreatingCareFollowUp === careRecommendations[0].id}
              >
                {isCreatingCareFollowUp === careRecommendations[0].id
                  ? "Vytvarim reminder"
                  : "Vytvorit reminder z prvni pece"}
              </button>
            </div>
            <div className="dashboard-columns">
              <div className="stack">
              {careRecommendations.slice(0, 2).map((item) => (
                <div className={`mini-card ${selectedBiomarkerCareIds.has(item.id) ? "is-linked" : ""}`} key={item.id}>
                  <strong>{item.title}</strong>
                  <span>Zdroj: {item.source}</span>
                  <span>Priorita: {item.priority}</span>
                  {item.nextDue ? <span>{"Další kontrola: "}{new Date(item.nextDue).toLocaleDateString("cs-CZ")}</span> : null}
                  <span>{item.recommendation}</span>
                  <div className="chips">
                    <button
                      className={`chat-button ${selectedBiomarkerCareIds.has(item.id) ? "is-active" : ""}`}
                      type="button"
                      onClick={() => syncFocusFromCareRecommendation(item)}
                    >
                      OtevÅÃ­t navÃ¡zanÃ½ fokus
                    </button>
                    <button
                      className="chat-button"
                      type="button"
                      onClick={() => handleCreateCareFollowUp(item.id)}
                      disabled={isCreatingCareFollowUp === item.id}
                    >
                      {isCreatingCareFollowUp === item.id ? "Vytvářím reminder" : "Vytvořit reminder"}
                    </button>
                  </div>
                </div>
              ))}
            </div>
            {movementBlocks.length > 0 ? (
              <div className="mini-card">
                <strong>{"PÅipravenÃ© pohybovÃ© bloky"}</strong>
                {movementBlocks.slice(0, 2).map((block) => (
                  <div key={block.id} className="dashboard-block-detail">
                    <span>{block.title}</span>
                    <span>Minimum: {block.minimumVariant.join(" | ")}</span>
                    <span>PlnÃ¡ verze: {block.fullVariant.join(" | ")}</span>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
          </div>
        ) : null}
      </section>

      <details className="panel stack collapsible-panel" ref={integrationPanelRef}>
        <summary className="collapsible-summary">
          <span>{"Integrace a synchronizace"}</span>
          <span className="meta-pill">{"Notion + znalostnÃ­ vrstva"}</span>
        </summary>
        <div className="meta-line">
          <span className="meta-pill">
            Poslední sync: {notionSyncStatus?.lastSyncAt ? new Date(notionSyncStatus.lastSyncAt).toLocaleString("cs-CZ") : "zatím ne"}
          </span>
          <span className="meta-pill">{"Outbox: "}{notionSyncStatus?.outboxDir ?? "není připraven"}</span>
        </div>
        <div className="mini-card workflow-primary-action-card">
          <span className="dashboard-card-label">Hlavni akce panelu</span>
          <strong>Synchronizovat vse do Notion</strong>
          <span>
            Kdyz chcete poslat sdileny nebo archivni stav ven z aplikace, tohle je hlavni produkcni krok.
          </span>
          <button className="chat-button" type="button" onClick={handleSyncAllToNotion} disabled={syncingSource !== null}>
            {syncingSource === "all" ? "Synchronizuji vse" : "Synchronizovat vse do Notion"}
          </button>
        </div>
        <div className="mini-card release-readiness-card">
          <div className="release-readiness-heading">
            <div className="stack">
              <span className="dashboard-card-label">Production readiness checklist</span>
              <strong>
                {productionReadinessChecklist.autoReadyCount}/{productionReadinessChecklist.autoItemCount} automatickych gate ready
              </strong>
              <span>
                Pred releasem zkontrolujte runtime flow, sync audit, knowledge vrstvu a nakonec pustte eval suite.
              </span>
            </div>
            <span className="meta-pill">Manual gate: eval:production</span>
          </div>
          <div className="release-readiness-grid">
            {productionReadinessChecklist.items.map((item) => (
              <div key={item.id} className={`release-readiness-item tone-${item.tone}`}>
                <span className="dashboard-card-label">{item.label}</span>
                <strong>{item.status}</strong>
                <span>{item.detail}</span>
                {"actionLabel" in item && item.actionLabel && "onClick" in item && item.onClick ? (
                  <button className="chat-button" type="button" onClick={item.onClick}>
                    {item.actionLabel}
                  </button>
                ) : null}
                {item.id === "eval" ? <code>npm run eval:production</code> : null}
              </div>
            ))}
          </div>
        </div>
        <div className="mini-card layer-clarity-card">
          <div className="layer-clarity-header">
            <div className="stack">
              <span className="dashboard-card-label">Workflow clarity</span>
              <strong>Co je runtime, co je sync a co je jen knowledge vrstva</strong>
              <span>
                Tahle mapa oddeluje bezny provozni zapis dne od sdileneho Notion vystupu a od znalostni vrstvy pro vyklad.
              </span>
            </div>
          </div>
          <div className="layer-clarity-grid">
            {layerClarityCards.map((card) => (
              <div key={card.id} className={`layer-clarity-column tone-${card.tone}`}>
                <span className="dashboard-card-label">{card.eyebrow}</span>
                <strong>{card.headline}</strong>
                <span className="meta-pill">{card.badge}</span>
                <div className="layer-clarity-block">
                  <span className="layer-clarity-label">Patri sem</span>
                  <div className="dashboard-list">
                    {card.belongs.map((item) => (
                      <span key={item} className="dashboard-list-item">
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="layer-clarity-block">
                  <span className="layer-clarity-label">Nepouzivat jako</span>
                  <div className="dashboard-list">
                    {card.avoid.map((item) => (
                      <span key={item} className="dashboard-list-item">
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="dashboard-list">
            {layerClarityRules.map((rule) => (
              <span key={rule} className="dashboard-list-item">
                {rule}
              </span>
            ))}
          </div>
        </div>
        <div className="workflow-grid workflow-boundary-grid">
          {workflowBoundaryCards.map((card) => (
            <div key={card.title} className={`mini-card workflow-boundary-card tone-${card.tone}`}>
              <span className="dashboard-card-label">{card.title}</span>
              <strong>{card.headline}</strong>
              <span className="meta-pill">{card.badge}</span>
              <span>{card.body}</span>
              <button className="chat-button" type="button" onClick={card.onClick} disabled={card.disabled}>
                {card.disabled ? card.actionStateLabel : card.actionLabel}
              </button>
            </div>
          ))}
        </div>
        <div className="workflow-grid">
          {compactWorkflowCards.map((card) => (
            <div key={card.title} className="mini-card workflow-card">
              <span className="dashboard-card-label">{card.title}</span>
              <strong>{card.badge}</strong>
              <span>{card.body}</span>
              <span className="workflow-card-footer">{card.footer}</span>
            </div>
          ))}
        </div>
        <div className="mini-card workflow-steps-card">
          <strong>Jak to teď prakticky používat</strong>
          <div className="dashboard-list">
            {compactWorkflowSteps.map((step) => (
              <span key={step} className="dashboard-list-item">
                {step}
              </span>
            ))}
          </div>
        </div>
        <div className="workflow-grid workflow-bucket-grid">
          {compactWorkflowBuckets.map((bucket) => (
            <div key={bucket.title} className="mini-card workflow-bucket-card">
              <span className="dashboard-card-label">{bucket.title}</span>
              <strong>{bucket.badge}</strong>
              <div className="dashboard-list">
                {bucket.items.map((item) => (
                  <span key={item} className="dashboard-list-item">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
        <div className="mini-card workflow-steps-card">
          <strong>Bezny den s aplikaci</strong>
          <div className="dashboard-list">
            {compactDayFlow.map((step) => (
              <span key={step} className="dashboard-list-item">
                {step}
              </span>
            ))}
          </div>
        </div>
        <div className="workflow-grid workflow-action-grid">
          <div className="mini-card workflow-action-card">
            <span className="dashboard-card-label">Doporuceny prvni krok</span>
            <strong>Zapsat lokalni stav dne</strong>
            <span>
              Kdyz si nejste jisti, zacnete check-inem. Chat pak odpovida nad realnym dnem, ne nad odhadem.
            </span>
            <button className="chat-button" type="button" onClick={scrollToCheckInPanel}>
              Otevrit check-in niz
            </button>
          </div>
          <div className="mini-card workflow-action-card">
            <span className="dashboard-card-label">Kdyz chcete sdilet vystup</span>
            <strong>Ulozit denni souhrn do Notion</strong>
            <span>
              To je nejcistsi produkcni cesta pro archiv dne nebo sdileny vystup bez nutnosti synchronizovat vsechno.
            </span>
            <button className="chat-button" type="button" onClick={handleSaveDailySummaryToNotion} disabled={isSavingDailySummary}>
              {isSavingDailySummary ? "Ukladam denni souhrn" : "Ulozit denni souhrn"}
            </button>
          </div>
          <div className="mini-card workflow-action-card">
            <span className="dashboard-card-label">Kdyz chcete lepsi odpovedi</span>
            <strong>Obnovit knowledge vrstvu</strong>
            <span>
              Synchronizujte UBZ a evidence obsah, kdyz chcete osvezit znalostni podklad pro dalsi chat odpovedi.
            </span>
            <button className="chat-button" type="button" onClick={handleKnowledgeSyncAll} disabled={isSyncingKnowledgeAll}>
              {isSyncingKnowledgeAll ? "Synchronizuji knowledge vrstvu" : "Synchronizovat knowledge vrstvu"}
            </button>
          </div>
        </div>
        <div className="chips">
          <button className="chat-button" type="button" onClick={handleSyncAllToNotion} disabled={syncingSource !== null}>
            {syncingSource === "all" ? "Synchronizuji vše" : "Synchronizovat vše do Notion"}
          </button>
          <button className="chat-button" type="button" onClick={() => handleNotionSync("daily_check_ins")} disabled={syncingSource !== null}>
            {syncingSource === "daily_check_ins" ? "Synchronizuji check-iny" : "Synchronizovat Daily Check-ins"}
          </button>
          <button className="chat-button" type="button" onClick={() => handleNotionSync("health_signals")} disabled={syncingSource !== null}>
            {syncingSource === "health_signals" ? "Synchronizuji signály" : "Synchronizovat Health Signals"}
          </button>
          <button className="chat-button" type="button" onClick={() => handleNotionSync("follow_ups")} disabled={syncingSource !== null}>
            {syncingSource === "follow_ups" ? "Synchronizuji follow-upy" : "Synchronizovat Follow-ups"}
          </button>
          <button className="chat-button" type="button" onClick={() => handleNotionSync("care_recommendations")} disabled={syncingSource !== null}>
            {syncingSource === "care_recommendations" ? "Synchronizuji vrstvu p\u00e9\u010de" : "Synchronizovat doporu\u010den\u00ed p\u00e9\u010de"}
          </button>
          <button className="chat-button" type="button" onClick={() => handleNotionSync("biomarker_reports")} disabled={syncingSource !== null}>
            {syncingSource === "biomarker_reports" ? "Synchronizuji biomarker reporty" : "Synchronizovat Biomarker Reports"}
          </button>
          <button className="chat-button" type="button" onClick={() => handleNotionSync("biomarker_trends")} disabled={syncingSource !== null}>
            {syncingSource === "biomarker_trends" ? "Synchronizuji biomarker trendy" : "Synchronizovat Biomarker Trends"}
          </button>
          <button className="chat-button" type="button" onClick={() => handleNotionSync("genetic_profile")} disabled={syncingSource !== null}>
            {syncingSource === "genetic_profile" ? "Synchronizuji DNA profil" : "Synchronizovat DNA profil"}
          </button>
          <button className="chat-button" type="button" onClick={() => handleNotionSync("genetic_markers")} disabled={syncingSource !== null}>
            {syncingSource === "genetic_markers" ? "Synchronizuji DNA markery" : "Synchronizovat DNA markery"}
          </button>
        </div>
        {lastSyncResult ? (
          <div className="mini-card">
            <strong>Poslední výsledek synchronizace</strong>
            <span>Zdroj: {lastSyncResult.sourceType}</span>
            <span>Stav: {getSyncDeliveryStateMeta(lastSyncResult.deliveryState).label}</span>
            <span>PokusĹŻ: {lastSyncResult.attemptedCount}</span>
            <span>Režim: {lastSyncResult.mode}</span>
            <span>Počet záznamů: {lastSyncResult.syncedCount}</span>
            <span>Databáze: {lastSyncResult.databaseLabel}</span>
            <span>
              Create / update / skip: {lastSyncResult.createdCount} / {lastSyncResult.updatedCount} /{" "}
              {lastSyncResult.skippedCount}
            </span>
            <span>Soubor: {lastSyncResult.outboxPath}</span>
            {lastSyncResult.errorMessage ? <span>Chyba: {lastSyncResult.errorMessage}</span> : null}
          </div>
        ) : null}
        {lastSyncAllResults.length > 0 ? (
          <div className="mini-card">
            <strong>Poslední výsledek hromadné synchronizace</strong>
            {lastSyncAllResults.map((result) => (
              <span key={`${result.sourceType}-${result.syncedAt}`}>
                {result.sourceType}: {result.syncedCount} záznamů [{result.mode}]
              </span>
            ))}
          </div>
        ) : null}
        <div className="chips">
          <button className="chat-button" type="button" onClick={() => handlePreviewSourceChange("daily_check_ins")}>
            Náhled Check-ins
          </button>
          <button className="chat-button" type="button" onClick={() => handlePreviewSourceChange("health_signals")}>
            Náhled Signals
          </button>
          <button className="chat-button" type="button" onClick={() => handlePreviewSourceChange("follow_ups")}>
            Náhled Follow-ups
          </button>
          <button className="chat-button" type="button" onClick={() => handlePreviewSourceChange("daily_summary")}>
            Náhled Daily Summary
          </button>
          <button className="chat-button" type="button" onClick={() => handlePreviewSourceChange("care_recommendations")}>
            Náhled Care
          </button>
          <button className="chat-button" type="button" onClick={() => handlePreviewSourceChange("biomarker_reports")}>
            Náhled Biomarker Reports
          </button>
          <button className="chat-button" type="button" onClick={() => handlePreviewSourceChange("biomarker_trends")}>
            Náhled Biomarker Trends
          </button>
          <button className="chat-button" type="button" onClick={() => handlePreviewSourceChange("genetic_profile")}>
            Náhled Genetic Profile
          </button>
          <button className="chat-button" type="button" onClick={() => handlePreviewSourceChange("genetic_markers")}>
            Náhled Genetic Markers
          </button>
        </div>
        {mappingPreview ? (
          <div className="mini-card">
            <strong>Náhled mapování: {mappingPreview.databaseLabel}</strong>
            <span>Lokálně: {selectedPreviewExplainer.localMeaning}</span>
            <span>Sync role: {selectedPreviewExplainer.syncMeaning}</span>
            <span>Celkem záznamů: {mappingPreview.totalRecords}</span>
            <span>Vlastnosti: {mappingPreview.propertyNames.join(", ")}</span>
            {mappingPreview.sampleRecords.slice(0, 2).map((record, index) => (
              <span key={`${mappingPreview.sourceType}-${index}`}>
                {JSON.stringify(record)}
              </span>
            ))}
          </div>
        ) : null}
        {notionSyncHistory.length ? (
          <div className="mini-card">
            <strong>Historie synchronizace</strong>
            {notionSyncHistory.slice(0, 3).map((entry) => (
              <div key={`${entry.sourceType}-${entry.syncedAt}`} className="dashboard-block-detail">
                <span>
                  {entry.sourceType} [{entry.mode}]: {entry.syncedCount} záznamů,{" "}
                  {new Date(entry.syncedAt).toLocaleString("cs-CZ")}
                </span>
                <span>
                  Stav: {getSyncDeliveryStateMeta(entry.deliveryState).label} | pokusy {entry.attemptedCount}
                </span>
                <span>
                  Create / update / skip: {entry.createdCount} / {entry.updatedCount} / {entry.skippedCount}
                </span>
                {entry.errorMessage ? <span>Chyba: {entry.errorMessage}</span> : null}
              </div>
            ))}
          </div>
        ) : null}
        {operationalSyncItems.length ? (
          <div className="mini-card">
            <strong>Co se dnes synchronizuje do Notion</strong>
            {operationalSyncItems.map((item) => (
              <div key={item.sourceType} className="stack">
                <span>
                  {item.label}: {item.syncedCount} záznamů
                </span>
                <span>
                  Stav: {getSyncDeliveryStateMeta(item.sourceState?.deliveryState).label}
                  {item.sourceState?.attemptCount ? ` | pokusy ${item.sourceState.attemptCount}` : ""}
                  {item.sourceState?.consecutiveFailures
                    ? ` | selhani v rade ${item.sourceState.consecutiveFailures}`
                    : ""}
                </span>
                {item.sourceState?.lastError ? <span>Posledni chyba: {item.sourceState.lastError}</span> : null}
                <span>{getNotionSourceExplainer(item.sourceType).localMeaning}</span>
                <span>{getNotionSourceExplainer(item.sourceType).syncMeaning}</span>
              </div>
            ))}
          </div>
        ) : null}
        <div className="mini-card">
          <strong>Synchronizace UBZ znalostn\u00ed vrstvy</strong>
          <button className="chat-button" type="button" onClick={handleKnowledgeSyncAll} disabled={isSyncingKnowledgeAll}>
            {isSyncingKnowledgeAll ? "Synchronizuji znalostní vrstvu" : "Synchronizovat celou znalostní vrstvu"}
          </button>
          <button className="chat-button" type="button" onClick={handleUzbSync}>
            {"Synchronizovat UBZ z Notion"}
          </button>
          {ubzSyncResult ? (
            <>
              <span>Synchronizováno: {ubzSyncResult.syncedCount}</span>
              {ubzSyncResult.items.slice(0, 3).map((item) => (
                <span key={item.id}>
                  {item.title}: {item.synced ? item.sourceMode : item.error ?? "bez přístupu"}
                </span>
              ))}
            </>
          ) : (
            <span>UBZ zatím běží ze seed vrstvy. Tady se postupně přepne na živý obsah z Notion.</span>
          )}
        </div>
        <div className="mini-card">
          <strong>Synchronizace evidence vrstvy</strong>
          <button className="chat-button" type="button" onClick={handleEvidenceSync}>
            Synchronizovat evidence z Notion
          </button>
          {evidenceSyncResult ? (
            <>
              <span>Synchronizováno: {evidenceSyncResult.syncedCount}</span>
              {evidenceSyncResult.items.slice(0, 3).map((item) => (
                <span key={item.id}>
                  {item.title}: {item.synced ? item.sourceMode : item.error ?? "bez přístupu"}
                </span>
              ))}
            </>
          ) : (
            <span>Evidence vrstva zatím běží ze seed vrstvy NotebookLM a biomarkerů.</span>
          )}
        </div>
      </details>

      <section className="grid grid-two">
        <article className="panel stack cockpit-main conversation-panel">
          <span className="hero-kicker">Konverzace</span>
          <h2>{state.conversation.title}</h2>
          <p className="operations-subtitle">
            Průběžná konverzace nad dnešním stavem, prioritami a osobním health map kontextem.
          </p>
          <div className="assistant-preview conversation-stream">
            {state.messages.map((message) => (
              <div className={`bubble ${message.role === "assistant" ? "assistant" : "user"}`} key={message.id}>
                {message.content}
              </div>
            ))}
          </div>

          <form className="chat-form conversation-form" onSubmit={handleSubmit}>
            <label className="chat-label" htmlFor="chat-input">
              NapiÅ¡te dalÅ¡Ã­ otÃ¡zku
            </label>
            <div className="quick-prompt-panel">
              <span className="dashboard-card-label">Rychle produkcni testy</span>
              <div className="quick-prompt-grid">
                {CHAT_QUICK_PROMPTS.map((item) => (
                  <button
                    key={item.label}
                    className="quick-prompt-button"
                    type="button"
                    onClick={() => applyQuickPrompt(item.prompt)}
                    disabled={isSubmitting}
                  >
                    <strong>{item.label}</strong>
                    <span>{item.prompt}</span>
                  </button>
                ))}
              </div>
            </div>
            <textarea
              ref={chatInputRef}
              id="chat-input"
              className="chat-input"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Například: Dal jsem si jogurt. Je to pro mě v pohodě?"
              rows={4}
              disabled={isSubmitting}
            />
            <button className="chat-button" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Odesílám" : "Odeslat"}
            </button>
          </form>
        </article>

        <aside className="panel stack cockpit-sidebar response-sidebar" ref={responseSidebarRef}>
          <span className="hero-kicker">{"Fokus"}</span>
          <h2>{"VybranÃ½ kontext"}</h2>
          <p className="operations-subtitle">
            AktivnÃ­ vÃ½kladovÃ¡ vrstva, navÃ¡zanÃ© vztahy a detailnÃ­ interpretace dne.
          </p>
          <div className="meta-line">
            <span className="meta-pill">Mode: {state.answer.selectedScope.mode}</span>
            <span className="meta-pill">{"Uzamčeno: "}{state.answer.selectedScope.locked ? "ano" : "ne"}</span>
          </div>
        <div className="chips">
          {state.answer.selectedScope.groups.map((group) => (
            <span className="chip" key={group}>
              {group}
            </span>
          ))}
        </div>
          <div className="mini-card">
            <strong>Jak tenhle chat pracuje s vrstvami</strong>
            <span>
              Lokální runtime zdroje: {sourceWorkflowSummary.localRuntimeCount} | Notion kontext:{" "}
              {sourceWorkflowSummary.notionContextCount} | Knowledge a evidence:{" "}
              {sourceWorkflowSummary.knowledgeCount}
            </span>
            <span>
              Odpověď bere nejdřív lokální stav dne, potom případně strukturovaný Notion kontext a
              nakonec UBZ nebo evidence vrstvu jako znalostní oporu.
            </span>
          </div>
          {activeFocusPath.length ? (
            <div className="mini-card is-linked">
              <strong>{"AktivnÃ­ cesta fokusu"}</strong>
              <span>{activeFocusPath.join(" -> ")}</span>
            </div>
          ) : null}
          {biomarkerInsightSection ? (
            <>
              <h3 style={{ marginBottom: 0 }}>Detail biomarkeru</h3>
              <div className="mini-card">
                <strong>{biomarkerInsightSection.title}</strong>
                <span>{biomarkerInsightSection.content}</span>
                {briefing?.biomarkerHighlights?.length ? (
                  <span>{"Highlights: "}{briefing.biomarkerHighlights.join(" | ")}</span>
                ) : null}
                {briefing?.flaggedBiomarkerCount ? (
                  <span>{"AktivnÃ­ vÃ½znamnÃ© odchylky: "}{briefing.flaggedBiomarkerCount}</span>
                ) : null}
              </div>
            </>
          ) : null}
          {foodBiomarkerSection ? (
            <>
              <h3 style={{ marginBottom: 0 }}>{"J\u00eddlo -> biomarker"}</h3>
              <div className="mini-card">
                <strong>{foodBiomarkerSection.title}</strong>
                <span>{foodBiomarkerSection.content}</span>
                {meals[0] ? <span>{"Poslední jídlo: "}{meals[0].title}</span> : null}
                {meals[0] ? (
                  <button
                    className="chat-button"
                    type="button"
                    onClick={() => syncFocusFromMealEntry(meals[0])}
                  >
                    OtevÅÃ­t navÃ¡zanÃ½ fokus jÃ­dla
                  </button>
                ) : null}
                {briefing?.biomarkerHighlights?.length ? (
                  <span>Biomarker fokus: {briefing.biomarkerHighlights.join(" | ")}</span>
                ) : null}
              </div>
            </>
          ) : null}
          {careBiomarkerSection ? (
            <>
              <h3 style={{ marginBottom: 0 }}>{"P\u00e9\u010de -> biomarker"}</h3>
              <div className="mini-card">
                <strong>{careBiomarkerSection.title}</strong>
                <span>{careBiomarkerSection.content}</span>
                {selectedBiomarkerPriority ? (
                  <span>
                    AktivnÃ­ marker fokus: {selectedBiomarkerPriority.title}
                  </span>
                ) : null}
                {selectedBiomarkerCareSummary ? <span>{selectedBiomarkerCareSummary}</span> : null}
                {selectedBiomarkerCareRecommendations.length ? (
                  <span>
                    NavÃ¡zanÃ¡ care doporuÄenÃ­:{" "}
                    {selectedBiomarkerCareRecommendations.slice(0, 3).map((item) => item.title).join(" | ")}
                  </span>
                ) : careRecommendations[0] ? (
                  <span>AktivnÃ­ care: {careRecommendations[0].title}</span>
                ) : null}
                {selectedBiomarkerCareRecommendations.length ? (
                  <div className="chips">
                    {selectedBiomarkerCareRecommendations.slice(0, 3).map((item) => (
                      <button
                        className="chat-button"
                        type="button"
                        key={item.id}
                        onClick={() => syncFocusFromCareRecommendation(item)}
                      >
                        {item.title}
                      </button>
                    ))}
                  </div>
                ) : null}
                {briefing?.careHighlights?.length ? (
                  <span>Highlights p\u00e9\u010de: {briefing.careHighlights.join(" | ")}</span>
                ) : null}
                {selectedBiomarkerTrend ? (
                  <span>
                    Biomarker fokus:{" "}
                    {(selectedBiomarkerPriority?.title ?? selectedBiomarkerTrend.markerKey)}
                  </span>
                ) : briefing?.biomarkerHighlights?.length ? (
                  <span>Biomarker fokus: {briefing.biomarkerHighlights.join(" | ")}</span>
                ) : null}
              </div>
            </>
          ) : null}
          {dnaBiomarkerSection ? (
            <>
              <h3 style={{ marginBottom: 0 }}>{"DNA -> biomarker"}</h3>
              <div className="mini-card">
                <strong>{dnaBiomarkerSection.title}</strong>
                <span>{dnaBiomarkerSection.content}</span>
                {biomarkerInsightSection ? (
                  <span>Biomarker fokus: {biomarkerInsightSection.title}</span>
                ) : null}
                {briefing?.careHighlights?.length ? (
                  <span>Kontext p\u00e9\u010de: {briefing.careHighlights.join(" | ")}</span>
                ) : null}
              </div>
            </>
          ) : null}
          {geneticPriorities.length ? (
            <>
              <h3 style={{ marginBottom: 0 }}>Priorita DNA</h3>
              <div className="chips">
                {geneticPriorities.map((marker) => (
                  <button
                    className={`chat-button ${selectedGeneticPriority?.markerKey === marker.markerKey ? "is-active" : ""}`}
                    type="button"
                    key={marker.markerKey}
                    onClick={() => {
                      setSelectedGeneticKey(marker.markerKey);
                      const linkedBiomarkerKey = marker.linkWith.find((value) =>
                        biomarkerTrends.some((trend) => trend.markerKey === value),
                      );
                      if (linkedBiomarkerKey) {
                        setSelectedBiomarkerKey(linkedBiomarkerKey);
                      }
                    }}
                  >
                    {marker.title}
                  </button>
                ))}
              </div>
              {selectedGeneticPriority ? (
                <div className="mini-card">
                  <strong>{selectedGeneticPriority.title}</strong>
                  <span>{selectedGeneticPriority.whyItMatters}</span>
                  <span>{"Kategorie: "}{selectedGeneticPriority.category}</span>
                  <span>{"SÃ­la doporuÄenÃ­: "}{selectedGeneticPriority.recommendationStrength}</span>
                  <span>{"Jistota: "}{selectedGeneticPriority.confidence}</span>
                  {selectedGeneticPriority.genotype ? (
                    <span>Genotyp: {selectedGeneticPriority.genotype}</span>
                  ) : null}
                  <span>{"Interpretace: "}{selectedGeneticPriority.interpretation}</span>
                  {selectedGeneticPriority.watchFor.length ? (
                    <span>Co sledovat: {selectedGeneticPriority.watchFor.join(" | ")}</span>
                  ) : null}
                  {selectedGeneticPriority.linkWith.length ? (
                    <span>{"S ÄÃ­m spojovat: "}{selectedGeneticPriority.linkWith.join(" | ")}</span>
                  ) : null}
                  {selectedGeneticPriority.alertWhen.length ? (
                    <span>{"Kdy zpozornÄt: "}{selectedGeneticPriority.alertWhen.join(" | ")}</span>
                  ) : null}
                  {selectedGeneticLinkedBiomarkerTitles.length ? (
                    <span>{"NavÃ¡zanÃ½ biomarker fokus: "}{selectedGeneticLinkedBiomarkerTitles.join(" | ")}</span>
                  ) : null}
                  {selectedGeneticLinkedBiomarkerTrends.length ? (
                    <span>
                      AktuÃ¡lnÃ­ biomarker realita:{" "}
                      {selectedGeneticLinkedBiomarkerTrends
                        .map((trend) => {
                          const title =
                            biomarkerPriorities.find((item) => item.markerKey === trend.markerKey)?.title ??
                            getBiomarkerDisplayName(trend.markerKey);
                          const value =
                            trend.latestValue !== null && trend.latestValue !== undefined
                              ? `${trend.latestValue} ${trend.latestUnit ?? ""}`.trim()
                              : "bez hodnoty";
                          return `${title}: ${value}`;
                        })
                        .join(" | ")}
                    </span>
                  ) : null}
                  {selectedGeneticCareHighlights.length ? (
                    <span>Vazba p\u00e9\u010de: {selectedGeneticCareHighlights.join(" | ")}</span>
                  ) : null}
                  {selectedGeneticMealContext ? <span>{"Jídlo: "}{selectedGeneticMealContext}</span> : null}
                </div>
              ) : null}
            </>
          ) : null}
          {biomarkerDashboardCards.length ? (
            <>
              <div className="stack" ref={biomarkerPanelRef}>
                <div className="mini-card workflow-primary-action-card">
                  <span className="dashboard-card-label">Hlavni akce panelu</span>
                  <strong>Otevrit prioritu markeru</strong>
                  <span>
                    Vyberte dnesni hlavni marker a hned pod nim sledujte trend, status i navaznou interpretaci.
                  </span>
                  <button
                    className="chat-button"
                    type="button"
                    onClick={() =>
                      setSelectedBiomarkerKey(
                        selectedBiomarkerTrend?.markerKey ??
                          priorityBiomarkerTrends[0]?.markerKey ??
                          biomarkerDashboardCards[0]?.trend.markerKey ??
                          null,
                      )
                    }
                  >
                    {selectedBiomarkerPriority?.title
                      ? `Otevrit ${selectedBiomarkerPriority.title}`
                      : "Otevrit prioritu markeru"}
                  </button>
                </div>
                <h3 style={{ marginBottom: 0 }}>P\u0159ehled biomarker\u016f</h3>
                <div className="biomarker-dashboard-grid">
                  {biomarkerDashboardCards.map((card) => (
                    <button
                      key={card.trend.markerKey}
                      type="button"
                      className={`mini-card biomarker-dashboard-card status-${card.statusMeta.tone} ${card.isActive ? "is-linked" : ""}`}
                      onClick={() => setSelectedBiomarkerKey(card.trend.markerKey)}
                    >
                      <span className="dashboard-card-label">{card.title}</span>
                      <strong>
                        {card.trend.latestValue ?? "?"} {card.trend.latestUnit ?? ""}
                      </strong>
                      <span>
                        {card.trendMeta.arrow} {card.trendMeta.label}
                      </span>
                      <span>Status: {card.statusMeta.label}</span>
                      {card.trend.deltaAbsolute !== null && card.trend.deltaAbsolute !== undefined ? (
                        <span>
                          Delta: {card.trend.deltaAbsolute > 0 ? "+" : ""}
                          {card.trend.deltaAbsolute.toFixed(2)}
                          {card.trend.latestUnit ? ` ${card.trend.latestUnit}` : ""}
                        </span>
                      ) : (
                        <span>{"Delta: prvn? bod"}</span>
                      )}
                      <span>Vzorky: {card.trend.sampleCount}</span>
                    </button>
                  ))}
                </div>
              </div>
            </>
          ) : null}
          {priorityBiomarkerTrends.length ? (
            <>
              <h3 style={{ marginBottom: 0 }}>Priorita markeru</h3>
              <div className="chips">
                {priorityBiomarkerTrends.map((trend) => (
                  <button
                    className={`chat-button ${selectedBiomarkerTrend?.markerKey === trend.markerKey ? "is-active" : ""}`}
                    type="button"
                    key={trend.markerKey}
                    onClick={() => setSelectedBiomarkerKey(trend.markerKey)}
                  >
                    {biomarkerPriorities.find((item) => item.markerKey === trend.markerKey)?.title ??
                      getBiomarkerDisplayName(trend.markerKey)}
                  </button>
                ))}
              </div>
              {selectedBiomarkerTrend ? (
                <div className="mini-card">
                  <strong>
                    {biomarkerPriorities.find((item) => item.markerKey === selectedBiomarkerTrend.markerKey)?.title ??
                      getBiomarkerDisplayName(selectedBiomarkerTrend.markerKey)}
                  </strong>
                  {biomarkerPriorities.find((item) => item.markerKey === selectedBiomarkerTrend.markerKey)?.whyItMatters ? (
                    <span>
                      {
                        biomarkerPriorities.find((item) => item.markerKey === selectedBiomarkerTrend.markerKey)
                          ?.whyItMatters
                      }
                    </span>
                  ) : null}
                  {selectedBiomarkerSnapshotItems.length ? (
                    <div className="biomarker-snapshot-grid">
                      {selectedBiomarkerSnapshotItems.map((item) => (
                        <div
                          key={`${item.label}-${item.value}`}
                          className={`biomarker-snapshot-card tone-${item.tone}`}
                        >
                          <span className="dashboard-card-label">{item.label}</span>
                          <strong>{item.value}</strong>
                          <span>{item.detail}</span>
                        </div>
                      ))}
                    </div>
                  ) : null}
                  {(
                    biomarkerPriorities.find((item) => item.markerKey === selectedBiomarkerTrend.markerKey)?.watchFor
                      ?.length ?? 0
                  ) > 0 ? (
                    <span>
                      Co sledovat:{" "}
                      {biomarkerPriorities
                        .find((item) => item.markerKey === selectedBiomarkerTrend.markerKey)
                        ?.watchFor.join(" | ")}
                    </span>
                  ) : null}
                  {(
                    biomarkerPriorities.find((item) => item.markerKey === selectedBiomarkerTrend.markerKey)?.linkWith
                      ?.length ?? 0
                  ) > 0 ? (
                    <span>
                      S čím spojovat:{" "}
                      {biomarkerPriorities
                        .find((item) => item.markerKey === selectedBiomarkerTrend.markerKey)
                        ?.linkWith.join(" | ")}
                    </span>
                  ) : null}
                  {(
                    biomarkerPriorities.find((item) => item.markerKey === selectedBiomarkerTrend.markerKey)?.alertWhen
                      ?.length ?? 0
                  ) > 0 ? (
                    <span>
                      Kdy zpozornět:{" "}
                      {biomarkerPriorities
                        .find((item) => item.markerKey === selectedBiomarkerTrend.markerKey)
                        ?.alertWhen.join(" | ")}
                    </span>
                  ) : null}
                  <span>
                    Poslední hodnota:{" "}
                    {selectedBiomarkerTrend.latestValue ?? "?"}{" "}
                    {selectedBiomarkerTrend.latestUnit ?? ""}
                  </span>
                  <span>
                    PoslednÃ­ odbÄr:{" "}
                    {selectedBiomarkerTrend.latestObservedAt
                      ? new Date(selectedBiomarkerTrend.latestObservedAt).toLocaleDateString("cs-CZ")
                      : "nezn\u00e1m\u00fd"}
                  </span>
                  <span>{"SmÄr trendu: "}{selectedBiomarkerTrend.trendDirection}</span>
                  <span>{"PoÄet vzorkÅ¯: "}{selectedBiomarkerTrend.sampleCount}</span>
                  {selectedBiomarkerTrend.previousValue !== null &&
                  selectedBiomarkerTrend.previousValue !== undefined ? (
                    <span>
                      P\u0159edchoz\u00ed hodnota: {selectedBiomarkerTrend.previousValue}{" "}
                      {selectedBiomarkerTrend.latestUnit ?? ""}
                    </span>
                  ) : null}
                  {selectedBiomarkerTrend.deltaAbsolute !== null &&
                  selectedBiomarkerTrend.deltaAbsolute !== undefined ? (
                    <span>
                      Delta: {selectedBiomarkerTrend.deltaAbsolute > 0 ? "+" : ""}
                      {selectedBiomarkerTrend.deltaAbsolute}
                      {selectedBiomarkerTrend.latestUnit ? ` ${selectedBiomarkerTrend.latestUnit}` : ""}
                      {selectedBiomarkerTrend.deltaPercent !== null &&
                      selectedBiomarkerTrend.deltaPercent !== undefined
                        ? ` (${selectedBiomarkerTrend.deltaPercent > 0 ? "+" : ""}${selectedBiomarkerTrend.deltaPercent.toFixed(1)} %)`
                        : ""}
                    </span>
                  ) : null}
                  {selectedBiomarkerTrendChart ? (
                    <div className="trend-card">
                      <strong>Trend</strong>
                      <svg
                        viewBox={`0 0 ${selectedBiomarkerTrendChart.width} ${selectedBiomarkerTrendChart.height}`}
                        className="trend-svg"
                        role="img"
                        aria-label="Biomarker trend chart"
                      >
                        {selectedBiomarkerTrendChart.referenceBand ? (
                          <rect
                            x="0"
                            y={selectedBiomarkerTrendChart.referenceBand.yTop}
                            width={selectedBiomarkerTrendChart.width}
                            height={
                              selectedBiomarkerTrendChart.referenceBand.yBottom -
                              selectedBiomarkerTrendChart.referenceBand.yTop
                            }
                            fill="rgba(84, 106, 79, 0.12)"
                          />
                        ) : null}
                        <polyline
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="3"
                          points={selectedBiomarkerTrendChart.polyline}
                        />
                        {selectedBiomarkerTrendChart.points.map((point) => (
                          <circle
                            key={`${point.item.id}-${point.x}`}
                            cx={point.x}
                            cy={point.y}
                            r={selectedBiomarkerObservationDetail?.item.id === point.item.id ? "5.5" : "4"}
                            fill={point.color}
                            stroke={selectedBiomarkerObservationDetail?.item.id === point.item.id ? "#1b1d1a" : "#fffdf8"}
                            strokeWidth={selectedBiomarkerObservationDetail?.item.id === point.item.id ? "2" : "1.5"}
                            style={{ cursor: "pointer" }}
                            onClick={() => setSelectedObservationId(point.item.id)}
                          />
                        ))}
                      </svg>
                      <div className="meta-line">
                        {selectedBiomarkerTrendChart.legend.map((item) => (
                          <span key={`${item.label}-${item.fill}`} className="meta-pill">
                            <span
                              aria-hidden="true"
                              style={{
                                display: "inline-block",
                                width: 10,
                                height: 10,
                                borderRadius: "999px",
                                background: item.fill,
                                marginRight: 6,
                                verticalAlign: "middle",
                              }}
                            />
                            {item.label}
                          </span>
                        ))}
                      </div>
                      <span>
                        Rozsah: {selectedBiomarkerTrendChart.min} - {selectedBiomarkerTrendChart.max}{" "}
                        {selectedBiomarkerTrend.latestUnit ?? ""}
                      </span>
                      {selectedBiomarkerTrendChart.referenceBand ? (
                        <span>
                          Referen?n? p?smo: {selectedBiomarkerTrendChart.referenceBand.low} -{" "}
                          {selectedBiomarkerTrendChart.referenceBand.high}{" "}
                          {selectedBiomarkerTrend.latestUnit ?? ""}
                        </span>
                      ) : null}
                      <div className="trend-points-line">
                        <span>Body:</span>
                        <div className="trend-point-pills">
                          {selectedBiomarkerTrendChart.points.map((point) => {
                            const value =
                              point.item.value !== null && point.item.value !== undefined
                                ? `${point.item.value} ${point.item.unit ?? ""}`.trim()
                                : "bez hodnoty";
                            return (
                              <span
                                key={`point-pill-${point.item.id}`}
                                className="trend-point-pill"
                                onClick={() => setSelectedObservationId(point.item.id)}
                                style={{
                                  borderColor: point.color,
                                  color: point.color,
                                  background: `${point.color}14`,
                                  cursor: "pointer",
                                  boxShadow:
                                    selectedBiomarkerObservationDetail?.item.id === point.item.id
                                      ? "0 0 0 2px rgba(27, 29, 26, 0.08)"
                                      : "none",
                                }}
                              >
                                <span
                                  aria-hidden="true"
                                  className="trend-point-pill-dot"
                                  style={{ background: point.color }}
                                />
                                {new Date(point.item.observedAt).toLocaleDateString("cs-CZ")}: {value}
                              </span>
                            );
                          })}
                        </div>
                      </div>
                      {selectedBiomarkerObservationDetail ? (
                        <div className="mini-card trend-detail-card">
                          <strong>
                            Detail bodu:{" "}
                            {new Date(selectedBiomarkerObservationDetail.item.observedAt).toLocaleDateString("cs-CZ")}
                          </strong>
                          <span>
                            Hodnota:{" "}
                            {selectedBiomarkerObservationDetail.item.value !== null &&
                            selectedBiomarkerObservationDetail.item.value !== undefined
                              ? `${selectedBiomarkerObservationDetail.item.value} ${selectedBiomarkerObservationDetail.item.unit ?? ""}`.trim()
                              : "bez hodnoty"}
                          </span>
                          <span>Status: {selectedBiomarkerObservationDetail.item.status}</span>
                          <span>Zdroj ??dku: {selectedBiomarkerObservationDetail.item.sourceLine}</span>
                          {selectedBiomarkerObservationDetail.item.referenceLow !== null &&
                          selectedBiomarkerObservationDetail.item.referenceLow !== undefined &&
                          selectedBiomarkerObservationDetail.item.referenceHigh !== null &&
                          selectedBiomarkerObservationDetail.item.referenceHigh !== undefined ? (
                            <span>
                              Referen?n? p?smo: {selectedBiomarkerObservationDetail.item.referenceLow} -{" "}
                              {selectedBiomarkerObservationDetail.item.referenceHigh}{" "}
                              {selectedBiomarkerObservationDetail.item.unit ?? ""}
                            </span>
                          ) : null}
                          <span>
                            Kontext m??en?: {selectedBiomarkerObservationDetail.item.measurementContext}
                          </span>
                          <span>Confidence: {selectedBiomarkerObservationDetail.item.confidence}</span>
                          {selectedBiomarkerObservationMeaning ? (
                            <span>Co to znamen? dnes: {selectedBiomarkerObservationMeaning}</span>
                          ) : null}
                          {selectedBiomarkerObservationAction ? (
                            <span>Co ud?lat dnes: {selectedBiomarkerObservationAction}</span>
                          ) : null}
                          {selectedBiomarkerObservationComparison ? (
                            <>
                              <span>{selectedBiomarkerObservationComparison.summary}</span>
                              <span>
                                P?edchoz? bod:{" "}
                                {new Date(
                                  selectedBiomarkerObservationComparison.previousDate,
                                ).toLocaleDateString("cs-CZ")}
                                {" - "}
                                {`${selectedBiomarkerObservationComparison.previousValue} ${selectedBiomarkerObservationComparison.unit}`.trim()}
                              </span>
                            </>
                          ) : (
                            <span>{"Pro srovnÃ¡nÃ­ zatÃ­m chybÃ­ pÅedchozÃ­ validnÃ­ bod."}</span>
                          )}
                        </div>
                      ) : null}
                    </div>
                  ) : selectedBiomarkerObservations.length === 1 ? (
                    <span>
                       Trend bude plnÄ ÄitelnÃ½ po vÃ­ce neÅ¾ jednom mÄÅenÃ­. ZatÃ­m je k dispozici 1 observation.
                    </span>
                  ) : null}
                </div>
              ) : null}
            </>
          ) : null}
          <details className="mini-card collapsible-card">
            <summary className="collapsible-summary">
              <span>Struktura odpovÄdi</span>
              <span className="meta-pill">{state.answer.sections.length} sekci</span>
            </summary>
            <div className="stack">
              {state.answer.sections.map((section) => (
                <div key={section.kind} className="mini-card">
                  <strong>{section.title}</strong>
                  <span>{section.content}</span>
                </div>
              ))}
            </div>
          </details>
          <details className="mini-card collapsible-card">
            <summary className="collapsible-summary">
              <span>Sources</span>
              <span className="meta-pill">{groupedSources.length} zdrojÅ¯</span>
            </summary>
            <div className="mini-card workflow-summary-card">
              <strong>Jak byla odpověď složená</strong>
              <span>Lokální runtime: {sourceWorkflowSummary.localRuntimeCount}</span>
              <span>Notion kontext: {sourceWorkflowSummary.notionContextCount}</span>
              <span>Knowledge a evidence: {sourceWorkflowSummary.knowledgeCount}</span>
              <span>Modelová syntéza: {sourceWorkflowSummary.modelCount}</span>
            </div>
            <div className="stack">
              {groupedSources.map((source) => (
                <div key={`${source.label}-${source.type}`} className="mini-card">
                  <strong>{source.label}</strong>
                  <span>{getSourceExplainer(source.type).layer}</span>
                  <span>Typ: {formatSourceTypeLabel(source.type)}</span>
                  <span>Tier: {source.authorityTier}</span>
                  <span>{getSourceExplainer(source.type).meaning}</span>
                  <span>{getSourceExplainer(source.type).storage}</span>
                  {source.reference ? <span>{source.reference}</span> : null}
                </div>
              ))}
            </div>
          </details>
          <details className="mini-card collapsible-card">
            <summary className="collapsible-summary">
              <span>Z\u00e1sahy UBZ znalostn\u00ed vrstvy</span>
              <span className="meta-pill">{ubzHits.length}</span>
            </summary>
            <div className="stack">
              {ubzHits.length ? (
                ubzHits.map((hit) => (
                  <div key={hit.id} className="mini-card">
                    <strong>{hit.title}</strong>
                    <span>Score: {hit.score} / {hit.sourceMode}</span>
                    <span>Tier: {hit.authorityTier}</span>
                    <span>{hit.summary}</span>
                    {hit.excerpt ? <span>{hit.excerpt}</span> : null}
                    <span>{hit.notionPath}</span>
                  </div>
                ))
              ) : (
                <div className="mini-card">
                  <strong>ZatÃ­m bez UBZ hitu</strong>
                  <span>Po dotazu na dech, rytmus, regeneraci nebo UBZ se tu ukÃ¡Å¾ou souvisejÃ­cÃ­ uzly.</span>
                </div>
              )}
            </div>
          </details>
          <details className="mini-card collapsible-card">
            <summary className="collapsible-summary">
              <span>Z\u00e1sahy evidence vrstvy</span>
              <span className="meta-pill">{evidenceHits.length}</span>
            </summary>
            <div className="stack">
              {evidenceHits.length ? (
                evidenceHits.map((hit) => (
                  <div key={hit.id} className="mini-card">
                    <strong>{hit.title}</strong>
                    <span>Score: {hit.score} / {hit.sourceMode}</span>
                    <span>Tier: {hit.authorityTier}</span>
                    <span>{hit.summary}</span>
                    {hit.excerpt ? <span>{hit.excerpt}</span> : null}
                    <span>{hit.notionPath}</span>
                  </div>
                ))
              ) : (
                <div className="mini-card">
                  <strong>ZatÃ­m bez evidence hitu</strong>
                  <span>Po dotazu na biomarkery, laboratoÅ, vÃ½zkum nebo NotebookLM se tu ukÃ¡Å¾ou souvisejÃ­cÃ­ zdroje.</span>
                </div>
              )}
            </div>
          </details>
        </aside>
      </section>

      <section className="grid grid-two operations-zone">
        <article className="panel stack operations-panel operations-panel-checkin" ref={checkInPanelRef}>
          <span className="hero-kicker">Operativa</span>
          <h2>DennÃ­ check-in</h2>
          <p className="operations-subtitle">RannÃ­ nebo veÄernÃ­ kotva dne pro energii, stres a spÃ¡nek.</p>
          <div className="mini-card workflow-test-card">
            <span className="dashboard-card-label">Praktický test check-inu</span>
            <strong>1. Předvyplnit check-in 2. Uložit 3. Zeptat se chatu</strong>
            <span>
              Rychlé ověření, že denní operativa opravdu pohání další interpretaci a doporučený další krok.
            </span>
            <div className="chips">
              {CHECK_IN_TEST_SCENARIOS.map((scenario) => (
                <button
                  key={scenario.label}
                  className="chat-button"
                  type="button"
                  onClick={() => applyCheckInTestScenario(scenario)}
                  disabled={isSavingCheckIn}
                >
                  {scenario.label}
                </button>
              ))}
              <button
                className="chat-button chat-button-secondary"
                type="button"
                onClick={askAboutLatestCheckIn}
                disabled={isSubmitting}
              >
                Zeptat se na poslední check-in
              </button>
            </div>
          </div>
          <form className="chat-form" onSubmit={handleCheckInSubmit}>
            <select className="chat-input" value={checkInType} onChange={(e) => setCheckInType(e.target.value as "morning" | "evening")} disabled={isSavingCheckIn}>
              <option value="morning">RannÃ­ check-in</option>
              <option value="evening">VeÄernÃ­ check-in</option>
            </select>
            <label className="chat-label">Energie: {energy}/10</label>
            <input className="chat-input" type="range" min="1" max="10" value={energy} onChange={(e) => setEnergy(Number(e.target.value))} disabled={isSavingCheckIn} />
            <label className="chat-label">Stres: {stress}/10</label>
            <input className="chat-input" type="range" min="1" max="10" value={stress} onChange={(e) => setStress(Number(e.target.value))} disabled={isSavingCheckIn} />
            <label className="chat-label">Kvalita spÃ¡nku: {sleepQuality}/10</label>
            <input className="chat-input" type="range" min="1" max="10" value={sleepQuality} onChange={(e) => setSleepQuality(Number(e.target.value))} disabled={isSavingCheckIn} />
            <textarea className="chat-input" value={checkInNotes} onChange={(e) => setCheckInNotes(e.target.value)} placeholder="PoznÃ¡mka k check-inu" rows={3} disabled={isSavingCheckIn} />
            <button className="chat-button" type="submit" disabled={isSavingCheckIn}>
              {isSavingCheckIn ? "Ukládám check-in" : "Uložit check-in"}
            </button>
          </form>
        </article>

        <aside className="panel stack operations-panel operations-panel-reminder">
          <span className="hero-kicker">Reminder</span>
          <h2>Dnes k vyÅÃ­zenÃ­</h2>
          <p className="operations-subtitle">AktivnÃ­ follow-upy, kterÃ© drÅ¾Ã­ rytmus dne a navazujÃ­ na zapsanÃ© udÃ¡losti.</p>
          <div className="stack">
            {todayFollowUps.length ? (
              todayFollowUps.slice(0, 5).map((followUp) => (
                <div className="mini-card" key={followUp.id}>
                  <strong>{followUp.title}</strong>
                  <span>{followUp.delayLabel}</span>
                  <span>Due: {new Date(followUp.dueAt).toLocaleString("cs-CZ")}</span>
                  <span>{followUp.message}</span>
                  <button className="chat-button" type="button" onClick={() => handleCompleteFollowUp(followUp.id)} disabled={completingId === followUp.id}>
                    {completingId === followUp.id ? "Dokončuji" : "Označit jako hotové"}
                  </button>
                </div>
              ))
            ) : (
              <div className="mini-card">
                <strong>ZatÃ­m nic akutnÃ­ho</strong>
                <span>Reminder engine sem bude posÃ­lat follow-upy z jÃ­dla, signÃ¡lÅ¯ i check-inÅ¯.</span>
              </div>
            )}
          </div>
        </aside>
      </section>

      <section className="grid grid-two operations-zone">
        <article className="panel stack operations-panel operations-panel-meal">
          <span className="hero-kicker">Log jÃ­dla</span>
          <h2>RychlÃ½ zÃ¡pis jÃ­dla</h2>
          <p className="operations-subtitle">ZachyÅ¥te jÃ­dlo hned a propojte ho s biomarkerovÃ½m a DNA fokusem.</p>
          <div className="mini-card workflow-test-card">
            <span className="dashboard-card-label">Praktický test jídla</span>
            <strong>1. Předvyplnit jídlo 2. Uložit 3. Zeptat se chatu</strong>
            <span>
              Tohle je nejrychlejší produkční flow pro ověření, že vrstva jídla, biomarkerů a knowledge odpovědí drží pohromadě.
            </span>
            <div className="chips">
              {MEAL_TEST_SCENARIOS.map((scenario) => (
                <button
                  key={scenario.label}
                  className="chat-button"
                  type="button"
                  onClick={() => applyMealTestScenario(scenario)}
                  disabled={isSavingMeal}
                >
                  {scenario.label}
                </button>
              ))}
              <button
                className="chat-button chat-button-secondary"
                type="button"
                onClick={askAboutLatestMeal}
                disabled={isSubmitting}
              >
                Zeptat se na poslední jídlo
              </button>
            </div>
          </div>
          <form className="chat-form" onSubmit={handleMealSubmit}>
            <input className="chat-input" value={mealTitle} onChange={(e) => setMealTitle(e.target.value)} placeholder="NapÅÃ­klad: Jogurt s ovocem" disabled={isSavingMeal} />
            <select className="chat-input" value={mealType} onChange={(e) => setMealType(e.target.value)} disabled={isSavingMeal}>
              <option value="breakfast">SnÃ­danÄ</option>
              <option value="lunch">ObÄd</option>
              <option value="dinner">VeÄeÅe</option>
              <option value="snack">SvaÄina</option>
            </select>
            <input className="chat-input" value={mealTags} onChange={(e) => setMealTags(e.target.value)} placeholder="Tagy: lactose, protein, sugar" disabled={isSavingMeal} />
            <textarea className="chat-input" value={mealNotes} onChange={(e) => setMealNotes(e.target.value)} placeholder="PoznÃ¡mka k jÃ­dlu" rows={3} disabled={isSavingMeal} />
            <button className="chat-button" type="submit" disabled={isSavingMeal}>
              {isSavingMeal ? "Ukládám jídlo" : "Uložit jídlo"}
            </button>
          </form>
        </article>

        <aside className="panel stack operations-panel operations-panel-overview">
          <span className="hero-kicker">PÅehled</span>
          <h2>PoslednÃ­ jÃ­dla</h2>
          <p className="operations-subtitle">RychlÃ½ pÅehled poslednÃ­ch zapsanÃ½ch jÃ­del a jejich vazeb.</p>
          <div className="stack">
            {meals.length ? (
              meals.slice(0, 4).map((meal) => (
                <div className={`mini-card ${selectedMealId === meal.id ? "is-linked" : ""}`} key={meal.id}>
                  <strong>{meal.title}</strong>
                  <span>{meal.mealType}</span>
                  {meal.tags.length ? <span>Tagy: {meal.tags.join(" | ")}</span> : null}
                  {meal.notes ? <span>{meal.notes}</span> : null}
                  <button
                    className={`chat-button ${selectedMealId === meal.id ? "is-active" : ""}`}
                    type="button"
                    onClick={() => syncFocusFromMealEntry(meal)}
                  >
                    OtevÅÃ­t navÃ¡zanÃ½ fokus jÃ­dla
                  </button>
                  <button
                    className="chat-button chat-button-secondary"
                    type="button"
                    onClick={() => handleDeleteMeal(meal.id)}
                    disabled={deletingMealId === meal.id}
                  >
                    {deletingMealId === meal.id ? "Maz?m j?dlo" : "Smazat j?dlo"}
                  </button>
                </div>
              ))
            ) : (
              <div className="mini-card">
                <strong>ZatÃ­m bez jÃ­del</strong>
                <span>Po zapsÃ¡nÃ­ jÃ­dla se tady objevÃ­ i rychlÃ© propojenÃ­ na biomarker a DNA fokus.</span>
              </div>
            )}
          </div>
        </aside>
      </section>

      <section className="grid grid-two operations-zone">
        <article className="panel stack operations-panel operations-panel-signal">
          <span className="hero-kicker">Log signÃ¡lÅ¯</span>
          <h2>RychlÃ½ zÃ¡pis signÃ¡lÅ¯</h2>
          <p className="operations-subtitle">PozorovanÃ© signÃ¡ly tÄla, kterÃ© se majÃ­ propsat do kontextu dne.</p>
          <div className="mini-card workflow-test-card">
            <span className="dashboard-card-label">Praktický test signálu</span>
            <strong>1. Předvyplnit signál 2. Uložit 3. Zeptat se chatu</strong>
            <span>
              Hodí se pro rychlé ověření, že signál naváže na dnešní stav, biomarkerový fokus i další praktický krok.
            </span>
            <div className="chips">
              {SIGNAL_TEST_SCENARIOS.map((scenario) => (
                <button
                  key={scenario.label}
                  className="chat-button"
                  type="button"
                  onClick={() => applySignalTestScenario(scenario)}
                  disabled={isSavingSignal}
                >
                  {scenario.label}
                </button>
              ))}
              <button
                className="chat-button chat-button-secondary"
                type="button"
                onClick={askAboutLatestSignal}
                disabled={isSubmitting}
              >
                Zeptat se na poslední signál
              </button>
            </div>
          </div>
          <form className="chat-form" onSubmit={handleSignalSubmit}>
            <input className="chat-input" value={signalTitle} onChange={(e) => setSignalTitle(e.target.value)} placeholder="NapÅÃ­klad: NadÃ½mÃ¡nÃ­ po snÃ­dani" disabled={isSavingSignal} />
            <select className="chat-input" value={signalCategory} onChange={(e) => setSignalCategory(e.target.value)} disabled={isSavingSignal}>
              <option value="digestion">TrÃ¡venÃ­</option>
              <option value="energy">Energie</option>
              <option value="sleep">SpÃ¡nek</option>
              <option value="stress">Stres</option>
            </select>
            <select className="chat-input" value={signalSeverity} onChange={(e) => setSignalSeverity(e.target.value as "low" | "medium" | "high")} disabled={isSavingSignal}>
              <option value="low">NÃ­zkÃ¡</option>
              <option value="medium">StÅednÃ­</option>
              <option value="high">VysokÃ¡</option>
            </select>
            <textarea className="chat-input" value={signalNotes} onChange={(e) => setSignalNotes(e.target.value)} placeholder="PoznÃ¡mka k signÃ¡lu" rows={3} disabled={isSavingSignal} />
            <button className="chat-button" type="submit" disabled={isSavingSignal}>
              {isSavingSignal ? "Ukládám signál" : "Uložit signál"}
            </button>
          </form>
        </article>

        <aside className="panel stack operations-panel operations-panel-overview">
          <span className="hero-kicker">Přehled</span>
          <h2>Poslední signály</h2>
          <p className="operations-subtitle">Nejčerstvější signály a rychlý vstup do navázaného fokusu.</p>
          <div className="stack">
            {signals.length ? (
              signals.slice(0, 4).map((signal) => (
                <div className={`mini-card ${selectedBiomarkerPriority && (
                  (signal.category === "digestion" && ["glucose_fasting", "triglycerides", "vitamin_b12"].includes(selectedBiomarkerPriority.markerKey)) ||
                  (signal.category === "energy" && ["vitamin_b12", "ferritin", "glucose_fasting", "tsh"].includes(selectedBiomarkerPriority.markerKey)) ||
                  (signal.category === "sleep" && ["crp", "glucose_fasting", "tsh"].includes(selectedBiomarkerPriority.markerKey)) ||
                  (signal.category === "stress" && ["crp", "glucose_fasting", "tsh"].includes(selectedBiomarkerPriority.markerKey))
                ) ? "is-linked" : ""}`} key={signal.id}>
                  <strong>{signal.title}</strong>
                  <span>{signal.category}</span>
                  <span>Závažnost: {signal.severity}</span>
                  {signal.notes ? <span>{signal.notes}</span> : null}
                  <button
                    className={`chat-button ${selectedBiomarkerPriority && (
                      (signal.category === "digestion" && ["glucose_fasting", "triglycerides", "vitamin_b12"].includes(selectedBiomarkerPriority.markerKey)) ||
                      (signal.category === "energy" && ["vitamin_b12", "ferritin", "glucose_fasting", "tsh"].includes(selectedBiomarkerPriority.markerKey)) ||
                      (signal.category === "sleep" && ["crp", "glucose_fasting", "tsh"].includes(selectedBiomarkerPriority.markerKey)) ||
                      (signal.category === "stress" && ["crp", "glucose_fasting", "tsh"].includes(selectedBiomarkerPriority.markerKey))
                    ) ? "is-active" : ""}`}
                    type="button"
                    onClick={() => syncFocusFromHealthSignal(signal)}
                  >
                    OtevÅÃ­t navÃ¡zanÃ½ fokus signÃ¡lu
                  </button>
                  <button
                    className="chat-button chat-button-secondary"
                    type="button"
                    onClick={() => handleDeleteSignal(signal.id)}
                    disabled={deletingSignalId === signal.id}
                  >
                    {deletingSignalId === signal.id ? "Maz?m sign?l" : "Smazat sign?l"}
                  </button>
                </div>
              ))
            ) : (
              <div className="mini-card">
                <strong>Zatím bez signálů</strong>
                <span>Po zapsání signálu se tady objeví poslední pozorované zdravotní signály.</span>
              </div>
            )}
          </div>
        </aside>
      </section>

      <section className="panel stack operations-panel operations-panel-history">
        <span className="hero-kicker">Follow-up log</span>
        <h2>Historie follow-upu</h2>
        <p className="operations-subtitle">Krátký provozní log posledních reminderů a navazných kroků.</p>
        <div className="stack">
          {followUps.slice(0, 6).map((followUp) => (
            <div className="mini-card" key={followUp.id}>
              <strong>{followUp.title}</strong>
              <span>{followUp.triggerType}</span>
              <span>{followUp.delayLabel}</span>
              <span>Status: {followUp.status}</span>
              <span>{followUp.message}</span>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
