# WS Combat V2: Targeting und Aiming Konzept

## Ziel

Dieses Dokument beschreibt ein robustes Frontend-Konzept fuer Targeting/Aiming im ws-combat-v2 Flow.

Hauptziele:

- Eindeutige Click-Interpretation pro UI-Mode
- Sichtbare, verlassliche Highlights fuer moegliche Ziele
- Kein Konflikt zwischen Token-Auswahl und Target-Auswahl
- Backend bleibt Authoritative Source of Truth

## Aktuelle Probleme

1. Moegliche Targets werden nicht konsistent gehighlighted.
2. Click auf ein Token waehlt teils das Objekt aus, statt es als Ziel zu setzen.
3. Targeting-Flow ist in mehreren Komponenten verteilt und nicht zentral priorisiert.
4. Der Mode-Uebergang ist nicht streng genug, dadurch entstehen Mischzustaende.

## Leitprinzipien

1. Backend ist Truth: Frontend rendert nur Snapshot/Preview und sendet Intents.
2. Ein zentraler Interaction State steuert alle Pointer/Click Entscheidungen.
3. Pro Action gilt ein expliziter Targeting Contract.
4. Ein zentraler Click Resolver entscheidet nach Prioritaet, nicht einzelne Komponenten ad hoc.

## Begriffe

- Interaction Mode: UI Zustand, in dem ein Click interpretiert wird.
- Targeting Contract: Backend-definierte Anforderungen fuer Zielwahl.
- Click Resolver: Zentrale Funktion, die Clicks anhand von Mode + Contract mappt.

## Interaction Mode FSM

Empfohlene States:

1. `idle`
2. `movement_preview`
3. `movement_commit`
4. `action_selected`
5. `target_pick_entity`
6. `target_pick_cell`
7. `target_pick_direction`
8. `confirm`
9. `executing`
10. `error_recover`

### Kernregeln

- Nur der aktive Mode bestimmt die Click-Bedeutung.
- In `executing` werden neue Auswahl-Clicks ignoriert.
- `Esc` oder Cancel bringt immer nach `idle` zurueck.
- Ein Statewechsel darf nur ueber definierte Transitionen passieren.

## Targeting/Aiming Modes (fachlich)

Empfohlene minimale Menge:

1. `self`
2. `entity_single`
3. `entity_multi`
4. `cell_point`
5. `template_burst` (origin)
6. `template_line` (origin + direction)
7. `template_cone` (origin + direction)

### Semantik

- `self`: kein Target-Pick, direkte Ausfuehrung.
- `entity_single`: genau ein gueltiges Token.
- `entity_multi`: mehrere Tokens zwischen min/max.
- `cell_point`: eine gueltige Zelle.
- `template_*`: erst Origin waehlen, optional Direction, dann bestaetigen.

## Backend Targeting Contract

Der Snapshot pro Action sollte einen klaren Contract liefern.

Empfohlene Struktur:

```json
{
  "targeting_contract": {
    "kind": "entity_single",
    "entity_filter": "enemy",
    "min_targets": 1,
    "max_targets": 1,
    "requires_los": false,
    "requires_path": false,
    "template": null,
    "confirm_policy": "single_click"
  }
}
```

Fuer Template-Angriffe:

```json
{
  "targeting_contract": {
    "kind": "template_cone",
    "entity_filter": "enemy",
    "min_targets": 0,
    "max_targets": 99,
    "requires_los": false,
    "requires_path": false,
    "template": {
      "shape": "cone",
      "size": 3,
      "needs_direction": true
    },
    "confirm_policy": "two_step_confirm"
  }
}
```

## Click Resolver (zentral)

Alle Grid/Token Clicks laufen durch eine zentrale Funktion, z. B.:

```ts
resolveClick({
  mode,
  clickedCell,
  tokenUnderCursor,
  contract,
  eligibility,
}) -> InteractionEffect[]
```

### Prioritaetsregeln

1. Wenn `mode = target_pick_entity`: Token hat Vorrang vor Cell.
2. Wenn `mode = target_pick_cell`: Cell hat Vorrang; Token-Click wird auf Cell gemappt.
3. Wenn Click nicht gueltig ist: keine implizite Objekt-Auswahl.
4. Wenn `mode = idle`: nur normale Auswahl/Navigation, keine Targeting-Selektion.

## Highlighting-Regeln

Highlights kommen nur aus backend-authoritativen Daten:

- Entity-Highlights: `eligible_target_ids`
- Cell-Highlights: `eligible_cells`
- AoE-Projection: `template_projection.affected_cells`

UI-Regeln:

1. Nur im passenden Mode highlighten.
2. Ausgewaehltes Ziel visuell von nur eligible unterscheiden.
3. Invalide Klickflaechen neutral anzeigen.

## UX-Flows

### Single Target

1. Action waehlen -> `target_pick_entity`
2. Eligible Tokens highlighten
3. Token click -> Ziel gesetzt
4. Auto-confirm (oder Confirm-Button je Contract)

### AoE Burst

1. Action waehlen -> `target_pick_cell`
2. Eligible Origin Cells highlighten
3. Cell click -> Projection anzeigen + `confirm`
4. Confirm -> request_action mit `template_origin`

### AoE Line/Cone

1. Action waehlen -> `target_pick_cell`
2. Origin click -> `target_pick_direction`
3. Direction click -> Projection locken + `confirm`
4. Confirm -> request_action mit `template_origin` + `template_direction`

## Architekturvorschlag fuer Umsetzung

### Phase A: Stabilisierung

- Konsolidiere Targeting-Mappings (`single_target` statt Mischformen).
- Fuehre zentralen `interactionMode` im Store ein.
- Gating: keine Click-Interpretation ausserhalb des aktiven Modes.

### Phase B: Resolver

- Fuehre zentralen Click Resolver ein.
- Leite Player-Grid und Action-Surface auf denselben Resolver.
- Entferne ad hoc Click-Entscheidungen in Einzelkomponenten.

### Phase C: Contract-Haertung

- Erweitere executable action payload um `targeting_contract`.
- Frontend rendert komplett contract-driven.
- Remove implizite Frontend-Inferenz fuer Zieltypen.

### Phase D: Tests und Hardening

- Unit-Tests fuer Resolver (Mode x Click x Contract Matrix).
- Integration-Tests fuer Preview->Confirm Flows.
- Regression-Tests fuer "Token selected statt Target selected".

## Testmatrix (Auszug)

1. `idle` + Token click -> nur Auswahl, kein Target.
2. `target_pick_entity` + non-eligible Token -> keine Auswahl.
3. `target_pick_entity` + eligible Token -> target gesetzt.
4. `target_pick_cell` + eligible Cell -> origin gesetzt.
5. `target_pick_direction` + direction click -> projection updated.
6. `executing` + click -> ignoriert.
7. `action_denied` Event -> Mode reset + Hint anzeigen.

## Konkrete Akzeptanzkriterien

1. Moegliche Ziele sind in jedem Targeting-Mode sichtbar markiert.
2. Click auf Token in Targeting-Mode setzt Target, nicht Objektselektion.
3. Keine Cross-Mode Fehlklicks (z. B. Move-Click waehrend Targeting).
4. Kein Request-Loop durch State- oder Preview-Updates.
5. Fuer jeden Targeting-Mode existiert mindestens ein automatisierter Test.

## Offene Entscheidungen

1. Auto-confirm bei `entity_single` oder immer expliziter Confirm-Button?
2. Soll Multi-Target als Toggle-Chips oder direkt im Grid markiert werden?
3. Soll Right-Click global als Cancel in allen Non-Idle Modes gelten?

## Empfehlung

Kurzfristig Phase A+B priorisieren, damit die aktuellen UX-Fehler sofort verschwinden.
Mittelfristig Phase C einfuehren, damit Frontend strikt contract-driven wird und nicht durch lokale Inferenz regressionsanfaellig bleibt.
