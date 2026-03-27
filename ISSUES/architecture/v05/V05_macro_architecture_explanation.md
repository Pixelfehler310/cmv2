# V05 Macro-Architecture Namespace Overview

Dieses Dokument erklärt das `V05_macro_architecture_overview.mmd` Diagramm. Es dient als "Wegweiser" und setzt die drei detaillierten V05-Planungsdiagramme (Business Entities, CRUD, Query) in einen kausalen Zusammenhang, vom Autoring bis hin zur tatsächlichen Spiel-Ausführung in V02.

Der VTT (Virtual Tabletop) / Campaign Manager ist in fünf große Makro-Domänen unterteilt, um Separation of Concerns (SoC) und Skalierbarkeit zu garantieren.

---

## 1. Identity & Campaign Domain (The Shell)
**Zuständig für:** Den SaaS-Wrapper, in dem sich die Nutzer bewegen. Hier existieren Accounts, Subscriptions, persistente Spielercharaktere und Campaign-Lobbys.
**Warum wichtig:** Content (Monster, Spells) nützt wenig ohne eine Berechtigungsprüfung, "wem" dieser Content gehört. Die Campaign definiert die *Content Policy* (darf "Tasha's Cauldron" in dieser Runde verwendet werden?). 
**Dazugehöriges Detaildiagramm:** `V05_business_and_content_entities_class_diagram`
*   **Datenfluss:** Ein Nutzer authorisiert eigenen "Homebrew"-Content (Übergang in WritePath). Eine Campaign limitiert, was der ReadPath (Query) als Suchergebnisse zurückgeben darf.

## 2. Content Mutation & Lifecycle Domain (The Write Path)
**Zuständig für:** Das exakte, versionssichere und validierte Schreiben von Definitionen in die Bibliothek. (CRUD-Operationen, Veröffentlichungs-Zustände, Wahrung von Link-Integrität).
**Warum wichtig:** D&D-Daten sind graphartig (eine Klasse referenziert ein Feature, das Feature referenziert einen Buff). Dieser Namespace garantiert, dass keine kaputten Links (Missing References) beim Speichern entstehen und keine Cycles (A -> B -> A) das Backend crashen.
**Dazugehöriges Detaildiagramm:** `V05_compendium_crud_and_definition_catalog_detailed_plan`
*   **Datenfluss:** Nimmt Autoren-Inputs auf, validiert das Regelwerk und schreibt das "Platonische Ideal" z.B. eines Monsters in die relationale Datenbank.

## 3. Content Query & Projection Domain (The Read Path)
**Zuständig für:** Das rasend schnelle Anzeigen von Content in Listen, Suchfeldern und Character Sheets.
**Warum wichtig:** VTTs erfordern ständige Suchvorgänge (z.B. Spieler tippt "Fireb..."). Eine reine relationale DB wäre hierfür zu langsam und komplex. Dieser Pfad trennt Command (Write) von Query (Read) – ein CQRS-Ansatz. Er baut ReadModels (Ansichts-Kopien) auf, damit der Client nicht bei jeder Aktion 20 Tabellen joinen muss.
**Dazugehöriges Detaildiagramm:** `V05_content_management_query_and_projection_detailed_plan`
*   **Datenfluss:** Befragt den Such-Index für IDs, reichert sie aus der Datenbank mit Details an, löst Abhängigkeiten (Links) auf und pusht das konsumfertige ReadModel an den Client (z.B. ins Character Sheet).

## 4. Storage & Indexing (Persistence)
**Zuständig für:** Die tatsächliche Datenspeicherung.
**Warum wichtig:** Trennt die absolute Wahrheit (Relational DB) vom performanten Zugriff (Search Index). Wenn ein neues Monster veröffentlicht wird, stellt ein Event (Change Data Capture) sicher, dass der Index aktualisiert wird.

## 5. V02 Combat Execution Runtime (The Consumer)
**Zuständig für:** Das Ausführen von Spielmechaniken. Das ist der Moment, in dem aus "Text im Regelbuch" echter Spielzustand wird (Trefferpunkte sinken, Flächeneffekte liegen auf dem Spielfeld).
**Warum wichtig:** Dieser Namespace ist flüchtig (ephemeral). Er hat nichts mit dem Bauen oder Speichern einer Kampagne zu tun. Das Macro-Diagramm veranschaulicht den **Hand-off**: Eine persistente Scene spawnt einen ephemeral Encounter. Ein persistentes Character Sheet instanziiert einen flüchtigen Actor-Knoten auf der Map.
**Dazugehöriges Detaildiagramm:** `V02_combat_actions_detailed_plan` und `V02_action_processing_details` (außerhalb des V05 Scopes).
*   **Datenfluss:** Erhält die fertigen, ausgelesenen Definitionen vom ReadPath und instanziiert sie als reaktive Live-Knoten im Speicher.

---

### Fazit & Architekturmuster
Das gesamte Layout orientiert sich am Prinzip **CQRS** (Command Query Responsibility Segregation) kombiniert mit **Domain Driven Design** (DDD). Das bedeutet:
1. Wie wir Content ändern, unterliegt strikten Regeln, um die Graphen der Spielregeln nicht zu verletzen (WritePath).
2. Wie wir Content lesen, ist stark denormalisiert für rasante Suchen, Filter und Baumauflösungen (ReadPath).
3. Wenn gespielt wird, verlässt der Zustand die V05-Persistenz und wird in die V02 State Machine übergeben.
