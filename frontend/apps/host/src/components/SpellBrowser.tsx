import React, { useState } from 'react';
import { useSpells, useSpell } from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, Input } from '@rpg/ui';
import type { Spell } from '@rpg/types';

export function SpellBrowser() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSpellId, setSelectedSpellId] = useState<string | null>(null);
  const [levelFilter, setLevelFilter] = useState<string>('all');
  const { data: spells = [], loading } = useSpells();
  const { data: selectedSpell } = useSpell(selectedSpellId);

  const filteredSpells = spells.filter((spell) => {
    const matchesSearch = spell.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesLevel = levelFilter === 'all' || spell.level.toString() === levelFilter;
    return matchesSearch && matchesLevel;
  });

  return (
    <div className="grid grid-cols-2 gap-4 h-full">
      <Card>
        <CardHeader>
          <CardTitle>Spells</CardTitle>
          <Input
            placeholder="Search spells..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="mt-2"
          />
          <div className="mt-2">
            <select
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value)}
              className="w-full px-3 py-2 border rounded-md bg-background text-sm"
            >
              <option value="all">All Levels</option>
              {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((level) => (
                <option key={level} value={level.toString()}>
                  Level {level}
                </option>
              ))}
            </select>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-muted-foreground text-sm">Loading...</p>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {filteredSpells.length === 0 ? (
                <p className="text-muted-foreground text-sm">No spells found</p>
              ) : (
                filteredSpells.map((spell) => (
                  <div
                    key={spell.id}
                    className={`p-2 border rounded cursor-pointer hover:bg-accent ${
                      selectedSpellId === spell.id ? 'bg-accent' : ''
                    }`}
                    onClick={() => setSelectedSpellId(spell.id)}
                  >
                    <div className="font-semibold">{spell.name}</div>
                    <div className="text-sm text-muted-foreground">
                      Level {spell.level} • {spell.school}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Spell Details</CardTitle>
        </CardHeader>
        <CardContent>
          {selectedSpell ? (
            <div className="space-y-4">
              <div>
                <h3 className="font-bold text-lg">{selectedSpell.name}</h3>
                <p className="text-sm text-muted-foreground">
                  Level {selectedSpell.level} {selectedSpell.school}
                </p>
              </div>
              <div>
                <p className="text-sm">{selectedSpell.description}</p>
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="font-semibold">Casting Time:</span> {selectedSpell.casting_time}
                </div>
                <div>
                  <span className="font-semibold">Range:</span> {selectedSpell.range}
                </div>
                <div>
                  <span className="font-semibold">Duration:</span> {selectedSpell.duration}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-muted-foreground text-sm">Select a spell to view details</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}



