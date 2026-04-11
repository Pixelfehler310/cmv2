import React from "react";
import { BookOpen, Flag, Globe2, GraduationCap, Link2, MapPinned, Package, ScrollText, Shield, Sword, Users } from "lucide-react";
import { FamilyTab } from "../config/familyConfig";

interface CompendiumFamilyTabsProps {
  activeFamily: FamilyTab;
  onSelectFamily: (family: FamilyTab) => void;
}

const TAB_ITEMS: Array<{ family: FamilyTab; label: string; icon: React.ReactNode }> = [
  { family: "monster", label: "Bestiary", icon: <Sword size={16} /> },
  { family: "spell", label: "Spells", icon: <BookOpen size={16} /> },
  { family: "item", label: "Items", icon: <Package size={16} /> },
  { family: "species", label: "Species", icon: <Users size={16} /> },
  { family: "class", label: "Classes", icon: <Shield size={16} /> },
  { family: "background", label: "Backgrounds", icon: <GraduationCap size={16} /> },
  { family: "lore", label: "Lore", icon: <ScrollText size={16} /> },
  { family: "condition", label: "Conditions", icon: <Link2 size={16} /> },
  { family: "faction", label: "Factions", icon: <Flag size={16} /> },
  { family: "region", label: "Regions", icon: <Globe2 size={16} /> },
  { family: "place", label: "Places", icon: <MapPinned size={16} /> },
];

export const CompendiumFamilyTabs: React.FC<CompendiumFamilyTabsProps> = ({ activeFamily, onSelectFamily }) => {
  return (
    <div className="flex gap-2 border-b border-border mb-6 overflow-x-auto pb-1 scrollbar-hide">
      {TAB_ITEMS.map((item) => (
        <TabButton
          key={item.family}
          active={activeFamily === item.family}
          onClick={() => onSelectFamily(item.family)}
          label={item.label}
          icon={item.icon}
        />
      ))}
    </div>
  );
};

const TabButton = ({ active, onClick, label, icon }: { active: boolean; onClick: () => void; label: string; icon: React.ReactNode }) => (
  <button
    onClick={onClick}
    className={`px-6 py-3 font-semibold text-sm rounded-t-lg transition-colors border-b-2 flex items-center gap-2 whitespace-nowrap ${
      active ? "border-primary text-primary bg-surface-100/50" : "border-transparent text-muted-foreground hover:text-foreground hover:bg-surface-50"
    }`}
  >
    {icon}
    {label}
  </button>
);
