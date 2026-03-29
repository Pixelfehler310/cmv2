__production_status__ = "gold"
from enum import Enum
from typing import Optional
from pydantic import BaseModel

class RelationKind(str, Enum):
    INLINE_REF = "inline_ref"
    PREREQUISITE = "prerequisite"
    REPLACEMENT = "replacement"
    PARENT_CHILD = "parent_child"
    RELATED = "related"
    GRANTS = "grants"

class ResolveMode(str, Enum):
    STRICT = "strict"
    BEST_EFFORT = "best_effort"

class LinkedEntryReference(BaseModel):
    id: str
    source_definition_id: str
    source_path: str
    target_definition_id: str
    target_family: str
    relation_kind: RelationKind
    required: bool
    resolve_mode: ResolveMode

class ReplacementChain(BaseModel):
    head_definition_id: str
    next_definition_id: Optional[str] = None
    chain_depth: int
    terminal_definition_id: Optional[str] = None

    def validate_chain(self) -> None:
        pass

    def resolve_current_visible(self) -> str:
        return self.terminal_definition_id or self.head_definition_id
