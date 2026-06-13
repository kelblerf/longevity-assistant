const MOJIBAKE_DETECTOR = /[\u00C3\u00C5\u00C4\u00C2]/;

export function repairMojibakeText(value: string): string {
  if (!value) return value;

  let next = value;

  for (let i = 0; i < 3; i += 1) {
    if (!MOJIBAKE_DETECTOR.test(next)) break;

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

export function normalizeTextTree<T>(value: T): T {
  if (typeof value === "string") {
    return repairMojibakeText(value) as T;
  }

  if (Array.isArray(value)) {
    return value.map((item) => normalizeTextTree(item)) as T;
  }

  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([key, entry]) => [key, normalizeTextTree(entry)]),
    ) as T;
  }

  return value;
}
