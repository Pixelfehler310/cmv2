# ISSUE: Implementierung "Production Status" Guardrails

## Problembeschreibung
Während des Re-Engineerings vom MVP zur Produktionsreife vermischen sich unreifer Prototypen-Code und neuer, qualitätsgeprüfter Code. Um die architektonische Integrität zu wahren, benötigen wir ein System, das den Reifegrad jeder Datei explizit markiert und verhindert, dass "Unchecked" oder "Bronze" Code in die neuen Produktions-Scopes gelangt.

## Zielsetzung
Einführung eines dreistufigen Tier-Systems (**Gold, Silber, Bronze**) sowie eines Standard-Status (**Unchecked**). Ein automatisierter Check soll sicherstellen, dass neue Kern-Komponenten nur auf verifizierten Code zugreifen.

---

## Definition der Tiers

| Tier | Status | Anforderungen |
| :--- | :--- | :--- |
| **Gold** | `production_status = "gold"` | Volle Testabdeckung, Pydantic-Validierung, optimierte DB-Queries, Dokumentation vorhanden. |
| **Silber** | `production_status = "silver"` | Logik ist stabil & integer, Typ-Hints vorhanden, Refactoring (Clean Code) steht noch aus. |
| **Bronze** | `production_status = "bronze"` | MVP-Code. Funktioniert, ist aber "unsauber", ungetestet oder schwer wartbar. |
| **Broken** | `production_status = "broken"` | Unbrauchbarer Code. Architektonisch oder logisch falsch/unbenutzt. |
| **Unchecked** | `Default / Missing` | Alles, was noch nicht evaluiert wurde. |

---

## Technische Umsetzung

### 1. Datei-Markierung (Metadata)
Jede Python-Datei im Projekt erhält im Header ein Metadatum.
```python
# my_module.py
__production_status__ = "bronze"  # Optionen: gold, silver, bronze, unchecked
```

### 2. Automatisierter Check (Pytest-Integration)
Ein zentraler Test prüft alle Importe innerhalb des neuen Scopes (`src/systems/dnd5e/` oder similar).

**Vorgeschlagener Test-Code:**
```python
import pkgutil
import importlib
import pytest
import backend.src as my_project_root

def test_production_code_purity():
    """
    Stellt sicher, dass Code im neuen Scope nur auf 'silver' oder 'gold' zugreift.
    """
    allowed_statuses = ["silver", "gold"]
    new_scope_prefix = "backend.src.systems.dnd5e"
    
    for loader, module_name, is_pkg in pkgutil.walk_packages(my_project_root.__path__, my_project_root.__name__ + "."):
        if module_name.startswith(new_scope_prefix):
            module = importlib.import_module(module_name)
            status = getattr(module, "__production_status__", "unchecked")
            
            if status not in allowed_statuses:
                pytest.fail(f"Quality Violation: Module '{module_name}' has status '{status}'. "
                            f"Only 'silver' or 'gold' allowed in backend production scope.")
```

### 3. CI/CD Integration
* Der Test wird in die Pipeline aufgenommen.
* **Pre-Commit Hook:** Optionaler Hook, der Commits ablehnt, wenn im Ziel-Verzeichnis Dateien ohne `__production_status__` oder mit `bronze` erstellt werden.

---

## Akzeptanzkriterien
- [x] Definition der Tiers in der Dokumentation.
- [ ] Pytest-Lauf schlägt fehl, wenn ein Modul im neuen Scope keinen oder einen zu niedrigen Status hat.
- [ ] Alle neuen "V05" Dateien haben eine Markierung.
