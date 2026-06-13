from __future__ import annotations

from app.models import BiomarkerPriorityConfig, BiomarkerPriorityMarker
from app.services.storage_service import read_json, write_json


_ACTION_HINTS: dict[str, dict[str, list[str]]] = {
    "ldl_c": {
        "watchFor": ["dlouhodobe vyssi trend", "vztah k celemu lipidovemu panelu", "soulad s doporucenim doktorky"],
        "linkWith": ["total_cholesterol", "hdl_c", "triglycerides", "pohyb", "jidlo"],
        "alertWhen": ["je vyrazne mimo rozsah", "drzi se vysoko opakovane", "jde proti rezimovym opatrenim v case"],
    },
    "total_cholesterol": {
        "watchFor": ["jestli potvrzuje smer lipidoveho panelu", "jestli neni cten izolovane"],
        "linkWith": ["ldl_c", "hdl_c", "triglycerides"],
        "alertWhen": ["roste spolu s LDL nebo triglyceridy", "je hodnocen bez ostatnich lipidu"],
    },
    "triglycerides": {
        "watchFor": ["vztah k jidlu a metabolickemu rytmu", "soubeh s glukozovou oblasti"],
        "linkWith": ["glucose_fasting", "hba1c", "total_cholesterol", "jidlo"],
        "alertWhen": ["rostou spolu s glukozovou oblasti", "dlouhodobe se zhorsuji"],
    },
    "hdl_c": {
        "watchFor": ["pozici uvnitr celeho lipidoveho panelu", "ne cteni bez kontextu LDL a triglyceridu"],
        "linkWith": ["ldl_c", "total_cholesterol", "triglycerides", "pohyb"],
        "alertWhen": ["je vyrazne slabsi proti zbytku panelu", "panel se cte jen podle jednoho cisla"],
    },
    "glucose_fasting": {
        "watchFor": ["trend v case", "vazbu na jidlo a energii", "soubeh s HbA1c"],
        "linkWith": ["hba1c", "triglycerides", "jidlo", "energie"],
        "alertWhen": ["roste opakovane", "nejde dohromady s dennim fungovanim", "zvysuje se i HbA1c"],
    },
    "vitamin_b12": {
        "watchFor": ["vztah k energii", "vztah k DNA signalu", "vazbu na homocystein"],
        "linkWith": ["homocysteine", "folate", "dna", "energie"],
        "alertWhen": ["je slabsi a soucasne roste homocystein", "nesedi s energii a nervovou oblasti"],
    },
    "homocysteine": {
        "watchFor": ["vztah k B12 a folatu", "methylacni souvislosti", "trend v case"],
        "linkWith": ["vitamin_b12", "folate", "dna", "kardiometabolicka oblast"],
        "alertWhen": ["roste navzdory slusnemu B12", "ukazuje nesoulad v methylacni vrstve"],
    },
    "vitamin_d_25oh": {
        "watchFor": ["dlouhodoby stav", "sezonni souvislosti", "vazbu na vitalitu"],
        "linkWith": ["energie", "regenerace", "pohyb venku"],
        "alertWhen": ["je dlouhodobe nizky", "neodpovida subjektivni vitalite", "chybi dlouhodoby trend"],
    },
    "hba1c": {
        "watchFor": ["dlouhodoby glukozovy trend", "soulad s glukozou nalacno"],
        "linkWith": ["glucose_fasting", "triglycerides", "jidlo", "energie"],
        "alertWhen": ["roste soubezne s glukozou nalacno", "trend se zhorsuje i pri rezimovych zmenach"],
    },
    "ferritin": {
        "watchFor": ["vztah k energii", "dlouhodobe zasoby", "souvislost s dalsimi zelezitymi markery"],
        "linkWith": ["iron_serum", "transferrin", "energie"],
        "alertWhen": ["je nizky a soucasne klesa energie", "nesedi se zbytkem zelezite vrstvy"],
    },
    "crp": {
        "watchFor": ["akutni vs dlouhodoby signal", "souvislost se symptomy a regeneraci"],
        "linkWith": ["health signals", "regenerace", "symptomy"],
        "alertWhen": ["je opakovane vyssi", "nejde dohromady s klidnym subjektivnim stavem"],
    },
    "tsh": {
        "watchFor": ["trend cele thyroid osy", "vztah k energii a rytmu"],
        "linkWith": ["ft4", "ft3", "energie", "ritmus"],
        "alertWhen": ["se rozchazi s FT4 a FT3", "dlouhodobe nejde dohromady s energii"],
    },
    "ft4": {
        "watchFor": ["pozici uvnitr thyroid panelu", "vazbu na TSH a FT3"],
        "linkWith": ["tsh", "ft3", "energie"],
        "alertWhen": ["je vyrazne mimo osu se zbytkem panelu", "panel se meni jednim smerem"],
    },
    "ft3": {
        "watchFor": ["pozici v thyroid panelu", "vazbu na energii a regulaci"],
        "linkWith": ["tsh", "ft4", "energie", "regulace"],
        "alertWhen": ["je v nesouladu se zbytkem thyroid panelu", "neodpovida subjektivni energii"],
    },
}


def _enrich_marker(marker: BiomarkerPriorityMarker) -> BiomarkerPriorityMarker:
    hints = _ACTION_HINTS.get(marker.marker_key, {})
    return BiomarkerPriorityMarker(
        markerKey=marker.marker_key,
        title=marker.title,
        category=marker.category,
        priorityRank=marker.priority_rank,
        whyItMatters=marker.why_it_matters,
        watchFor=marker.watch_for or hints.get("watchFor", []),
        linkWith=marker.link_with or hints.get("linkWith", []),
        alertWhen=marker.alert_when or hints.get("alertWhen", []),
    )


def _seed_priority_biomarkers() -> list[BiomarkerPriorityMarker]:
    return [
        BiomarkerPriorityMarker(
            markerKey="ldl_c",
            title="LDL cholesterol",
            category="lipids",
            priorityRank=1,
            whyItMatters="Primarni lipidovy marker pro vazbu na preventivni doporuceni doktorky a kardiometabolickou prioritu.",
            watchFor=["dlouhodobe vyssi trend", "vztah k celemu lipidovemu panelu", "soulad s doporucenim doktorky"],
            linkWith=["total_cholesterol", "hdl_c", "triglycerides", "pohyb", "jidlo"],
            alertWhen=["je vyrazne mimo rozsah", "drzi se vysoko opakovane", "jde proti rezimovym opatrenim v case"],
        ),
        BiomarkerPriorityMarker(
            markerKey="total_cholesterol",
            title="Celkovy cholesterol",
            category="lipids",
            priorityRank=2,
            whyItMatters="Dava rychly prehled lipidove oblasti a ma byt cteny spolu s LDL, HDL a triglyceridy.",
            watchFor=["jestli potvrzuje smer lipidoveho panelu", "jestli neni cten izolovane"],
            linkWith=["ldl_c", "hdl_c", "triglycerides"],
            alertWhen=["roste spolu s LDL nebo triglyceridy", "je hodnocen bez ostatnich lipidu"],
        ),
        BiomarkerPriorityMarker(
            markerKey="triglycerides",
            title="Triglyceridy",
            category="lipids",
            priorityRank=3,
            whyItMatters="Pomahaji cist vztah mezi jidlem, metabolickym rytmem a celou lipidovou oblasti.",
            watchFor=["vztah k jidlu a metabolickemu rytmu", "soubeh s glukozovou oblasti"],
            linkWith=["glucose_fasting", "hba1c", "total_cholesterol", "jidlo"],
            alertWhen=["rostou spolu s glukozovou oblasti", "dlouhodobe se zhorsuji"],
        ),
        BiomarkerPriorityMarker(
            markerKey="hdl_c",
            title="HDL cholesterol",
            category="lipids",
            priorityRank=4,
            whyItMatters="Doplnuje lipidovy panel a ma smysl ho cist spolu s ostatnimi lipidy, ne izolovane.",
            watchFor=["pozici uvnitr celeho lipidoveho panelu", "ne cteni bez kontextu LDL a triglyceridu"],
            linkWith=["ldl_c", "total_cholesterol", "triglycerides", "pohyb"],
            alertWhen=["je vyrazne slabsi proti zbytku panelu", "panel se cte jen podle jednoho cisla"],
        ),
        BiomarkerPriorityMarker(
            markerKey="glucose_fasting",
            title="Glukoza nalacno",
            category="glucose_metabolism",
            priorityRank=5,
            whyItMatters="Ukazuje zakladni glukozovy signal a dobre se propojuje s jidlem, energii a rytmem dne.",
            watchFor=["trend v case", "vazbu na jidlo a energii", "soubeh s HbA1c"],
            linkWith=["hba1c", "triglycerides", "jidlo", "energie"],
            alertWhen=["roste opakovane", "nejde dohromady s dennim fungovanim", "zvysuje se i HbA1c"],
        ),
        BiomarkerPriorityMarker(
            markerKey="vitamin_b12",
            title="Vitamin B12",
            category="vitamins",
            priorityRank=6,
            whyItMatters="Je prakticky dulezity pro energii, nervovy system a vazbu na DNA signal kolem B12.",
            watchFor=["vztah k energii", "vztah k DNA signalu", "vazbu na homocystein"],
            linkWith=["homocysteine", "folate", "dna", "energie"],
            alertWhen=["je slabsi a soucasne roste homocystein", "nesedi s energii a nervovou oblasti"],
        ),
        BiomarkerPriorityMarker(
            markerKey="homocysteine",
            title="Homocystein",
            category="methylation",
            priorityRank=7,
            whyItMatters="Dobre propojuje methylaci, B12, folat a dlouhodoby kardiometabolicky kontext.",
            watchFor=["vztah k B12 a folatu", "methylacni souvislosti", "trend v case"],
            linkWith=["vitamin_b12", "folate", "dna", "kardiometabolicka oblast"],
            alertWhen=["roste navzdory slusnemu B12", "ukazuje nesoulad v methylacni vrstve"],
        ),
        BiomarkerPriorityMarker(
            markerKey="vitamin_d_25oh",
            title="Vitamin D 25-OH",
            category="vitamins",
            priorityRank=8,
            whyItMatters="Je dulezity pro celkovou vitalitu, imunitu a dlouhodobe fungovani v longevity vrstve.",
            watchFor=["dlouhodoby stav", "sezonni souvislosti", "vazbu na vitalitu"],
            linkWith=["energie", "regenerace", "pohyb venku"],
            alertWhen=["je dlouhodobe nizky", "neodpovida subjektivni vitalite", "chybi dlouhodoby trend"],
        ),
        BiomarkerPriorityMarker(
            markerKey="hba1c",
            title="HbA1c",
            category="glucose_metabolism",
            priorityRank=9,
            whyItMatters="Dava dlouhodobejsi pohled na glukozovou oblast a doplnuje glukozu nalacno.",
            watchFor=["dlouhodoby glukozovy trend", "soulad s glukozou nalacno"],
            linkWith=["glucose_fasting", "triglycerides", "jidlo", "energie"],
            alertWhen=["roste soubezne s glukozou nalacno", "trend se zhorsuje i pri rezimovych zmenach"],
        ),
        BiomarkerPriorityMarker(
            markerKey="ferritin",
            title="Ferritin",
            category="iron",
            priorityRank=10,
            whyItMatters="Pomaha cist zelezitou a energetickou vrstvu, ne jen akutni serum iron.",
            watchFor=["vztah k energii", "dlouhodobe zasoby", "souvislost s dalsimi zelezitymi markery"],
            linkWith=["iron_serum", "transferrin", "energie"],
            alertWhen=["je nizky a soucasne klesa energie", "nesedi se zbytkem zelezite vrstvy"],
        ),
        BiomarkerPriorityMarker(
            markerKey="crp",
            title="CRP",
            category="inflammation",
            priorityRank=11,
            whyItMatters="Je dobry orientacni marker zanetlive zateze a hodne se opira o kontext symptomu a regenerace.",
            watchFor=["akutni vs dlouhodoby signal", "souvislost se symptomy a regeneraci"],
            linkWith=["health signals", "regenerace", "symptomy"],
            alertWhen=["je opakovane vyssi", "nejde dohromady s klidnym subjektivnim stavem"],
        ),
        BiomarkerPriorityMarker(
            markerKey="tsh",
            title="TSH",
            category="thyroid",
            priorityRank=12,
            whyItMatters="Je zakladni vstup do cteni stitne zlazy a ma smysl ho cist spolu s FT4 a FT3.",
            watchFor=["trend cele thyroid osy", "vztah k energii a rytmu"],
            linkWith=["ft4", "ft3", "energie", "ritmus"],
            alertWhen=["se rozchazi s FT4 a FT3", "dlouhodobe nejde dohromady s energii"],
        ),
        BiomarkerPriorityMarker(
            markerKey="ft4",
            title="FT4",
            category="thyroid",
            priorityRank=13,
            whyItMatters="Doplnuje stitnou osu a pomaha odlisit orientacni interpretaci od jedne izolovane hodnoty.",
            watchFor=["pozici uvnitr thyroid panelu", "vazbu na TSH a FT3"],
            linkWith=["tsh", "ft3", "energie"],
            alertWhen=["je vyrazne mimo osu se zbytkem panelu", "panel se meni jednim smerem"],
        ),
        BiomarkerPriorityMarker(
            markerKey="ft3",
            title="FT3",
            category="thyroid",
            priorityRank=14,
            whyItMatters="Uzavira zakladni thyroid panel ve vazbe na energii a celkovou regulaci organismu.",
            watchFor=["pozici v thyroid panelu", "vazbu na energii a regulaci"],
            linkWith=["tsh", "ft4", "energie", "regulace"],
            alertWhen=["je v nesouladu se zbytkem thyroid panelu", "neodpovida subjektivni energii"],
        ),
    ]


def list_priority_biomarkers() -> list[BiomarkerPriorityMarker]:
    payload = read_json("biomarker-priority-markers.json", default=None)
    if payload is None:
        markers = [_enrich_marker(item) for item in _seed_priority_biomarkers()]
        write_json(
            "biomarker-priority-markers.json",
            BiomarkerPriorityConfig(markers=markers).model_dump(by_alias=True),
        )
        return markers

    config = BiomarkerPriorityConfig.model_validate(payload)
    return sorted((_enrich_marker(item) for item in config.markers), key=lambda item: item.priority_rank)


def replace_priority_biomarkers(markers: list[BiomarkerPriorityMarker]) -> list[BiomarkerPriorityMarker]:
    normalized = sorted((_enrich_marker(item) for item in markers), key=lambda item: item.priority_rank)
    write_json(
        "biomarker-priority-markers.json",
        BiomarkerPriorityConfig(markers=normalized).model_dump(by_alias=True),
    )
    return normalized


def priority_marker_keys() -> list[str]:
    return [item.marker_key for item in list_priority_biomarkers()]
