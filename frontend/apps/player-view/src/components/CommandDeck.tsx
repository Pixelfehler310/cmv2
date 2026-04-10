import React, { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { CharacterCommandEnvelope, IHostBridge, apiClient } from "@rpg/bridge";
import { useCharacterSheet, useCreateCharacter, useMyCharacter, useUpdateCharacter } from "../hooks/useMyCharacter";
import { Sword, Backpack, Scroll, User, Book, Shield, Zap, LayoutGrid, PanelTop } from "lucide-react";
import { clsx } from "clsx";
import { Character } from "../types";

type LayoutMode = "dock" | "sheet";
type EditorMode = "view" | "create" | "edit";
type PrimaryTab = "actions" | "inventory" | "spells" | "attributes" | "lore";

type DefinitionOption = {
  id: string;
  name?: string;
};

type CharacterFormState = {
  name: string;
  player_name: string;
  status: string;
  species_id: string;
  class_id: string;
  background_id: string;
  level: number;
  xp: number;
  alignment: string;
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
  max_hp: number;
  current_hp: number;
  temp_hp: number;
  hit_dice: string;
  armor_class: number;
  speed: number;
  initiative: number;
};

const DEFAULT_FORM_STATE: CharacterFormState = {
  name: "",
  player_name: "",
  status: "active",
  species_id: "",
  class_id: "",
  background_id: "",
  level: 1,
  xp: 0,
  alignment: "neutral",
  strength: 10,
  dexterity: 10,
  constitution: 10,
  intelligence: 10,
  wisdom: 10,
  charisma: 10,
  max_hp: 12,
  current_hp: 12,
  temp_hp: 0,
  hit_dice: "1d10",
  armor_class: 10,
  speed: 30,
  initiative: 0,
};

const mapCharacterToForm = (character: Character): CharacterFormState => ({
  name: character.name,
  player_name: character.player_name ?? "",
  status: "active",
  species_id: character.species_id,
  class_id: character.class_id,
  background_id: character.background_id ?? "",
  level: character.level,
  xp: character.xp,
  alignment: character.alignment ?? "",
  strength: character.strength,
  dexterity: character.dexterity,
  constitution: character.constitution,
  intelligence: character.intelligence,
  wisdom: character.wisdom,
  charisma: character.charisma,
  max_hp: character.max_hp,
  current_hp: character.current_hp,
  temp_hp: character.temp_hp,
  hit_dice: character.hit_dice,
  armor_class: character.armor_class,
  speed: character.speed,
  initiative: character.initiative,
});

const buildCharacterPayload = (
  form: CharacterFormState,
  options: {
    playerId: string;
    campaignId: string;
    fallbackCollections?: {
      inventory?: unknown[];
      spells?: unknown[];
      spell_slots?: Record<string, number>;
      actions?: unknown[];
      effects?: unknown[];
      ability_ids?: string[];
    };
  },
) => {
  const { playerId, campaignId, fallbackCollections } = options;
  return {
    name: form.name,
    player_name: form.player_name || null,
    player_id: playerId,
    status: form.status,
    campaign_id: campaignId,
    species_id: form.species_id,
    class_id: form.class_id,
    background_id: form.background_id || null,
    ability_ids: fallbackCollections?.ability_ids ?? [],
    level: form.level,
    xp: form.xp,
    alignment: form.alignment || null,
    strength: form.strength,
    dexterity: form.dexterity,
    constitution: form.constitution,
    intelligence: form.intelligence,
    wisdom: form.wisdom,
    charisma: form.charisma,
    max_hp: form.max_hp,
    current_hp: form.current_hp,
    temp_hp: form.temp_hp,
    hit_dice: form.hit_dice,
    armor_class: form.armor_class,
    speed: form.speed,
    initiative: form.initiative,
    inventory: fallbackCollections?.inventory ?? [],
    spells: fallbackCollections?.spells ?? [],
    spell_slots: fallbackCollections?.spell_slots ?? {},
    actions: fallbackCollections?.actions ?? [],
    effects: fallbackCollections?.effects ?? [],
  };
};

interface CommandDeckProps {
  bridge: IHostBridge;
  campaignId?: string;
}

export const CommandDeck: React.FC<CommandDeckProps> = ({ bridge, campaignId }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [layoutMode, setLayoutMode] = useState<LayoutMode>("dock");
  const [editorMode, setEditorMode] = useState<EditorMode>("view");
  const [activeTab, setActiveTab] = useState<PrimaryTab>("actions");
  const [formState, setFormState] = useState<CharacterFormState>(DEFAULT_FORM_STATE);
  const [catalogRevision, setCatalogRevision] = useState(1);
  const [commandError, setCommandError] = useState<string | null>(null);
  const [commandMessage, setCommandMessage] = useState<string | null>(null);

  const activeCampaignId = campaignId || "campaign-1";
  const { data: character, isLoading, error } = useMyCharacter(bridge, activeCampaignId);
  const createCharacter = useCreateCharacter(activeCampaignId);
  const updateCharacter = useUpdateCharacter(activeCampaignId);
  const { data: sheetEnvelope, isFetching: sheetLoading, refetch: refetchSheet } = useCharacterSheet(character?.id ?? null, catalogRevision);

  const { data: currentUser } = useQuery({
    queryKey: ["command-deck-current-user"],
    queryFn: () => bridge.auth.getUser(),
  });

  const { data: speciesOptions = [] } = useQuery({
    queryKey: ["character-species-options"],
    queryFn: async () => (await apiClient.definitions.species()) as DefinitionOption[],
  });

  const { data: classOptions = [] } = useQuery({
    queryKey: ["character-class-options"],
    queryFn: async () => (await apiClient.definitions.classes()) as DefinitionOption[],
  });

  const { data: backgroundOptions = [] } = useQuery({
    queryKey: ["character-background-options"],
    queryFn: async () => (await apiClient.definitions.backgrounds()) as DefinitionOption[],
  });

  useEffect(() => {
    if (!character) {
      return;
    }
    if (editorMode === "view") {
      setFormState(mapCharacterToForm(character));
    }
  }, [character, editorMode]);

  useEffect(() => {
    if (formState.species_id || speciesOptions.length === 0) {
      return;
    }
    setFormState((prev) => ({ ...prev, species_id: speciesOptions[0].id }));
  }, [speciesOptions, formState.species_id]);

  useEffect(() => {
    if (formState.class_id || classOptions.length === 0) {
      return;
    }
    setFormState((prev) => ({ ...prev, class_id: classOptions[0].id }));
  }, [classOptions, formState.class_id]);

  const isSheetMode = layoutMode === "sheet";

  const submitCreate = async () => {
    setCommandError(null);
    setCommandMessage(null);
    if (!currentUser?.id) {
      setCommandError("Missing authenticated user context.");
      return;
    }

    try {
      await createCharacter.mutateAsync(
        buildCharacterPayload(formState, {
          playerId: currentUser.id,
          campaignId: activeCampaignId,
        }),
      );
      setEditorMode("view");
      setCommandMessage("Character created.");
    } catch (mutationError) {
      setCommandError(mutationError instanceof Error ? mutationError.message : "Create failed.");
    }
  };

  const submitUpdate = async () => {
    setCommandError(null);
    setCommandMessage(null);
    if (!currentUser?.id || !character?.id) {
      setCommandError("Cannot update character without user and character context.");
      return;
    }

    try {
      await updateCharacter.mutateAsync({
        characterId: character.id,
        payload: buildCharacterPayload(formState, {
          playerId: currentUser.id,
          campaignId: activeCampaignId,
          fallbackCollections: {
            inventory: character.inventory,
            spells: character.spells,
            spell_slots: character.spell_slots,
            actions: character.actions,
            effects: character.effects,
            ability_ids: [],
          },
        }),
      });
      setEditorMode("view");
      setCommandMessage("Character updated.");
    } catch (mutationError) {
      setCommandError(mutationError instanceof Error ? mutationError.message : "Update failed.");
    }
  };

  if (isLoading) {
    return <div className="p-4 text-muted">Loading character...</div>;
  }

  if (error) {
    return <div className="p-4 text-gaming-500">Error loading character</div>;
  }

  if (!character || editorMode === "create") {
    return (
      <CharacterFormPanel
        title={character ? "Create Another Character" : "Create Character"}
        subtitle="Production character flow now uses the CM-07 write endpoint."
        formState={formState}
        speciesOptions={speciesOptions}
        classOptions={classOptions}
        backgroundOptions={backgroundOptions}
        onChange={setFormState}
        onSubmit={submitCreate}
        onCancel={character ? () => setEditorMode("view") : undefined}
        submitLabel="Create Character"
        submitting={createCharacter.isPending}
        error={commandError}
      />
    );
  }

  const hpPercent = Math.min(100, Math.max(0, (character.current_hp / character.max_hp) * 100));

  const toggleLayout = () => {
    setLayoutMode((prev) => (prev === "dock" ? "sheet" : "dock"));
  };

  const renderSheetState = () => {
    if (!sheetEnvelope) {
      return <p className="text-muted text-sm">Sheet has not been loaded yet.</p>;
    }
    return <SheetStatePanel envelope={sheetEnvelope} onReload={() => void refetchSheet()} />;
  };

  return (
    <div ref={containerRef} className={clsx("w-full h-full bg-surface text-primary overflow-hidden transition-all", isSheetMode ? "flex flex-col" : "flex flex-row border-t border-default")}>
      {/* Layout Toggle Button */}
      <button
        onClick={toggleLayout}
        className="btn btn-ghost btn-sm absolute z-10 transition-all top-2 right-2"
        data-tooltip={isSheetMode ? "Switch to Dock Mode" : "Switch to Sheet Mode"}
        aria-label={isSheetMode ? "Switch to Dock Mode" : "Switch to Sheet Mode"}
      >
        {isSheetMode ? <LayoutGrid size={18} /> : <PanelTop size={18} />}
      </button>

      {/* Vitals Section */}
      <div className={clsx("bg-muted shrink-0 transition-all", isSheetMode ? "w-full p-4 border-b border-default" : "w-64 p-4 flex flex-col gap-4 border-r border-default")}>
        <div className="flex flex-wrap gap-2">
          <button className="btn btn-sm btn-primary" onClick={() => setEditorMode("edit")}>
            Edit
          </button>
          <button className="btn btn-sm btn-secondary" onClick={() => setEditorMode("create")}>
            New
          </button>
          <button className="btn btn-sm" onClick={() => void refetchSheet()} disabled={sheetLoading}>
            Refresh Sheet
          </button>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-label-s text-secondary" htmlFor="catalog-revision-input">
            Catalog Rev
          </label>
          <input
            id="catalog-revision-input"
            type="number"
            min={0}
            className="input input-sm w-24"
            value={catalogRevision}
            onChange={(event) => setCatalogRevision(Math.max(0, Number(event.target.value) || 0))}
          />
        </div>

        {commandMessage && <p className="text-xs text-success">{commandMessage}</p>}
        {commandError && <p className="text-xs text-gaming-500">{commandError}</p>}

        <div className={clsx("flex gap-3", isSheetMode ? "items-center justify-between" : "items-center")}>
          {/* Profile */}
          <div className="flex items-center gap-3">
            <div className="avatar avatar-lg gradient-vtt flex items-center justify-center shrink-0">
              <User className="w-6 h-6 text-white" />
            </div>
            <div className="min-w-0">
              <h2 className="font-bold text-lg truncate">{character.name}</h2>
              <div className="text-label-s text-secondary">
                Level {character.level} {character.class_id}
              </div>
            </div>
          </div>

          {/* Stats Row (Sheet mode: inline with profile) */}
          {isSheetMode && (
            <div className="flex gap-4 items-center">
              <StatBox icon={Shield} label="AC" value={character.armor_class} />
              <StatBox icon={Zap} label="Init" value={character.initiative >= 0 ? `+${character.initiative}` : character.initiative} iconClassName="text-spark-500" />
              <HPBar current={character.current_hp} max={character.max_hp} percent={hpPercent} compact />
            </div>
          )}
        </div>

        {/* HP & Stats (Dock mode: vertical layout) */}
        {!isSheetMode && (
          <>
            <HPBar current={character.current_hp} max={character.max_hp} percent={hpPercent} />
            <div className="grid grid-cols-2 gap-2 text-center">
              <StatBox icon={Shield} label="AC" value={character.armor_class} />
              <StatBox icon={Zap} label="Init" value={character.initiative >= 0 ? `+${character.initiative}` : character.initiative} iconClassName="text-spark-500" />
            </div>
          </>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 min-h-0 relative">
        {editorMode === "edit" && (
          <div className="border-b border-default">
            <CharacterFormPanel
              title="Edit Character"
              subtitle="Updates are sent through the CM-07 update endpoint."
              formState={formState}
              speciesOptions={speciesOptions}
              classOptions={classOptions}
              backgroundOptions={backgroundOptions}
              onChange={setFormState}
              onSubmit={submitUpdate}
              onCancel={() => setEditorMode("view")}
              submitLabel="Save Changes"
              submitting={updateCharacter.isPending}
              compact
              error={commandError}
            />
          </div>
        )}

        {/* Tabs Header */}
        <div className={clsx("flex border-b border-default bg-muted/50", isSheetMode && "justify-center")}>
          <TabButton active={activeTab === "actions"} onClick={() => setActiveTab("actions")} icon={<Sword size={16} />} label="Actions" compact={isSheetMode} />
          <TabButton active={activeTab === "inventory"} onClick={() => setActiveTab("inventory")} icon={<Backpack size={16} />} label="Inventory" compact={isSheetMode} />
          <TabButton active={activeTab === "spells"} onClick={() => setActiveTab("spells")} icon={<Scroll size={16} />} label="Spells" compact={isSheetMode} />
          <TabButton active={activeTab === "attributes"} onClick={() => setActiveTab("attributes")} icon={<User size={16} />} label="Attributes" compact={isSheetMode} />
          <TabButton active={activeTab === "lore"} onClick={() => setActiveTab("lore")} icon={<Book size={16} />} label="Lore" compact={isSheetMode} />
        </div>

        {/* Tab Content */}
        <div className={clsx("flex-1 p-4 overflow-y-auto bg-surface/50", isSheetMode && "pb-8")}>
          <div className="mb-4 rounded-lg border border-default bg-muted/40 p-3">
            <h4 className="text-sm font-semibold mb-2">Sheet Projection</h4>
            {renderSheetState()}
          </div>

          {activeTab === "actions" && <ActionsTab character={character} isSheetMode={isSheetMode} />}
          {activeTab === "inventory" && <InventoryTab character={character} isSheetMode={isSheetMode} />}
          {activeTab === "spells" && <SpellsTab character={character} isSheetMode={isSheetMode} />}
          {activeTab === "attributes" && <AttributesTab character={character} isSheetMode={isSheetMode} />}
          {activeTab === "lore" && <LoreTab character={character} isSheetMode={isSheetMode} />}
        </div>
      </div>
    </div>
  );
};

type CharacterFormPanelProps = {
  title: string;
  subtitle: string;
  formState: CharacterFormState;
  speciesOptions: DefinitionOption[];
  classOptions: DefinitionOption[];
  backgroundOptions: DefinitionOption[];
  onChange: React.Dispatch<React.SetStateAction<CharacterFormState>>;
  onSubmit: () => void;
  onCancel?: () => void;
  submitLabel: string;
  submitting: boolean;
  compact?: boolean;
  error?: string | null;
};

const CharacterFormPanel: React.FC<CharacterFormPanelProps> = ({
  title,
  subtitle,
  formState,
  speciesOptions,
  classOptions,
  backgroundOptions,
  onChange,
  onSubmit,
  onCancel,
  submitLabel,
  submitting,
  compact,
  error,
}) => {
  const updateTextField = (key: keyof CharacterFormState, value: string) => {
    onChange((prev) => ({ ...prev, [key]: value }));
  };

  const updateNumberField = (key: keyof CharacterFormState, value: string) => {
    onChange((prev) => ({ ...prev, [key]: Number(value) || 0 }));
  };

  return (
    <section className={clsx("bg-surface border border-default rounded-xl", compact ? "p-3" : "p-4")}>
      <h3 className="text-sm font-semibold">{title}</h3>
      <p className="text-xs text-secondary mb-3">{subtitle}</p>

      <div className={clsx("grid gap-3", compact ? "grid-cols-2" : "grid-cols-1 md:grid-cols-3")}>
        <label className="form-control">
          <span className="text-label-s text-secondary">Name</span>
          <input className="input input-sm" value={formState.name} onChange={(event) => updateTextField("name", event.target.value)} />
        </label>

        <label className="form-control">
          <span className="text-label-s text-secondary">Player Name</span>
          <input className="input input-sm" value={formState.player_name} onChange={(event) => updateTextField("player_name", event.target.value)} />
        </label>

        <label className="form-control">
          <span className="text-label-s text-secondary">Level</span>
          <input className="input input-sm" type="number" min={1} value={formState.level} onChange={(event) => updateNumberField("level", event.target.value)} />
        </label>

        <label className="form-control">
          <span className="text-label-s text-secondary">Species</span>
          <select className="select select-sm" value={formState.species_id} onChange={(event) => updateTextField("species_id", event.target.value)}>
            <option value="">Select species</option>
            {speciesOptions.map((entry) => (
              <option key={entry.id} value={entry.id}>
                {entry.name ?? entry.id}
              </option>
            ))}
          </select>
        </label>

        <label className="form-control">
          <span className="text-label-s text-secondary">Class</span>
          <select className="select select-sm" value={formState.class_id} onChange={(event) => updateTextField("class_id", event.target.value)}>
            <option value="">Select class</option>
            {classOptions.map((entry) => (
              <option key={entry.id} value={entry.id}>
                {entry.name ?? entry.id}
              </option>
            ))}
          </select>
        </label>

        <label className="form-control">
          <span className="text-label-s text-secondary">Background</span>
          <select className="select select-sm" value={formState.background_id} onChange={(event) => updateTextField("background_id", event.target.value)}>
            <option value="">No background</option>
            {backgroundOptions.map((entry) => (
              <option key={entry.id} value={entry.id}>
                {entry.name ?? entry.id}
              </option>
            ))}
          </select>
        </label>

        <label className="form-control">
          <span className="text-label-s text-secondary">Max HP</span>
          <input className="input input-sm" type="number" min={1} value={formState.max_hp} onChange={(event) => updateNumberField("max_hp", event.target.value)} />
        </label>

        <label className="form-control">
          <span className="text-label-s text-secondary">Current HP</span>
          <input className="input input-sm" type="number" min={0} value={formState.current_hp} onChange={(event) => updateNumberField("current_hp", event.target.value)} />
        </label>

        <label className="form-control">
          <span className="text-label-s text-secondary">Armor Class</span>
          <input className="input input-sm" type="number" min={0} value={formState.armor_class} onChange={(event) => updateNumberField("armor_class", event.target.value)} />
        </label>
      </div>

      <div className="mt-3 flex gap-2">
        <button className="btn btn-primary btn-sm" onClick={onSubmit} disabled={submitting}>
          {submitting ? "Saving..." : submitLabel}
        </button>
        {onCancel && (
          <button className="btn btn-ghost btn-sm" onClick={onCancel} disabled={submitting}>
            Cancel
          </button>
        )}
      </div>

      {error && <p className="text-xs text-gaming-500 mt-2">{error}</p>}
    </section>
  );
};

const SheetStatePanel: React.FC<{ envelope: CharacterCommandEnvelope<unknown>; onReload?: () => void }> = ({ envelope, onReload }) => {
  if (envelope.status === "resolved") {
    const payload = envelope.payload as Record<string, unknown>;
    return (
      <div className="text-xs text-secondary space-y-1">
        <p className="text-success">Resolved at catalog revision {String(envelope.catalog_revision ?? "n/a")}.</p>
        <p>Sheet revision: {String(payload.sheet_revision ?? "n/a")}</p>
      </div>
    );
  }

  if (envelope.status === "invalidated") {
    return (
      <div className="flex items-center justify-between gap-4 py-1">
        <p className="text-xs text-warning">Projection invalidated. Increase catalog revision and refresh sheet.</p>
        <button className="btn btn-xs btn-secondary" onClick={onReload}>
          Reload
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between gap-4 py-1">
      <p className="text-xs text-gaming-500 font-medium">Projection denied: {envelope.reason_code ?? "UNKNOWN_REASON"}</p>
      {onReload && (
        <button className="btn btn-xs btn-ghost" onClick={onReload}>
          Retry
        </button>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────────────────

interface StatBoxProps {
  icon: React.FC<{ className?: string }>;
  label: string;
  value: string | number;
  iconClassName?: string;
}

const StatBox: React.FC<StatBoxProps> = ({ icon: Icon, label, value, iconClassName }) => (
  <div className="card card-flat p-2 text-center min-w-[60px]">
    <div className="text-label-s text-muted uppercase">{label}</div>
    <div className="font-bold text-xl flex items-center justify-center gap-1">
      <Icon className={clsx("w-4 h-4", iconClassName || "text-secondary")} />
      {value}
    </div>
  </div>
);

interface HPBarProps {
  current: number;
  max: number;
  percent: number;
  compact?: boolean;
}

const HPBar: React.FC<HPBarProps> = ({ current, max, percent, compact }) => (
  <div className={clsx("space-y-1", compact && "min-w-[120px]")}>
    <div className="flex justify-between text-label-s font-mono text-secondary">
      <span>HP</span>
      <span>
        {current} / {max}
      </span>
    </div>
    <div className="h-3 bg-muted rounded-full overflow-hidden border border-default">
      <div className="h-full bg-gaming-500 transition-all duration-500 ease-out" style={{ width: `${percent}%` }} />
    </div>
  </div>
);

// Tab Button Component

interface TabButtonProps {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
  compact?: boolean;
}

const TabButton: React.FC<TabButtonProps> = ({ active, onClick, icon, label, compact }) => (
  <button
    onClick={onClick}
    className={clsx(
      "flex items-center gap-2 text-sm font-medium transition-all border-r border-default",
      compact ? "px-4 py-2" : "px-6 py-3",
      active ? "bg-vtt-900/30 text-vtt-300 border-b-2 border-b-vtt-500" : "text-secondary hover:bg-muted hover:text-primary",
    )}
  >
    {icon}
    {!compact && label}
  </button>
);

interface TabContentProps {
  character: any;
  isSheetMode?: boolean;
}

const ActionsTab: React.FC<TabContentProps> = ({ character, isSheetMode }) => (
  <div className={clsx("grid gap-3", isSheetMode ? "grid-cols-2 sm:grid-cols-3 md:grid-cols-4" : "grid-cols-2 md:grid-cols-4 lg:grid-cols-6")}>
    {/* Default Actions */}
    <ActionButton name="Attack" type="physical" />
    <ActionButton name="Dash" type="utility" />
    <ActionButton name="Disengage" type="utility" />
    <ActionButton name="Dodge" type="utility" />

    {/* Character Specific Actions */}
    {character.actions?.map((action: any, i: number) => (
      <ActionButton key={i} name={action.name} type="class" />
    ))}
  </div>
);

const ActionButton = ({ name, type }: { name: string; type: "physical" | "utility" | "class" }) => {
  const colors = {
    physical: "bg-gaming-900/20 border-gaming-800 hover:bg-gaming-900/40 text-gaming-300",
    utility: "card card-flat hover:bg-muted text-secondary",
    class: "bg-vtt-900/20 border-vtt-800 hover:bg-vtt-900/40 text-vtt-300",
  };

  return (
    <button className={clsx("p-3 rounded-xl border text-left transition-all hover-lift flex flex-col gap-1", colors[type])}>
      <span className="font-bold text-sm">{name}</span>
      <span className="text-label-s opacity-70 uppercase tracking-wider">{type}</span>
    </button>
  );
};

const InventoryTab: React.FC<TabContentProps> = ({ character, isSheetMode }) => (
  <div className={clsx("space-y-2", isSheetMode && "max-w-2xl mx-auto")}>
    {character.inventory?.length === 0 && <div className="text-muted italic">Inventory is empty.</div>}
    {character.inventory?.map((item: any, i: number) => (
      <div key={i} className="card card-flat flex items-center justify-between p-3">
        <span>{item.name}</span>
        <span className="badge badge-neutral">Qty: {item.quantity || 1}</span>
      </div>
    ))}
  </div>
);

const SpellsTab: React.FC<TabContentProps> = ({ character, isSheetMode }) => (
  <div className={clsx("grid gap-4", isSheetMode ? "grid-cols-1" : "grid-cols-1 md:grid-cols-2")}>
    {/* Group by level logic would go here */}
    <div className="space-y-2">
      <h3 className="text-label-s font-bold uppercase text-muted mb-2">Cantrips</h3>
      {character.spells
        ?.filter((s: any) => s.level === 0)
        .map((spell: any, i: number) => (
          <div key={i} className="card card-flat p-3 text-sm">
            {spell.name}
          </div>
        ))}
      {(!character.spells || character.spells.length === 0) && <div className="text-muted italic">No spells known.</div>}
    </div>
  </div>
);

const AttributesTab: React.FC<TabContentProps> = ({ character, isSheetMode }) => {
  const attrs = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"];
  return (
    <div className={clsx("grid gap-4", isSheetMode ? "grid-cols-2 sm:grid-cols-3 max-w-xl mx-auto" : "grid-cols-3 md:grid-cols-6")}>
      {attrs.map((attr) => {
        const val = character[attr];
        const mod = Math.floor((val - 10) / 2);
        return (
          <div key={attr} className="card card-flat p-4 text-center hover-lift">
            <div className="text-label-s uppercase text-muted mb-1">{attr.substring(0, 3)}</div>
            <div className="text-2xl font-bold">{mod >= 0 ? `+${mod}` : mod}</div>
            <div className="text-label-s text-secondary font-mono">{val}</div>
          </div>
        );
      })}
    </div>
  );
};

const LoreTab: React.FC<TabContentProps> = ({ character, isSheetMode }) => (
  <div className={clsx("prose prose-invert prose-sm", isSheetMode ? "max-w-2xl mx-auto" : "max-w-none")}>
    <h3 className="text-vtt-400">Background</h3>
    <p className="text-secondary">{character.background_id ? `Character has the ${character.background_id} background.` : "No background details available."}</p>
    {/* Future: Render full markdown lore here */}
  </div>
);
