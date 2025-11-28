import React from 'react';
import { useCharacters } from '../lib/api';
import { Select } from './Select';
import type { CharacterResponse as Character } from '@rpg/types';

export interface CharacterSelectorProps {
  selectedCharacterId: string | null;
  onCharacterSelect: (characterId: string | null) => void;
}

export function CharacterSelector({ selectedCharacterId, onCharacterSelect }: CharacterSelectorProps) {
  const { data: characters, loading, error } = useCharacters();

  if (loading) {
    return <div className="p-2 text-sm text-muted-foreground">Loading characters...</div>;
  }

  if (error) {
    return <div className="p-2 text-sm text-destructive">Error loading characters</div>;
  }

  if (!characters || characters.length === 0) {
    return <div className="p-2 text-sm text-muted-foreground">No characters found</div>;
  }

  return (
    <div className="p-2">
      <label className="text-sm font-medium mb-2 block">Select Character:</label>
      <select
        value={selectedCharacterId || ''}
        onChange={(e) => onCharacterSelect(e.target.value || null)}
        className="w-full px-3 py-2 border rounded-md bg-background"
      >
        <option value="">-- Select Character --</option>
        {characters.map((char) => (
          <option key={char.id} value={char.id}>
            {char.name} (Level {char.level} {(char as any).class_name})
          </option>
        ))}
      </select>
    </div>
  );
}

