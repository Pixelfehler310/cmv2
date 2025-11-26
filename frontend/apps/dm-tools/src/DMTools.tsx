import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@rpg/ui';
import { Card, CardContent, CardHeader, CardTitle, Button, Input } from '@rpg/ui';
import type { Monster, Campaign, Character } from '@rpg/types';

export interface DMToolsProps {
  monsters?: Monster[];
  campaigns?: Campaign[];
  onMonsterSelect?: (monster: Monster) => void;
  onCampaignSelect?: (campaign: Campaign) => void;
  onSpawnMonster?: (monsterId: string) => void;
  onUpdateHP?: (entityId: string, hp: number) => void;
  showItems?: boolean;
  showSpells?: boolean;
  showCharacterCreation?: boolean;
  showCampaignCreation?: boolean;
}

export function DMTools({
  monsters = [],
  campaigns = [],
  onMonsterSelect,
  onCampaignSelect,
  onSpawnMonster,
  onUpdateHP,
  showItems = false,
  showSpells = false,
  showCharacterCreation = false,
  showCampaignCreation = false,
}: DMToolsProps) {
  const tabCount = 3 + (showItems ? 1 : 0) + (showSpells ? 1 : 0) + (showCharacterCreation ? 1 : 0) + (showCampaignCreation ? 1 : 0);
  
  return (
    <div className="h-full overflow-auto p-4">
      <Tabs defaultValue="monsters" className="w-full">
        <TabsList className={`grid w-full grid-cols-${tabCount}`}>
          <TabsTrigger value="monsters">Monster Library</TabsTrigger>
          <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
          <TabsTrigger value="initiative">Initiative</TabsTrigger>
          {showItems && <TabsTrigger value="items">Items</TabsTrigger>}
          {showSpells && <TabsTrigger value="spells">Spells</TabsTrigger>}
          {showCharacterCreation && <TabsTrigger value="create-character">Create Character</TabsTrigger>}
          {showCampaignCreation && <TabsTrigger value="create-campaign">Create Campaign</TabsTrigger>}
        </TabsList>

        <TabsContent value="monsters" className="mt-4">
          <MonsterLibraryPanel
            monsters={monsters}
            onMonsterSelect={onMonsterSelect}
            onSpawnMonster={onSpawnMonster}
          />
        </TabsContent>

        <TabsContent value="campaigns" className="mt-4">
          <CampaignManagementPanel
            campaigns={campaigns}
            onCampaignSelect={onCampaignSelect}
          />
        </TabsContent>

        <TabsContent value="initiative" className="mt-4">
          <InitiativeTrackerPanel onUpdateHP={onUpdateHP} />
        </TabsContent>
        {showItems && (
          <TabsContent value="items" className="mt-4">
            <ItemsTab />
          </TabsContent>
        )}
        {showSpells && (
          <TabsContent value="spells" className="mt-4">
            <SpellsTab />
          </TabsContent>
        )}
        {showCharacterCreation && (
          <TabsContent value="create-character" className="mt-4">
            <CharacterCreationTab />
          </TabsContent>
        )}
        {showCampaignCreation && (
          <TabsContent value="create-campaign" className="mt-4">
            <CampaignCreationTab />
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
}

// Placeholder components - these would be imported from host app in real implementation
function ItemsTab() {
  return <div className="p-4">Items browser will be integrated here</div>;
}

function SpellsTab() {
  return <div className="p-4">Spells browser will be integrated here</div>;
}

function CharacterCreationTab() {
  return <div className="p-4">Character creation form will be integrated here</div>;
}

function CampaignCreationTab() {
  return <div className="p-4">Campaign creation form will be integrated here</div>;
}

function MonsterLibraryPanel({
  monsters,
  onMonsterSelect,
  onSpawnMonster,
}: {
  monsters: Monster[];
  onMonsterSelect?: (monster: Monster) => void;
  onSpawnMonster?: (monsterId: string) => void;
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedMonster, setSelectedMonster] = useState<Monster | null>(null);

  const filteredMonsters = monsters.filter((monster) =>
    monster.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleMonsterClick = (monster: Monster) => {
    setSelectedMonster(monster);
    onMonsterSelect?.(monster);
  };

  const handleSpawn = () => {
    if (selectedMonster && onSpawnMonster) {
      onSpawnMonster(selectedMonster.id);
    }
  };

  return (
    <div className="grid grid-cols-2 gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Monster Library</CardTitle>
          <Input
            placeholder="Search monsters..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="mt-2"
          />
        </CardHeader>
        <CardContent>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {filteredMonsters.length === 0 ? (
              <p className="text-muted-foreground text-sm">No monsters found</p>
            ) : (
              filteredMonsters.map((monster) => (
                <div
                  key={monster.id}
                  className={`p-2 border rounded cursor-pointer hover:bg-accent ${
                    selectedMonster?.id === monster.id ? 'bg-accent' : ''
                  }`}
                  onClick={() => handleMonsterClick(monster)}
                >
                  <div className="font-semibold">{monster.name}</div>
                  <div className="text-sm text-muted-foreground">
                    {monster.type} • CR {monster.hit_points}
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Monster Details</CardTitle>
        </CardHeader>
        <CardContent>
          {selectedMonster ? (
            <div className="space-y-4">
              <div>
                <h3 className="font-bold text-lg">{selectedMonster.name}</h3>
                <p className="text-sm text-muted-foreground">
                  {selectedMonster.size} {selectedMonster.type}, {selectedMonster.alignment}
                </p>
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="font-semibold">AC:</span> {selectedMonster.armor_class}
                </div>
                <div>
                  <span className="font-semibold">HP:</span> {selectedMonster.hit_points}
                </div>
                <div>
                  <span className="font-semibold">Speed:</span>{' '}
                  {Object.entries(selectedMonster.speed)
                    .map(([key, value]) => `${key} ${value}ft`)
                    .join(', ')}
                </div>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Ability Scores</h4>
                <div className="grid grid-cols-3 gap-2 text-sm">
                  <div>STR: {selectedMonster.strength}</div>
                  <div>DEX: {selectedMonster.dexterity}</div>
                  <div>CON: {selectedMonster.constitution}</div>
                  <div>INT: {selectedMonster.intelligence}</div>
                  <div>WIS: {selectedMonster.wisdom}</div>
                  <div>CHA: {selectedMonster.charisma}</div>
                </div>
              </div>
              {selectedMonster.description && (
                <div>
                  <p className="text-sm">{selectedMonster.description}</p>
                </div>
              )}
              <Button onClick={handleSpawn} className="w-full">
                Spawn Monster
              </Button>
            </div>
          ) : (
            <p className="text-muted-foreground text-sm">Select a monster to view details</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function CampaignManagementPanel({
  campaigns,
  onCampaignSelect,
}: {
  campaigns: Campaign[];
  onCampaignSelect?: (campaign: Campaign) => void;
}) {
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);

  const handleCampaignClick = (campaign: Campaign) => {
    setSelectedCampaign(campaign);
    onCampaignSelect?.(campaign);
  };

  return (
    <div className="grid grid-cols-2 gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Campaigns</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {campaigns.length === 0 ? (
              <p className="text-muted-foreground text-sm">No campaigns found</p>
            ) : (
              campaigns.map((campaign) => (
                <div
                  key={campaign.id}
                  className={`p-2 border rounded cursor-pointer hover:bg-accent ${
                    selectedCampaign?.id === campaign.id ? 'bg-accent' : ''
                  }`}
                  onClick={() => handleCampaignClick(campaign)}
                >
                  <div className="font-semibold">{campaign.name}</div>
                  {campaign.description && (
                    <div className="text-sm text-muted-foreground">{campaign.description}</div>
                  )}
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Campaign Details</CardTitle>
        </CardHeader>
        <CardContent>
          {selectedCampaign ? (
            <div className="space-y-4">
              <div>
                <h3 className="font-bold text-lg">{selectedCampaign.name}</h3>
                {selectedCampaign.description && (
                  <p className="text-sm text-muted-foreground">{selectedCampaign.description}</p>
                )}
              </div>
              <div>
                <h4 className="font-semibold mb-2">Characters ({selectedCampaign.characters.length})</h4>
                {selectedCampaign.characters.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No characters in this campaign</p>
                ) : (
                  <ul className="space-y-1">
                    {selectedCampaign.characters.map((character) => (
                      <li key={character.id} className="text-sm">
                        {character.name} - Level {character.level} {character.class_name}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          ) : (
            <p className="text-muted-foreground text-sm">Select a campaign to view details</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function InitiativeTrackerPanel({
  onUpdateHP,
}: {
  onUpdateHP?: (entityId: string, hp: number) => void;
}) {
  const [combatants, setCombatants] = useState<Array<{ id: string; name: string; initiative: number; hp: number; maxHp: number }>>([]);
  const [editingHP, setEditingHP] = useState<{ id: string; value: number } | null>(null);

  const sortedCombatants = [...combatants].sort((a, b) => b.initiative - a.initiative);

  const handleHPChange = (id: string, newHP: number) => {
    setCombatants((prev) =>
      prev.map((c) => (c.id === id ? { ...c, hp: Math.max(0, Math.min(c.maxHp, newHP)) } : c))
    );
    if (onUpdateHP) {
      onUpdateHP(id, newHP);
    }
    setEditingHP(null);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Initiative Tracker</CardTitle>
      </CardHeader>
      <CardContent>
        {combatants.length === 0 ? (
          <p className="text-muted-foreground text-sm">No combatants in initiative order</p>
        ) : (
          <div className="space-y-2">
            {sortedCombatants.map((combatant, index) => (
              <div
                key={combatant.id}
                className="flex items-center justify-between p-2 border rounded"
              >
                <div className="flex items-center gap-4">
                  <div className="w-8 text-center font-bold">{index + 1}</div>
                  <div>
                    <div className="font-semibold">{combatant.name}</div>
                    <div className="text-sm text-muted-foreground">
                      Initiative: {combatant.initiative}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {editingHP?.id === combatant.id ? (
                    <div className="flex items-center gap-2">
                      <Input
                        type="number"
                        value={editingHP.value}
                        onChange={(e) =>
                          setEditingHP({ id: combatant.id, value: parseInt(e.target.value) || 0 })
                        }
                        className="w-20"
                        min={0}
                        max={combatant.maxHp}
                      />
                      <Button
                        size="sm"
                        onClick={() => handleHPChange(combatant.id, editingHP.value)}
                      >
                        Save
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setEditingHP(null)}
                      >
                        Cancel
                      </Button>
                    </div>
                  ) : (
                    <>
                      <div className="text-sm">
                        HP: {combatant.hp} / {combatant.maxHp}
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setEditingHP({ id: combatant.id, value: combatant.hp })}
                      >
                        Edit HP
                      </Button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

