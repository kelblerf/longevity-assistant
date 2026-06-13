import { exampleAnswer } from "@/lib/example-answer";

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero">
        <span className="hero-kicker">Longevity-assistant</span>
        <h1>Osobni AI radce pro rytmus, dech, genetiku a dlouhovekost.</h1>
        <p>
          Scaffold prvni verze pocita s UBZ vrstvou, evidence/research vrstvou,
          DNA jako doporucujicim signalem a source-scope enginem nad Notion,
          OneNote, lokalnimi soubory a webem.
        </p>
        <div className="chips">
          <span className="chip">Chat-first + volitelny hlas</span>
          <span className="chip">UBZ philosophy layer</span>
          <span className="chip">NotebookLM research layer</span>
          <span className="chip">DNA conflict guidance</span>
        </div>
      </section>

      <section className="grid grid-two">
        <article className="panel stack">
          <h2>Jadro aplikace</h2>
          <ul className="list">
            <li>Identity layer pro kanonicky profil a pravidla.</li>
            <li>Health + genetics layer pro stav, biomarkery a DNA signaly.</li>
            <li>UBZ layer pro dech, rytmus, regeneraci a behavioralni vedeni.</li>
            <li>Evidence/research layer pro NotebookLM, biomarkery a web.</li>
            <li>Source-scope engine pro jadro a chytre rozsirovani zdroju.</li>
          </ul>
        </article>

        <aside className="panel stack">
          <h2>Vychozi zdroje</h2>
          <div className="mini-card">
            <strong>Core truth</strong>
            Profil, pravidla, rutiny, preference a schvalene geneticke
            interpretace.
          </div>
          <div className="mini-card">
            <strong>Domain knowledge</strong>
            UBZ, Pusty a dech v souvislostech, Blood Biomarkers, NotebookLM,
            Longevity Hub.
          </div>
          <div className="mini-card">
            <strong>Extended sources</strong>
            Dalsi Notion oblasti, OneNote, lokalni soubory, externi HDD a web.
          </div>
        </aside>
      </section>

      <section className="grid grid-two">
        <article className="panel stack">
          <h2>Sprint 1.1 domény</h2>
          <div className="mini-card">
            <strong>Meal entries</strong>
            Prvni zapisovatelna vrstva pro jidlo, meal type, poznamku a tagy.
            Guidance uz z poslednich jidel umi cist kontext.
          </div>
          <div className="mini-card">
            <strong>Health signals</strong>
            Prvni zapisovatelna vrstva pro signal, kategorii, zavaznost a cas.
            Tyto signaly se propisuji do denniho vedeni.
          </div>
        </article>

        <aside className="panel stack">
          <h2>Nove API body</h2>
          <ul className="list">
            <li>`GET /meals` a `POST /meals`</li>
            <li>`GET /health-signals` a `POST /health-signals`</li>
            <li>guidance odpovedi uz umi cist posledni jidlo a signal</li>
          </ul>
        </aside>
      </section>

      <section className="grid grid-two">
        <article className="panel stack">
          <h2>Ukazka struktury odpovedi</h2>
          <div className="assistant-preview">
            <div className="bubble user">
              Co je pro me dnes nejdulezitejsi z pohledu energie, dechu a
              regenerace?
            </div>
            <div className="bubble assistant">
              <strong>{exampleAnswer.summary}</strong>
              <div className="stack" style={{ marginTop: 12 }}>
                {exampleAnswer.sections.map((section) => (
                  <div key={section.kind} className="mini-card">
                    <strong>{section.title}</strong>
                    <span>{section.content}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </article>

        <aside className="panel stack">
          <h2>Selected scope</h2>
          <div className="meta-line">
            <span className="meta-pill">Mode: {exampleAnswer.selectedScope.mode}</span>
            <span className="meta-pill">
              Locked: {exampleAnswer.selectedScope.locked ? "ano" : "ne"}
            </span>
          </div>
          <div className="chips">
            {exampleAnswer.selectedScope.groups.map((group) => (
              <span className="chip" key={group}>
                {group}
              </span>
            ))}
          </div>

          <h3 style={{ marginBottom: 0 }}>Dalsi kroky</h3>
          <ul className="list">
            {exampleAnswer.nextSteps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ul>
        </aside>
      </section>
    </main>
  );
}
