from __future__ import annotations

from app.models import DailyCheckIn, HealthSignal
from app.models import MovementBlock, RoutineDefinition, RoutineStep
from app.services.storage_service import read_json


def _default_routines() -> list[RoutineDefinition]:
    return [
        RoutineDefinition(
            id="routine-morning-longevity",
            title="Ranní longevity rutina",
            category="morning_routine",
            goal="Klidný a vědomý start dne s dechem, hydratací, světlem a stabilitou.",
            timing="ihned po probuzení / prvních 20-35 minut dne",
            variants=["zkracena", "plna"],
            steps=[
                RoutineStep(
                    id="routine-step-breath-478",
                    title="Dechový blok 4-7-8 v posteli",
                    purpose="Zklidnění a vědomé nastartování dne.",
                    durationLabel="10 cyklu",
                    required=True,
                    fallback="3-5 cyklu",
                ),
                RoutineStep(
                    id="routine-step-hygiene",
                    title="Očištění jazyka a čištění zubů",
                    purpose="Hygienický start dne a přechod do denního režimu.",
                    durationLabel="krátký hygienický blok",
                    required=True,
                    fallback="minimální hygienické minimum",
                ),
                RoutineStep(
                    id="routine-step-hydration",
                    title="Hydratace cca 10 minut po probuzení",
                    purpose="Doplnění tekutin po noci před jídlem.",
                    durationLabel="cca 500 ml vody",
                    required=True,
                    fallback="250-300 ml vody",
                ),
                RoutineStep(
                    id="routine-step-balance",
                    title="Rovnováha a krátký pohybový start",
                    purpose="Stabilita, koordinace a aktivace těla.",
                    durationLabel="60 sekund",
                    required=True,
                    fallback="jedna krátká balanční varianta s oporou",
                ),
                RoutineStep(
                    id="routine-step-light-walk",
                    title="Denní světlo, slepice a ranní procházka",
                    purpose="Cirkadiánní rytmus, venek a přirozený pohyb.",
                    durationLabel="cca 10 minut nebo více",
                    required=True,
                    fallback="krátce vyjít ven na přirozené světlo",
                ),
                RoutineStep(
                    id="routine-step-barefoot",
                    title="Krátká chůze naboso",
                    purpose="Kontakt s podložkou a vědomé dokončení ranního bloku.",
                    durationLabel="krátký blok na konci chůze",
                    required=False,
                    fallback="vynechat při nevhodných podmínkách",
                ),
            ],
        )
    ]


def _default_movement_blocks() -> list[MovementBlock]:
    return [
        MovementBlock(
            id="movement-balance",
            title="Kratky stabilizacni blok",
            area="stabilita",
            frequency="denne nebo skoro denne",
            durationLabel="1-3 minuty",
            benefit="Rovnovaha, jistota a koordinace.",
            caution="Pri nejistote mit oporu.",
            examples=["Rovnovaha na jedne noze"],
            minimum_variant=[
                "1x 20-30 sekund balans na silnejsi noze s oporou",
                "kratke srovnani drzeni tela a dychani",
            ],
            full_variant=[
                "30 sekund balans na jedne noze",
                "30 sekund balans na druhe noze",
                "kratke vedome dorovnani postoje a dychani",
            ],
            sequence_steps=[
                "Postavte se stabilne a nachystejte si lehkou oporu.",
                "Drzte rovnovahu na jedne noze bez sileni do vykonu.",
                "Vymenit stranu a dokoncit stejnym klidnym tempem.",
            ],
        ),
        MovementBlock(
            id="movement-mobility",
            title="Mobilizacni rozchozeni tela",
            area="mobilita",
            frequency="denne nebo podle potreby",
            durationLabel="3-8 minut",
            benefit="Rozhybani tela bez tlaku na vykon.",
            caution="Nejit pres bolest a necpat rozsah nasilim.",
            examples=["Hluboky drep"],
            minimum_variant=[
                "jemne rozhybani kotniku, kycli a patere v malem rozsahu",
                "jen na hranici pohodli bez tlaku na zada",
            ],
            full_variant=[
                "kratke rozhybani kloubu a patere",
                "kontrolovany hluboky drep jen kdyz jsou zada v poradku",
                "plynule navazat dalsim lehkym rozhybanim",
            ],
            sequence_steps=[
                "Zacit jemnym rozhybanim v malem rozsahu.",
                "Teprve když tělo povolí, jít do větší mobility.",
                "Hluboký dřep zařadit jen bez signálu ze zad.",
            ],
        ),
        MovementBlock(
            id="movement-walk",
            title="Ranní venkovní chůze",
            area="chuze_kondice",
            frequency="denně",
            durationLabel="krátký blok podle času a podmínek",
            benefit="Rozchození těla, světlo a psychická stabilita.",
            caution="Nehnat tempo příliš brzy po probuzení.",
            examples=["Ranní procházka", "Chůze naboso na konci"],
            minimum_variant=[
                "krátce vyjít ven na přirozené světlo a obsloužit ranní venkovní minimum",
                "projít se v lehkém tempu bez tlaku na výkon nebo délku",
            ],
            full_variant=[
                "ranní procházka spojená se světlem, nakrmením slepic a klidným rozchozením těla",
                "na konci krátká chůze naboso podle povrchu, počasí a stavu chodidel",
            ],
            sequence_steps=[
                "Vyjit ven co nejdrive po rannim startu a dostat svetlo na oci.",
                "Spojit venkovni blok s nakrmenim slepic a klidnou ranní chuzi.",
                "Drzet prirozene tempo a nehnat kondici ani vykon.",
                "Pokud podminky dovoli, dokoncit kratkou chuzi naboso.",
            ],
        ),
        MovementBlock(
            id="movement-bike",
            title="Jízda na kole / cyklistika",
            area="chuze_kondice",
            frequency="pravidelně podle možností",
            durationLabel="podle typu dne a kapacity",
            benefit="Kondice, rytmus, lehká vytrvalost a vitalita.",
            caution="Nepřetížit se a respektovat energii, počasí a bezpečnost.",
            examples=["Klidná jízda", "Delší kondiční jízda"],
            minimum_variant=[
                "krátká klidná jízda v lehkém tempu podle energie dne",
                "bez tlaku na délku, rychlost nebo sportovní výkon",
            ],
            full_variant=[
                "delší pohodová jízda podle energie, počasí a kapacity zad",
                "stále bez přepínání do výkonového nebo soutěživého režimu",
            ],
            sequence_steps=[
                "Před jízdou zhodnotit energii, počasí, bezpečnost a stav zad.",
                "Začít klidným tempem bez sprintu, svižných nástupů nebo tlaku na výkon.",
                "Během jízdy hlídat, jestli tělo zůstává v pohodě a pohyb je pořád příjemný.",
                "Skončit dřív, pokud klesá kvalita pohybu nebo roste přetížení.",
            ],
        ),
        MovementBlock(
            id="movement-barefoot",
            title="Chůze naboso",
            area="stabilita_regenerace",
            frequency="podle podminek, idealne pravidelne",
            durationLabel="krátký blok na konci ranní chůze",
            benefit="Kontakt s podložkou, vnímání chodidel a vědomé dokončení venkovní části rána.",
            caution="Respektovat povrch, chlad, bezpečí a aktuální stav chodidel.",
            examples=["Krátký úsek naboso", "Vědomý krok přes chodidla"],
            minimum_variant=[
                "velmi krátký úsek naboso jen když jsou dobré podmínky",
                "pár vědomých kroků bez tlaku na délku nebo odolnost",
            ],
            full_variant=[
                "kratší vědomá chůze naboso na bezpečném povrchu",
                "vnímat chodidla, podložku a klidné dokončení ranního venkovního bloku",
            ],
            sequence_steps=[
                "Nejdřív zkontrolovat povrch, počasí a stav chodidel.",
                "Začít jen krátkým úsekem bez tlaku na výkon nebo otužilost.",
                "Držet klidný, vědomý krok a vnímat kontakt chodidel s podložkou.",
                "Skončit hned, když podmínky nejsou příjemné nebo bezpečné.",
            ],
        ),
        MovementBlock(
            id="movement-strength",
            title="Funkční silový blok 60+",
            area="sila",
            frequency="několikrát týdně",
            durationLabel="krátký samostatný blok",
            benefit="Funkční síla, držení těla a samostatnost.",
            caution="Respektovat techniku i aktuální stav.",
            examples=["Dřep u zdi", "Hluboký dřep"],
            minimum_variant=[
                "1-2 krat drep u zdi v kontrolovane verzi po 20-30 sekundach",
                "bez hlubokého dřepu při únavě, horším spánku nebo signálu ze zad",
            ],
            full_variant=[
                "2-3 kola drep u zdi po 20-40 sekundach podle kapacity",
                "3-5 kontrolovaných hlubokých dřepů jen když jsou záda bez přetížení",
            ],
            sequence_steps=[
                "Nejdřív zkontrolovat energii, spánek a signál ze zad.",
                "Začít dřepem u zdi jako bezpečnější základ a držet plynulé dýchání.",
                "Po krátké pauze rozhodnout, jestli je den jen na minimum, nebo i na plnou verzi.",
                "Hluboký dřep zařadit jen bez přetížení zad, bez bolesti a bez tlaku na rozsah.",
            ],
        ),
        MovementBlock(
            id="movement-regulation",
            title="Regenerační dechovo-pohybový blok",
            area="dech_regenerace",
            frequency="podle potřeby",
            durationLabel="3-10 minut",
            benefit="Zklidnění, návrat do rytmu a jemné uvolnění.",
            caution="Netlačit dech ani rozsah pohybu.",
            examples=["Pasivní vis na hrazdě"],
            minimum_variant=[
                "3-5 klidnych dechovych cyklu a jemne uvolneni tela",
                "jen pasivni vis nebo jen dech podle stavu a kapacity ramen",
            ],
            full_variant=[
                "vedome spojeni dechu, jemneho pohybu a kratkeho pasivniho visu",
                "delka 3-10 minut podle potreby regulace a aktualniho napeti",
            ],
            sequence_steps=[
                "Zacit klidnym dechem a zvolnenim tempa bez tlaku na vykon.",
                "Pridat jemny pohyb nebo kratky pasivni vis jen pokud jsou ramena a zada v klidu.",
                "Cely blok ukoncit ve stavu vetsiho klidu a regulace, ne dalsi aktivace.",
            ],
        ),
    ]


def list_routines() -> list[RoutineDefinition]:
    payload = read_json("routine-definitions.json", None)
    if payload is None:
        return _default_routines()
    return [RoutineDefinition.model_validate(item) for item in payload]


def list_movement_blocks() -> list[MovementBlock]:
    payload = read_json("movement-blocks.json", None)
    if payload is None:
        return _default_movement_blocks()
    return [MovementBlock.model_validate(item) for item in payload]


def routine_highlights(limit: int = 3) -> list[str]:
    routines = list_routines()
    highlights: list[str] = []
    for routine in routines[:limit]:
        if routine.steps:
            first_steps = ", ".join(step.title for step in routine.steps[:3])
            highlights.append(f"{routine.title}: {first_steps}")
        else:
            highlights.append(f"{routine.title}: bez kroku")
    return highlights


def movement_highlights(limit: int = 3) -> list[str]:
    blocks = list_movement_blocks()
    return [f"{block.title} - {', '.join(block.examples[:2])}" for block in blocks[:limit]]


def _contains_any(text: str | None, keywords: list[str]) -> bool:
    if not text:
        return False
    normalized = text.lower()
    return any(keyword in normalized for keyword in keywords)


def recommend_movement_plan(
    check_in: DailyCheckIn | None,
    signal: HealthSignal | None,
) -> dict[str, list[str] | str]:
    blocks = list_movement_blocks()
    block_by_id = {block.id: block for block in blocks}

    recommended_ids = ["movement-balance", "movement-walk"]
    avoided_ids: list[str] = []
    reasons: list[str] = []
    guardrails = [
        "Pohyb drzet primerene veku 60+ a nevolit rychle nebo svihove cviceni.",
        "Chránit záda a levé rameno při výběru bloku.",
    ]
    mode = "standard"

    if check_in and (check_in.energy <= 4 or check_in.sleep_quality <= 5 or check_in.stress >= 7):
        mode = "minimum"
        recommended_ids = ["movement-regulation", "movement-balance", "movement-walk"]
        avoided_ids.append("movement-strength")
        reasons.append(
            "Nižší energie, horší spánek nebo vyšší stres dnes ukazují na lehčí režim."
        )
        guardrails.append(
            "Po spatnem spanku nebo unave nevolit silovy blok a drzet jen dech, rovnovahu a kratkou chuzi."
        )

    back_or_shoulder_load = False
    if signal:
        if (
            _contains_any(signal.title, ["zada", "ramen", "bedra"])
            or _contains_any(signal.notes, ["zada", "ramen", "bedra", "pretiz"])
            or signal.category in {"movement", "recovery", "stress"}
        ):
            back_or_shoulder_load = True
    if check_in and _contains_any(check_in.notes, ["zada", "ramen", "pretiz"]):
        back_or_shoulder_load = True

    if back_or_shoulder_load:
        mode = "protective"
        for block_id in ["movement-strength", "movement-mobility"]:
            if block_id not in avoided_ids:
                avoided_ids.append(block_id)
        if "movement-regulation" not in recommended_ids:
            recommended_ids.insert(0, "movement-regulation")
        reasons.append(
            "Kdyz je citit pretezene zada nebo rameno, asistent ma ubrat a nechranit vykon na silu."
        )
        guardrails.append(
            "Při přetížení zad nevolit hluboké dřepy a jít spíš do regulace, rovnováhy a krátké chůze."
        )

    if mode == "standard":
        recommended_ids = ["movement-balance", "movement-mobility", "movement-walk"]
        reasons.append(
            "Když není signál únavy ani přetížení, můžete držet běžné pohybové minimum a jemnou mobilitu."
        )
        guardrails.append(
            "Plnou verzi volit jen když tělo nehlásí únavu, přetížená záda nebo horší spánek."
        )

    recommended_titles = [
        block_by_id[block_id].title for block_id in recommended_ids if block_id in block_by_id
    ]
    avoided_titles = [
        block_by_id[block_id].title for block_id in avoided_ids if block_id in block_by_id
    ]

    deduped_guardrails: list[str] = []
    for item in guardrails:
        if item not in deduped_guardrails:
            deduped_guardrails.append(item)

    return {
        "mode": mode,
        "recommendedTitles": recommended_titles,
        "avoidedTitles": avoided_titles,
        "reasons": reasons,
        "guardrails": deduped_guardrails[:4],
    }
