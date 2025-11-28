
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@rpg/ui';
import { StatBlock, HPBar } from '@rpg/ui';
import { Card, CardContent, CardHeader, CardTitle } from '@rpg/ui';
import type { CharacterResponse as Character } from '@rpg/types';

export interface PlayerSheetProps {
  character: Character | null;
  onAction?: (type: string, payload: any) => void;
}

export function PlayerSheet({ character, onAction }: PlayerSheetProps) {
  if (!character) {
    return (
      <div className="p-4">
        <p className="text-muted-foreground">No character selected</p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto p-4">
      <Tabs defaultValue="stats" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="stats">Stats</TabsTrigger>
          <TabsTrigger value="inventory">Inventory</TabsTrigger>
          <TabsTrigger value="spells">Spells</TabsTrigger>
          <TabsTrigger value="features">Features</TabsTrigger>
        </TabsList>

        <TabsContent value="stats" className="mt-4">
          <StatsTab character={character} onAction={onAction} />
        </TabsContent>

        <TabsContent value="inventory" className="mt-4">
          <InventoryTab character={character} />
        </TabsContent>

        <TabsContent value="spells" className="mt-4">
          <SpellsTab character={character} />
        </TabsContent>

        <TabsContent value="features" className="mt-4">
          <FeaturesTab character={character} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function StatsTab({ character, onAction }: { character: Character; onAction?: (type: string, payload: any) => void }) {
  const abilityScores = [
    { label: 'STR', value: character.strength || 10 },
    { label: 'DEX', value: character.dexterity || 10 },
    { label: 'CON', value: character.constitution || 10 },
    { label: 'INT', value: character.intelligence || 10 },
    { label: 'WIS', value: character.wisdom || 10 },
    { label: 'CHA', value: character.charisma || 10 },
  ];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Character Info</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div>
            <span className="font-semibold">Name:</span> {character.name}
          </div>
          <div>
            <span className="font-semibold">Race:</span> {(character as any).race || 'Unknown'}
          </div>
          <div>
            <span className="font-semibold">Class:</span> {(character as any).class_name || 'Unknown'}
          </div>
          <div>
            <span className="font-semibold">Level:</span> {character.level || 1}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Hit Points</CardTitle>
        </CardHeader>
        <CardContent>
          <HPBar
            current={character.current_hp}
            max={character.max_hp}
            temp={character.temp_hp || 0}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Ability Scores</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            {abilityScores.map((stat) => (
              <StatBlock
                key={stat.label}
                label={stat.label}
                value={stat.value}
                onClick={() => onAction?.('ROLL_ABILITY', { ability: stat.label.toLowerCase() })}
              />
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Combat Stats</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div>
            <span className="font-semibold">Armor Class:</span> {character.armor_class || 10}
          </div>
          <div>
            <span className="font-semibold">Speed:</span> {character.speed || 30} ft
          </div>
          <div>
            <span className="font-semibold">Initiative:</span> {character.initiative || 0}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function InventoryTab({ character }: { character: Character }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Inventory</CardTitle>
      </CardHeader>
      <CardContent>
        {(!character.inventory || character.inventory.length === 0) ? (
          <p className="text-muted-foreground">No items in inventory</p>
        ) : (
          <ul className="space-y-2">
            {character.inventory.map((item: any, index: number) => (
              <li key={index} className="border-b pb-2">
                <div className="font-semibold">{item.name || 'Unnamed Item'}</div>
                {item.description && (
                  <div className="text-sm text-muted-foreground">{item.description}</div>
                )}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

function SpellsTab({ character }: { character: Character }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Spells</CardTitle>
      </CardHeader>
      <CardContent>
        {(!character.spells || character.spells.length === 0) ? (
          <p className="text-muted-foreground">No spells known</p>
        ) : (
          <ul className="space-y-2">
            {character.spells.map((spell: any, index: number) => (
              <li key={index} className="border-b pb-2">
                <div className="font-semibold">{spell.name || 'Unnamed Spell'}</div>
                {spell.description && (
                  <div className="text-sm text-muted-foreground">{spell.description}</div>
                )}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

function FeaturesTab({ character: _character }: { character: Character }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Features & Traits</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground">Features and traits will be displayed here</p>
      </CardContent>
    </Card>
  );
}



