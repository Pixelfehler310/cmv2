# V05 Macro-Architecture Overview Plan

Du möchtest ein übergreifendes "Big Picture" Diagramm, das die drei bisherigen Detail-Diagramme aus V05 (CRUD, Query/Projection, und Business Entities) zusammenführt. Anstatt noch tiefer ins Detail zu gehen, wird dies ein **Namespace/Modul-Diagramm**, das zeigt, *wie* die großen Blöcke (Namespaces) miteinander interagieren und zusammen das gesamte V05 Content Management System bilden.

## Proposed Changes

### [NEW] `ISSUES/architecture/v05/V05_macro_architecture_overview.mmd`
Ein High-Level C4-artiges oder reines Namespace-Beziehungs-Diagramm. Es wird die Zusammenhänge folgender Hauptblöcke (basierend auf den drei existierenden V05-Diagrammen) visualisieren:

1.  **Identity & Campaign Context** (SaaS Core: Users, Campaigns, Assets)
2.  **Definition Catalog & CRUD Lifecycle** (Schreib-Pfad: Validation, Publishing, Linked Entries)
3.  **Query & Projection Pipeline** (Lese-Pfad: Search Index, deterministisches Querying, ReadModels)
4.  **Client/Consumer Boundary** (Wie die UIs und V02 Combat Runtimes diese Daten konsumieren)

Das Diagramm zeigt den Datenfluss: Wie ein "Draft" durch den CRUD-Pfad in den Index gelangt, von der Query-Pipeline gelesen wird, und letztendlich über eine Campaign in einen V02 Actor instanziiert wird.

### [NEW] `ISSUES/architecture/v05/V05_macro_architecture_explanation.md`
Ein Begleitdokument, das streng nach Namespaces gegliedert ist (passend zum Diagramm). Jede Sektion erklärt:
- **Was** dieser Namespace tut (Zuständigkeit).
- **Warum** er wichtig ist (z.B. warum trennen wir Query von CRUD, warum sind Assets ausgelagert).
- **Welches Detail-Diagramm** für tiefere Einblicke konsultiert werden muss.

## User Review Required

> [!QUESTION]
> Ist es sinnvoll, V02 (Combat Runtime) als externen "Konsumenten" auf dem Rand dieses Übersichtsdiagramms mit abzubilden, um zu zeigen, wo die V05-Inhalte enden und das Spielgeschehen beginnt? 

## Verification Plan
1. Ich generiere das PlantUML/Mermaid Namespace-Diagramm (`.mmd`).
2. Ich schreibe das detaillierte Begleitdokument (`.md`).
3. Du kannst prüfen, ob alle großen Konzepte aus V05 einen klaren Platz und eine logische Verbindung zueinander haben.
