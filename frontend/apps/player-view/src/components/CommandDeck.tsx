import React, { useState } from 'react';
import { useMyCharacter } from '../hooks/useMyCharacter';
import { Sword, Backpack, Scroll, User, Book, Shield, Heart, Zap } from 'lucide-react';
import { clsx } from 'clsx';

import { IHostBridge } from '@rpg/bridge';

interface CommandDeckProps {
  bridge: IHostBridge;
  campaignId?: string;
}

export const CommandDeck: React.FC<CommandDeckProps> = ({ bridge, campaignId }) => {
  // Hardcode campaignId for now if not provided, or get from context
  const activeCampaignId = campaignId || 'campaign-1'; 
  const { data: character, isLoading, error } = useMyCharacter(bridge, activeCampaignId);
  const [activeTab, setActiveTab] = useState<'actions' | 'inventory' | 'spells' | 'attributes' | 'lore'>('actions');

  if (isLoading) return <div className="p-4 text-slate-400">Loading character...</div>;
  if (error) return <div className="p-4 text-red-400">Error loading character</div>;
  if (!character) return <div className="p-4 text-slate-400">No character found for this campaign.</div>;

  const hpPercent = Math.min(100, Math.max(0, (character.current_hp / character.max_hp) * 100));

  return (
    <div className="w-full h-full bg-slate-900 text-slate-100 flex overflow-hidden border-t border-slate-700">
      {/* Sidebar: Vitals */}
      <div className="w-64 bg-slate-950 p-4 flex flex-col gap-4 border-r border-slate-800 shrink-0">
        <div className="flex items-center gap-3">
            <div className="w-16 h-16 bg-slate-800 rounded-full border-2 border-amber-600/50 flex items-center justify-center shrink-0">
                <User className="w-8 h-8 text-slate-500" />
            </div>
            <div className="min-w-0">
                <h2 className="font-bold text-lg truncate text-amber-50">{character.name}</h2>
                <div className="text-xs text-slate-400">Level {character.level} {character.class_id}</div>
            </div>
        </div>

        <div className="space-y-1">
            <div className="flex justify-between text-xs font-mono text-slate-400">
                <span>HP</span>
                <span>{character.current_hp} / {character.max_hp}</span>
            </div>
            <div className="h-3 bg-slate-800 rounded-full overflow-hidden border border-slate-700">
                <div 
                    className="h-full bg-red-600 transition-all duration-500 ease-out" 
                    style={{ width: `${hpPercent}%` }}
                />
            </div>
        </div>

        <div className="grid grid-cols-2 gap-2 text-center">
            <div className="bg-slate-900 p-2 rounded border border-slate-800">
                <div className="text-xs text-slate-500 uppercase">AC</div>
                <div className="font-bold text-xl flex items-center justify-center gap-1">
                    <Shield className="w-4 h-4 text-slate-600" />
                    {character.armor_class}
                </div>
            </div>
            <div className="bg-slate-900 p-2 rounded border border-slate-800">
                <div className="text-xs text-slate-500 uppercase">Init</div>
                <div className="font-bold text-xl flex items-center justify-center gap-1">
                    <Zap className="w-4 h-4 text-amber-600" />
                    {character.initiative >= 0 ? `+${character.initiative}` : character.initiative}
                </div>
            </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Tabs Header */}
        <div className="flex border-b border-slate-800 bg-slate-950/50">
            <TabButton active={activeTab === 'actions'} onClick={() => setActiveTab('actions')} icon={<Sword size={16} />} label="Actions" />
            <TabButton active={activeTab === 'inventory'} onClick={() => setActiveTab('inventory')} icon={<Backpack size={16} />} label="Inventory" />
            <TabButton active={activeTab === 'spells'} onClick={() => setActiveTab('spells')} icon={<Scroll size={16} />} label="Spells" />
            <TabButton active={activeTab === 'attributes'} onClick={() => setActiveTab('attributes')} icon={<User size={16} />} label="Attributes" />
            <TabButton active={activeTab === 'lore'} onClick={() => setActiveTab('lore')} icon={<Book size={16} />} label="Lore" />
        </div>

        {/* Tab Content */}
        <div className="flex-1 p-4 overflow-y-auto bg-slate-900/50">
            {activeTab === 'actions' && <ActionsTab character={character} />}
            {activeTab === 'inventory' && <InventoryTab character={character} />}
            {activeTab === 'spells' && <SpellsTab character={character} />}
            {activeTab === 'attributes' && <AttributesTab character={character} />}
            {activeTab === 'lore' && <LoreTab character={character} />}
        </div>
      </div>
    </div>
  );
};

// Sub-components

const TabButton = ({ active, onClick, icon, label }: any) => (
    <button 
        onClick={onClick}
        className={clsx(
            "flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors border-r border-slate-800",
            active ? "bg-slate-800 text-amber-400 border-b-2 border-b-amber-500" : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
        )}
    >
        {icon}
        {label}
    </button>
);

const ActionsTab = ({ character }: { character: any }) => (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
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

const ActionButton = ({ name, type }: { name: string, type: 'physical' | 'utility' | 'class' }) => {
    const colors = {
        physical: 'bg-red-900/20 border-red-800 hover:bg-red-900/40 text-red-200',
        utility: 'bg-slate-800 border-slate-700 hover:bg-slate-700 text-slate-300',
        class: 'bg-amber-900/20 border-amber-800 hover:bg-amber-900/40 text-amber-200'
    };
    
    return (
        <button className={clsx("p-3 rounded border text-left transition-colors flex flex-col gap-1", colors[type])}>
            <span className="font-bold text-sm">{name}</span>
            <span className="text-[10px] opacity-70 uppercase tracking-wider">{type}</span>
        </button>
    );
};

const InventoryTab = ({ character }: { character: any }) => (
    <div className="space-y-2">
        {character.inventory?.length === 0 && <div className="text-slate-500 italic">Inventory is empty.</div>}
        {character.inventory?.map((item: any, i: number) => (
            <div key={i} className="flex items-center justify-between p-2 bg-slate-800/50 rounded border border-slate-800">
                <span>{item.name}</span>
                <span className="text-xs text-slate-500">Qty: {item.quantity || 1}</span>
            </div>
        ))}
    </div>
);

const SpellsTab = ({ character }: { character: any }) => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Group by level logic would go here */}
        <div className="space-y-2">
            <h3 className="text-xs font-bold uppercase text-slate-500 mb-2">Cantrips</h3>
            {character.spells?.filter((s: any) => s.level === 0).map((spell: any, i: number) => (
                <div key={i} className="p-2 bg-slate-800/30 rounded border border-slate-800 text-sm">{spell.name}</div>
            ))}
            {(!character.spells || character.spells.length === 0) && <div className="text-slate-500 italic">No spells known.</div>}
        </div>
    </div>
);

const AttributesTab = ({ character }: { character: any }) => {
    const attrs = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'];
    return (
        <div className="grid grid-cols-3 md:grid-cols-6 gap-4">
            {attrs.map(attr => {
                const val = character[attr];
                const mod = Math.floor((val - 10) / 2);
                return (
                    <div key={attr} className="bg-slate-800/50 p-3 rounded border border-slate-800 text-center">
                        <div className="text-[10px] uppercase text-slate-500 mb-1">{attr.substring(0, 3)}</div>
                        <div className="text-2xl font-bold">{mod >= 0 ? `+${mod}` : mod}</div>
                        <div className="text-xs text-slate-600 font-mono">{val}</div>
                    </div>
                );
            })}
        </div>
    );
};

const LoreTab = ({ character }: { character: any }) => (
    <div className="prose prose-invert prose-sm max-w-none">
        <h3 className="text-amber-500">Background</h3>
        <p className="text-slate-300">
            {character.background_id ? `Character has the ${character.background_id} background.` : 'No background details available.'}
        </p>
        {/* Future: Render full markdown lore here */}
    </div>
);
