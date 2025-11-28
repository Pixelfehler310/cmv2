import React, { useState } from 'react';
import { charactersApi } from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, Input, Button } from '@rpg/ui';

export type CharacterCreate = any;

export interface CharacterCreationFormProps {
  onSuccess?: (characterId: string) => void;
  onCancel?: () => void;
}

export function CharacterCreationForm({ onSuccess, onCancel }: CharacterCreationFormProps) {
  const [formData, setFormData] = useState<Partial<CharacterCreate>>({
    name: '',
    race: '',
    class_name: '',
    level: 1,
    strength: 10,
    dexterity: 10,
    constitution: 10,
    intelligence: 10,
    wisdom: 10,
    charisma: 10,
    max_hp: 10,
    current_hp: 10,
    hit_dice: '1d8',
    armor_class: 10,
    speed: 30,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (!formData.name || !formData.race || !formData.class_name || !formData.max_hp || !formData.hit_dice) {
        setError('Please fill in all required fields');
        setLoading(false);
        return;
      }

      const character = await charactersApi.createCharacter(formData as CharacterCreate);
      onSuccess?.(character.id);
    } catch (err: any) {
      setError(err.message || 'Failed to create character');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: keyof CharacterCreate, value: any) => {
    setFormData((prev: any) => ({ ...prev, [field]: value }));
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create Character</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-1 block">Name *</label>
              <Input
                value={formData.name || ''}
                onChange={(e) => handleChange('name', e.target.value)}
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Player Name</label>
              <Input
                value={formData.player_name || ''}
                onChange={(e) => handleChange('player_name', e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Race *</label>
              <Input
                value={formData.race || ''}
                onChange={(e) => handleChange('race', e.target.value)}
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Class *</label>
              <Input
                value={formData.class_name || ''}
                onChange={(e) => handleChange('class_name', e.target.value)}
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Level</label>
              <Input
                type="number"
                value={formData.level || 1}
                onChange={(e) => handleChange('level', parseInt(e.target.value) || 1)}
                min={1}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Hit Dice *</label>
              <Input
                value={formData.hit_dice || ''}
                onChange={(e) => handleChange('hit_dice', e.target.value)}
                placeholder="e.g., 1d8"
                required
              />
            </div>
          </div>

          <div>
            <h3 className="font-semibold mb-2">Ability Scores</h3>
            <div className="grid grid-cols-3 gap-4">
              {[
                { key: 'strength', label: 'Strength' },
                { key: 'dexterity', label: 'Dexterity' },
                { key: 'constitution', label: 'Constitution' },
                { key: 'intelligence', label: 'Intelligence' },
                { key: 'wisdom', label: 'Wisdom' },
                { key: 'charisma', label: 'Charisma' },
              ].map(({ key, label }) => (
                <div key={key}>
                  <label className="text-sm font-medium mb-1 block">{label}</label>
                  <Input
                    type="number"
                    value={formData[key as string] || 10}
                    onChange={(e) => handleChange(key as string, parseInt(e.target.value) || 10)}
                    min={1}
                    max={30}
                  />
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium mb-1 block">Max HP *</label>
              <Input
                type="number"
                value={formData.max_hp || 10}
                onChange={(e) => handleChange('max_hp', parseInt(e.target.value) || 10)}
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Current HP</label>
              <Input
                type="number"
                value={formData.current_hp || 10}
                onChange={(e) => handleChange('current_hp', parseInt(e.target.value) || 10)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Armor Class</label>
              <Input
                type="number"
                value={formData.armor_class || 10}
                onChange={(e) => handleChange('armor_class', parseInt(e.target.value) || 10)}
              />
            </div>
          </div>

          {error && (
            <div className="text-sm text-destructive">{error}</div>
          )}

          <div className="flex gap-2 justify-end">
            {onCancel && (
              <Button type="button" variant="outline" onClick={onCancel}>
                Cancel
              </Button>
            )}
            <Button type="submit" disabled={loading}>
              {loading ? 'Creating...' : 'Create Character'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}



