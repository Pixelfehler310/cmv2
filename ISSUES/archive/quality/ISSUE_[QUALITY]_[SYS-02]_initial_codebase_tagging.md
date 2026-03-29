# ISSUE: Initial Codebase Tagging (`__production_status__`)

## Problembeschreibung
Nach Einführung der **Production Status Guardrails** müssen alle existierenden Dateien im Projekt initial markiert werden, um den Ist-Zustand abzubilden und den Purity-Check zu aktivieren. Ohne Markierung werden Dateien standardmäßig als `unchecked` gewertet.

## Zielsetzung
Einmalige Durchsicht der aktuellen Code-Basis und Hinzufügen von `__production_status__` in den Datei-Header.

---

## Durchführungsvorschrift

### 1. Legacy MVP Code (`Bronze` / `Broken` / `Unchecked`)
Alle Dateien in folgenden Pfaden werden initial markiert:
- `backend/src/legacy/` (**Bronze** oder **Broken**, falls veraltet/fehlerhaft)
- Prototypen-Logik in `backend/src/engine/` (**Bronze**)

### 2. Neuer V05 Standard (`Silver` / `Gold`)
Dateien, die bereits im neuen Domain-Pattern (DDD/Repositories) erstellt wurden, werden als `silver` markiert:
- `backend/src/systems/dnd5e/`

### 3. Core-Komponenten (`Silver`)
Logik, die universell stabil ist, aber evtl. noch Refactoring benötigt:
- `backend/src/core/`

---

## Checkliste
- [ ] Alle Python-Dateien in `backend/src/` gescannt.
- [ ] Metadata `__production_status__` hinzugefügt.
- [ ] Purity-Test erfolgreich gegen den neuen Scope (`systems/dnd5e/`) geprüft.

---

## Akzeptanzkriterien
- [ ] Keine Datei im `systems/dnd5e/` Pfad ist `unchecked` oder `bronze`.
- [ ] Der CI-Build (Pytest) ist grün.
