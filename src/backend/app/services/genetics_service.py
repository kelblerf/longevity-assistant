from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.models import (
    GeneticImportDraft,
    GeneticImportDraftInput,
    GeneticMarker,
    GeneticProfile,
    UpsertGeneticProfileInput,
)
from app.services.storage_service import read_json, write_json

_FILE_NAME = "genetic-profile.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_genetic_profile() -> GeneticProfile | None:
    payload = read_json(_FILE_NAME, default=None)
    if not payload:
        return None
    return GeneticProfile.model_validate(payload)


def upsert_genetic_profile(payload: UpsertGeneticProfileInput) -> GeneticProfile:
    existing = get_genetic_profile()
    profile = GeneticProfile(
        id=existing.id if existing else f"dna-{uuid4().hex[:12]}",
        sourceType=payload.source_type,
        sourceLabel=payload.source_label,
        importedAt=_now_iso(),
        summary=payload.summary,
        markers=payload.markers,
    )
    write_json(_FILE_NAME, profile.model_dump(by_alias=True))
    return profile


def _append_marker(
    markers: list[GeneticMarker],
    *,
    key: str,
    label: str,
    category: str,
    interpretation: str,
    source_ref: str,
    related_domains: list[str],
    recommendation_strength: str = "medium",
    confidence: str = "draft",
) -> None:
    if any(marker.key == key for marker in markers):
        return

    markers.append(
        GeneticMarker(
            id=f"marker-{uuid4().hex[:10]}",
            key=key,
            label=label,
            category=category,
            genotype=None,
            interpretation=interpretation,
            recommendationStrength=recommendation_strength,
            confidence=confidence,
            sourceRef=source_ref,
            relatedDomains=related_domains,
        )
    )


def build_genetic_import_draft(payload: GeneticImportDraftInput) -> GeneticImportDraft:
    normalized = payload.raw_text.lower()
    markers: list[GeneticMarker] = []
    unresolved_notes: list[str] = []

    if "lakt" in normalized or "lact" in normalized:
        lactose_positive = any(
            phrase in normalized
            for phrase in [
                "lactase persistence",
                "persistence laktazy",
                "nenasvedcuje geneticke predispozici k intoleranci laktozy",
                "neni geneticka predispozice k intoleranci laktozy",
                "geneticke predispozici k intoleranci laktozy nenasvedcuje",
            ]
        )

        interpretation = (
            "Text naznacuje zachovanou toleranci laktozy. DNA zde nema byt ctena jako "
            "zakaz mlecnych produktu, ale jako neutralni vrstva, kterou je potreba "
            "porovnavat s realnou travici reakci."
            if lactose_positive
            else "Text naznacuje horsi toleranci laktozy. Marker se ma pouzit jako "
            "doporucujici signal pro sledovani traveni a reakce po mlecnych produktech."
        )

        _append_marker(
            markers,
            key="lactose_tolerance",
            label="Tolerance laktozy",
            category="nutrition",
            interpretation=interpretation,
            source_ref=payload.source_label,
            related_domains=["nutrition", "digestion", "dna_conflict"],
        )

    if "kofein" in normalized or "caffeine" in normalized:
        _append_marker(
            markers,
            key="caffeine_response",
            label="Citlivost na kofein",
            category="stimulation",
            interpretation=(
                "Text naznacuje odchylku v reakci na kofein. Doporucuje se cist ji v "
                "souvislosti s energii, spankem a denni dobou."
            ),
            source_ref=payload.source_label,
            related_domains=["energy", "sleep", "stimulation"],
        )

    if "folat" in normalized or "mthfr" in normalized:
        _append_marker(
            markers,
            key="methylation_folate",
            label="Folat / methylace",
            category="methylation",
            interpretation=(
                "Text naznacuje relevantni signal v oblasti folatu nebo methylace. "
                "Tento marker ma vstupovat hlavne do evidence vrstvy a nevyvozovat "
                "zjednodusene zavery bez dalsiho kontextu."
            ),
            source_ref=payload.source_label,
            related_domains=["biomarkers", "energy", "methylation"],
        )

    if "fut2" in normalized or "vitamin b12" in normalized or "b12" in normalized:
        _append_marker(
            markers,
            key="b12_absorption",
            label="Vitamin B12 / absorpce",
            category="vitamins",
            interpretation=(
                "Text naznacuje signal pro vyssi peclivost kolem vitaminu B12. "
                "Je vhodne cist jej spolu s homocysteinem, energii a neurologickym kontextem."
            ),
            source_ref=payload.source_label,
            related_domains=["vitamins", "energy", "biomarkers", "neurology"],
        )

    if (
        "il6" in normalized
        or "il-6" in normalized
        or "il1" in normalized
        or "il-1" in normalized
        or "fads1" in normalized
        or "zanet" in normalized
    ):
        _append_marker(
            markers,
            key="inflammation_regulation",
            label="Zanetliva regulace",
            category="inflammation",
            interpretation=(
                "Text naznacuje vyssi citlivost v oblasti zanetu a potrebu sledovat "
                "protizanetlivy rezim, glykemii, lipidovy profil a rovnovahu omega-3 a omega-6."
            ),
            source_ref=payload.source_label,
            related_domains=["inflammation", "recovery", "biomarkers", "cardiometabolic"],
        )

    if (
        "sod2" in normalized
        or "mnsod" in normalized
        or "cat -262" in normalized
        or "gpx1" in normalized
        or "oxidacni stres" in normalized
    ):
        _append_marker(
            markers,
            key="oxidative_stress_response",
            label="Oxidacni stres",
            category="oxidative_stress",
            interpretation=(
                "Text naznacuje vyssi narok na antioxidadni ochranu, polyfenoly, zeleninu "
                "a omezeni toxicke zateze z prostredi i stravy."
            ),
            source_ref=payload.source_label,
            related_domains=["oxidative_stress", "recovery", "nutrition", "detox"],
        )

    if "pparg" in normalized or "tcf7l2" in normalized or "fto" in normalized or "inzulin" in normalized:
        _append_marker(
            markers,
            key="insulin_sensitivity",
            label="Citlivost na inzulin",
            category="metabolism",
            interpretation=(
                "Text naznacuje signal pro peclivost kolem inzulinove citlivosti, kvality tuku, "
                "hmotnosti, sytosti a pravidelneho pohybu."
            ),
            source_ref=payload.source_label,
            related_domains=["metabolism", "energy", "nutrition", "weight_management"],
        )

    if "lpl" in normalized or "cetp" in normalized or "apoe" in normalized or "pon1" in normalized:
        _append_marker(
            markers,
            key="lipid_regulation",
            label="Lipidova regulace",
            category="cardiometabolic",
            interpretation=(
                "Text naznacuje, ze lipidova oblast se ma cist hlavne pres triglyceridy, HDL, "
                "LDL, kvalitu tuku a dlouhodoby kardiometabolicky trend."
            ),
            source_ref=payload.source_label,
            related_domains=["cardiometabolic", "lipids", "nutrition", "biomarkers"],
        )

    if "ace " in normalized or "agt " in normalized or "citlivost na sul" in normalized:
        _append_marker(
            markers,
            key="salt_pressure_response",
            label="Citlivost na sul a tlak",
            category="blood_pressure",
            interpretation=(
                "Text naznacuje signal pro peclivost kolem prijmu soli, krevniho tlaku "
                "a omezeni ultra-prumyslove zpracovanych potravin."
            ),
            source_ref=payload.source_label,
            related_domains=["blood_pressure", "nutrition", "cardiometabolic"],
        )

    if "bco1" in normalized or "vitamin a" in normalized or "beta-karoten" in normalized:
        _append_marker(
            markers,
            key="vitamin_a_conversion",
            label="Vitamin A / konverze",
            category="vitamins",
            interpretation=(
                "Text naznacuje signal pro peclivost kolem konverze beta-karotenu na aktivni vitamin A "
                "a pro vhodny vyber potravinovych zdroju."
            ),
            source_ref=payload.source_label,
            related_domains=["vitamins", "nutrition", "vision", "immunity"],
        )

    if not markers:
        unresolved_notes.append(
            "V textu se nepodarilo automaticky rozpoznat zadny pripraveny DNA marker. "
            "Bude potreba rucni doplneni nebo rozsireni parseru."
        )

    summary = (
        "Prvni draft DNA profilu pripraveny k rucnimu potvrzeni. Markery jsou zatim "
        "vedene jako doporucujici signaly, ne konecne verdikty."
    )
    return GeneticImportDraft(
        sourceType=payload.source_type,
        sourceLabel=payload.source_label,
        summary=summary,
        markers=markers,
        unresolvedNotes=unresolved_notes,
    )
