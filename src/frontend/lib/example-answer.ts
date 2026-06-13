import type { AssistantAnswer } from "@shared/contracts/types";
import { normalizeTextTree } from "@/lib/text-normalization";

const rawExampleAnswer: AssistantAnswer = {
  summary:
    "Dnes dává největší smysl zklidnit přetížení, podržet dechovou regulaci a nechat regeneraci vést rytmus dne.",
  selectedScope: {
    mode: "core_plus_domain",
    groups: [
      "profile",
      "app_health_data",
      "app_genetics_data",
      "ubz_framework",
      "notebooklm_research",
    ],
    locked: false,
    reason:
      "Dotaz je silně o rytmu, stresu a dechové regulaci, ale stále vyžaduje i evidence vrstvu.",
  },
  sections: [
    {
      kind: "profile_context",
      title: "Co o vás systém ví",
      content:
        "Poslední dny ukazují vyšší napětí, kolísání energie a citlivost na přetížení pozdě odpoledne.",
    },
    {
      kind: "ubz_basis",
      title: "Co říká UBZ rámec",
      content:
        "Dech a rytmus dnes potřebují být stabilizační osou, ne dalším výkonovým úkolem.",
    },
    {
      kind: "dna_signal",
      title: "Co naznačuje DNA",
      content:
        "Genetické signály podporují opatrnost v přetížení organismu stresem a naznačují, že tlak nevyřešíte dalším tlakem.",
    },
    {
      kind: "evidence_basis",
      title: "Co podporuje evidence vrstva",
      content:
        "Spánkový deficit a vyšší stresový ton spolu běžně zhoršují energii, regulaci chuti a obnovu regenerace.",
    },
  ],
  nextSteps: [
    "Udělejte krátký dechový reset před prvním větším úkolem.",
    "Držte dnes jednodušší rytmus jídla bez zbytečných stresorů.",
    "Večer zapsat, jak reagovala energie po dechovém bloku.",
  ],
  sources: [
    {
      label: "Core profile",
      type: "profile",
      reference: null,
      authorityTier: "core_truth",
    },
    {
      label: "UBZ / Pusty a dech v souvislostech",
      type: "ubz_framework",
      reference: "Digitalni druhy mozek / Temata / UBZ Energo evoluce 2025",
      authorityTier: "ubz_primary",
    },
    {
      label: "NotebookLM - Medical Fundation",
      type: "notebooklm_research",
      reference: "Notion",
      authorityTier: "evidence_primary",
    },
  ],
};

export const exampleAnswer: AssistantAnswer = normalizeTextTree(rawExampleAnswer);
