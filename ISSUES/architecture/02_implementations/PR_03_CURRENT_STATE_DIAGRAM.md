# PR-3 Current State Diagram (Compendium Content Path)

This diagram captures the current backend structure for PR-3 scope:
- DND5E-02 content schema enforcement
- DND5E-04 query/projection behavior
- DND5E-03 integration touch (action payload contract round-trip)

```mermaid
flowchart LR
    %% Color legend:
    %% - Blue: previously implemented foundations (PR-1/PR-2 or pre-existing)
    %% - Green: PR-3 scope additions/validation focus

    subgraph API[Compendium API Layer]
        R1[router.py\ncreate/list/get definitions\nsearch, links, replacement-chain]
    end

    subgraph APP[Application Layer]
        S1[services.py\nCompendiumApplicationService]
        RS1[resolution.py\nLinkedEntryResolutionService]
    end

    subgraph DOMAIN[Domain Contracts]
        D1[definition_models.py\nDefinitionRecord + family models]
        D2[primitives.py\nActionOperationSpec/ModifierSpec]
        D3[pack_models.py\nContentPackRecord]
    end

    subgraph INFRA[Infrastructure]
        I1[repositories.py\ndefinitions/packs/links]
        I2[search_index_repository.py\ndeterministic search + revision]
        I3[orm.py\nDB constraints and tables]
    end

    subgraph TESTS[Test Coverage]
        T1[test_definition_models.py\ncontent/schema validation]
        T2[test_api_transport.py\nHTTP transport round-trip]
        T3[test_compendium_v05_e2e.py\nend-to-end lifecycle]
    end

    R1 --> S1
    R1 --> RS1
    S1 --> I1
    S1 --> I2
    S1 --> D1
    RS1 --> I1
    I1 --> I3
    I2 --> I3
    D1 --> D2
    D1 --> D3

    T1 --> D1
    T2 --> R1
    T3 --> S1

    %% Existing foundation components (blue)
    style R1 fill:#dbeafe,stroke:#1e3a8a,stroke-width:2px
    style S1 fill:#dbeafe,stroke:#1e3a8a,stroke-width:2px
    style RS1 fill:#dbeafe,stroke:#1e3a8a,stroke-width:2px
    style I1 fill:#dbeafe,stroke:#1e3a8a,stroke-width:2px
    style I2 fill:#dbeafe,stroke:#1e3a8a,stroke-width:2px
    style D2 fill:#dbeafe,stroke:#1e3a8a,stroke-width:2px
    style D3 fill:#dbeafe,stroke:#1e3a8a,stroke-width:2px
    style T3 fill:#dbeafe,stroke:#1e3a8a,stroke-width:2px

    %% PR-3 focused additions and assertions (green)
    style D1 fill:#dcfce7,stroke:#166534,stroke-width:2px
    style I3 fill:#dcfce7,stroke:#166534,stroke-width:2px
    style T1 fill:#dcfce7,stroke:#166534,stroke-width:2px
    style T2 fill:#dcfce7,stroke:#166534,stroke-width:2px
```
