from __future__ import annotations

from app.models import GeneticPriorityConfig, GeneticPriorityMarker
from app.services.genetics_service import get_genetic_profile
from app.services.storage_service import read_json, write_json

_FILE_NAME = "genetic-priority-markers.json"

_ACTION_HINTS: dict[str, dict[str, list[str] | str]] = {
    "lactose_tolerance": {
        "why": "Pomaha drzet rozumny pohled na mlecne produkty a cist je spolu s realnou travici reakci.",
        "watchFor": [
            "reakce po mlecnych produktech",
            "rozdil mezi fermentovanou a nefermentovanou formou",
            "opakovanou travici odezvu",
        ],
        "linkWith": ["traveni", "jidlo", "health signals"],
        "alertWhen": [
            "symptomy se opakuji i pri mensich davkach",
            "DNA a realna tolerance jdou dlouhodobe proti sobe",
        ],
    },
    "caffeine_response": {
        "why": "Je prakticky dulezity pro energii, stimulaci a vztah ke spanku.",
        "watchFor": ["odpoledni a vecerni kofein", "vztah k energii a neklidu", "kvalitu spanku"],
        "linkWith": ["energie", "spanek", "stres"],
        "alertWhen": ["kofein zhorsuje spanek", "dochazi k napeti nebo rozhozeni rytmu"],
    },
    "methylation_folate": {
        "why": "U vas je to hlavni DNA most mezi methylaci, energii, B12 a budoucim ctenim homocysteinu.",
        "watchFor": [
            "vztah k homocysteinu",
            "vztah k B12 a folatu",
            "dlouhodoby trend energie a mentalniho vykonu",
        ],
        "linkWith": ["vitamin_b12", "homocysteine", "methylace", "energie"],
        "alertWhen": [
            "homocystein roste",
            "B12 a folat nedavaji dobry kontext",
            "energie dlouhodobe nesedi",
        ],
    },
    "b12_absorption": {
        "why": "Pro vas je to prakticky marker k tomu, aby se DNA nebrala abstraktne, ale testovala proti realnemu B12, energii a casem i homocysteinu.",
        "watchFor": [
            "vztah k laboratornimu B12",
            "signaly unavy",
            "neurologicky nebo kognitivni kontext",
        ],
        "linkWith": ["vitamin_b12", "homocysteine", "energie", "methylation_folate"],
        "alertWhen": [
            "B12 je slabsi",
            "roste homocystein",
            "subjektivni energie se zhorsuje",
        ],
    },
    "inflammation_regulation": {
        "why": "Pomaha cist zanetlivou a regeneracni vrstvu jako predispozici, ne hotovy verdikt.",
        "watchFor": ["souvislost se symptomy", "reakci na jidlo", "delku regenerace"],
        "linkWith": ["crp", "regenerace", "health signals"],
        "alertWhen": [
            "pridava se vyssi CRP",
            "reakce na jidlo jsou caste",
            "zatez se hur regeneruje",
        ],
    },
    "oxidative_stress_response": {
        "why": "Ukazuje, kde muze byt vyssi narok na regeneraci a antioxidadni ochranu.",
        "watchFor": ["vztah k pretizeni", "kvalitu regenerace", "toleranci zateze"],
        "linkWith": ["regenerace", "jidlo", "stres"],
        "alertWhen": ["obnoveni po zatezi je pomale", "subjektivne roste pretizeni"],
    },
    "insulin_sensitivity": {
        "why": "Pro vas je to jeden z nejdulezitejsich DNA markeru, protoze propojuje glukozu, triglyceridy, jidlo a dlouhodobou metabolickou stabilitu.",
        "watchFor": [
            "glukozu nalacno",
            "HbA1c",
            "reakci po jidle a energeticke propady",
        ],
        "linkWith": ["glucose_fasting", "hba1c", "triglycerides", "jidlo", "energie"],
        "alertWhen": [
            "glukoza roste",
            "triglyceridy se zhorsuji",
            "jidlo casto rozhazuje energii",
        ],
    },
    "lipid_regulation": {
        "why": "Tohle je u vas nejdulezitejsi DNA vrstva, protoze se primo potkava s realnym vyssim cholesterolem a autoritativnim doporucenim doktorky.",
        "watchFor": [
            "LDL",
            "triglyceridy",
            "reakci na kvalitu tuku a uzeniny",
        ],
        "linkWith": ["ldl_c", "total_cholesterol", "triglycerides", "care", "pohyb", "jidlo"],
        "alertWhen": [
            "lipidovy panel je vyssi opakovane",
            "jde proti rezimovym opatrenim",
            "laboratorni trend a doporuceni doktorky miri stejnym smerem",
        ],
    },
    "salt_pressure_response": {
        "why": "Pomaha cist citlivost na sul a tlak pres jidlo a dlouhodoby rezim.",
        "watchFor": ["prijem soli", "ultra-zpracovane jidlo", "tlakovy kontext"],
        "linkWith": ["krevni tlak", "jidlo", "kardiometabolicka oblast"],
        "alertWhen": ["rostou tlakove signaly", "slane jidlo dela horsi odezvu"],
    },
    "vitamin_a_conversion": {
        "why": "Je uzitecny pro vyber zdroju vitaminu A a cteni konverze beta-karotenu.",
        "watchFor": ["kvalitu zdroju vitaminu A", "pestrost stravy", "dlouhodobe fungovani"],
        "linkWith": ["jidlo", "vitaminy", "regenerace"],
        "alertWhen": ["strava je jednostranna", "spoleha jen na jednu formu zdroje"],
    },
}


def _enrich_marker(marker: GeneticPriorityMarker) -> GeneticPriorityMarker:
    hints = _ACTION_HINTS.get(marker.marker_key, {})
    return GeneticPriorityMarker(
        markerKey=marker.marker_key,
        title=marker.title,
        category=marker.category,
        priorityRank=marker.priority_rank,
        whyItMatters=marker.why_it_matters or str(hints.get("why") or marker.interpretation),
        watchFor=marker.watch_for or list(hints.get("watchFor") or []),
        linkWith=marker.link_with or list(hints.get("linkWith") or []),
        alertWhen=marker.alert_when or list(hints.get("alertWhen") or []),
        confidence=marker.confidence,
        recommendationStrength=marker.recommendation_strength,
        genotype=marker.genotype,
        interpretation=marker.interpretation,
    )


def _profile_priority_seed() -> list[GeneticPriorityMarker]:
    profile = get_genetic_profile()
    if not profile:
        return []

    seeded: list[GeneticPriorityMarker] = []
    for index, marker in enumerate(profile.markers, start=1):
        hints = _ACTION_HINTS.get(marker.key, {})
        seeded.append(
            GeneticPriorityMarker(
                markerKey=marker.key,
                title=marker.label,
                category=marker.category,
                priorityRank=index,
                whyItMatters=str(hints.get("why") or marker.interpretation),
                watchFor=list(hints.get("watchFor") or []),
                linkWith=list(hints.get("linkWith") or marker.related_domains),
                alertWhen=list(hints.get("alertWhen") or []),
                confidence=marker.confidence,
                recommendationStrength=marker.recommendation_strength,
                genotype=marker.genotype,
                interpretation=marker.interpretation,
            )
        )
    return seeded


def _merge_with_profile(config_markers: list[GeneticPriorityMarker]) -> list[GeneticPriorityMarker]:
    profile = get_genetic_profile()
    if not profile:
        return sorted((_enrich_marker(marker) for marker in config_markers), key=lambda item: item.priority_rank)

    by_key = {marker.marker_key: marker for marker in config_markers}
    merged: list[GeneticPriorityMarker] = []
    used_keys: set[str] = set()

    for fallback_rank, profile_marker in enumerate(profile.markers, start=1):
        configured = by_key.get(profile_marker.key)
        if configured:
            merged.append(
                _enrich_marker(
                    GeneticPriorityMarker(
                        markerKey=configured.marker_key,
                        title=configured.title or profile_marker.label,
                        category=configured.category or profile_marker.category,
                        priorityRank=configured.priority_rank,
                        whyItMatters=configured.why_it_matters,
                        watchFor=configured.watch_for,
                        linkWith=configured.link_with,
                        alertWhen=configured.alert_when,
                        confidence=profile_marker.confidence,
                        recommendationStrength=profile_marker.recommendation_strength,
                        genotype=profile_marker.genotype,
                        interpretation=profile_marker.interpretation,
                    )
                )
            )
            used_keys.add(profile_marker.key)
        else:
            hints = _ACTION_HINTS.get(profile_marker.key, {})
            merged.append(
                GeneticPriorityMarker(
                    markerKey=profile_marker.key,
                    title=profile_marker.label,
                    category=profile_marker.category,
                    priorityRank=100 + fallback_rank,
                    whyItMatters=str(hints.get("why") or profile_marker.interpretation),
                    watchFor=list(hints.get("watchFor") or []),
                    linkWith=list(hints.get("linkWith") or profile_marker.related_domains),
                    alertWhen=list(hints.get("alertWhen") or []),
                    confidence=profile_marker.confidence,
                    recommendationStrength=profile_marker.recommendation_strength,
                    genotype=profile_marker.genotype,
                    interpretation=profile_marker.interpretation,
                )
            )

    remaining_config = [
        _enrich_marker(marker)
        for marker in config_markers
        if marker.marker_key not in used_keys
    ]
    merged.extend(remaining_config)
    return sorted(merged, key=lambda item: item.priority_rank)


def list_priority_genetic_markers() -> list[GeneticPriorityMarker]:
    payload = read_json(_FILE_NAME, default=None)
    if payload is None:
        seeded = _profile_priority_seed()
        if seeded:
            write_json(
                _FILE_NAME,
                GeneticPriorityConfig(markers=seeded).model_dump(by_alias=True),
            )
        return seeded

    config = GeneticPriorityConfig.model_validate(payload)
    return _merge_with_profile(config.markers)


def replace_priority_genetic_markers(
    markers: list[GeneticPriorityMarker],
) -> list[GeneticPriorityMarker]:
    normalized = sorted((_enrich_marker(marker) for marker in markers), key=lambda item: item.priority_rank)
    write_json(
        _FILE_NAME,
        GeneticPriorityConfig(markers=normalized).model_dump(by_alias=True),
    )
    return _merge_with_profile(normalized)
