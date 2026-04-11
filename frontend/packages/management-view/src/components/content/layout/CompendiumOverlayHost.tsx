import React from "react";
import { EntityDetailPanel } from "../EntityDetailPanel";
import { getEditorComponent } from "../config/editorRegistry";
import { FamilyTab } from "../config/familyConfig";
import { CreatePackDialog } from "../dialogs/CreatePackDialog";

interface CompendiumOverlayHostProps {
  activeFamily: FamilyTab;
  activePackId: string;
  selectedEntity: any | null;
  isAdding: boolean;
  editingEntity: any | null;
  isCreatePackDialogOpen: boolean;
  onCloseDetail: () => void;
  onCloseEditor: () => void;
  onCloseCreatePack: () => void;
  onCreatePackSuccess: (newPackId: string) => void;
}

export const CompendiumOverlayHost: React.FC<CompendiumOverlayHostProps> = ({
  activeFamily,
  activePackId,
  selectedEntity,
  isAdding,
  editingEntity,
  isCreatePackDialogOpen,
  onCloseDetail,
  onCloseEditor,
  onCloseCreatePack,
  onCreatePackSuccess,
}) => {
  return (
    <>
      <EntityDetailPanel entity={selectedEntity} isOpen={!!selectedEntity} onClose={onCloseDetail} />

      {(isAdding || editingEntity) && (
        <div className="fixed inset-0 z-50 flex items-center justify-end">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onCloseEditor} />
          <div className="relative h-full w-full max-w-4xl bg-background border-l border-border shadow-2xl animate-in slide-in-from-right-full">
            {getEditorComponent(activeFamily, {
              initialData: editingEntity,
              packId: activePackId,
              onSave: onCloseEditor,
              onCancel: onCloseEditor,
            })}
          </div>
        </div>
      )}

      <CreatePackDialog isOpen={isCreatePackDialogOpen} onClose={onCloseCreatePack} onSuccess={onCreatePackSuccess} />
    </>
  );
};
