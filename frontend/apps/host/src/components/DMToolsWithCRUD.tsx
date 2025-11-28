import React from 'react';
import { DMTools } from '@rpg/dm-tools';
import { ItemBrowser } from './ItemBrowser';
import { SpellBrowser } from './SpellBrowser';
import { CharacterCreationForm } from './CharacterCreationForm';
import { CampaignCreationForm } from './CampaignCreationForm';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@rpg/ui';
import type { MonsterResponse as Monster, CampaignResponse as Campaign } from '@rpg/types';

export interface DMToolsWithCRUDProps {
  monsters?: Monster[];
  campaigns?: Campaign[];
  onMonsterSelect?: (monster: Monster) => void;
  onCampaignSelect?: (campaign: Campaign) => void;
  onSpawnMonster?: (monsterId: string) => void;
  onUpdateHP?: (entityId: string, hp: number) => void;
  onCharacterCreated?: (characterId: string) => void;
  onCampaignCreated?: (campaignId: string) => void;
}

export function DMToolsWithCRUD(props: DMToolsWithCRUDProps) {
  return (
    <div className="h-full overflow-auto p-4">
      <Tabs defaultValue="monsters" className="w-full">
        <TabsList className="grid w-full grid-cols-7">
          <TabsTrigger value="monsters">Monster Library</TabsTrigger>
          <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
          <TabsTrigger value="initiative">Initiative</TabsTrigger>
          <TabsTrigger value="items">Items</TabsTrigger>
          <TabsTrigger value="spells">Spells</TabsTrigger>
          <TabsTrigger value="create-character">Create Character</TabsTrigger>
          <TabsTrigger value="create-campaign">Create Campaign</TabsTrigger>
        </TabsList>

        <TabsContent value="monsters" className="mt-4">
          <DMTools {...props} />
        </TabsContent>

        <TabsContent value="campaigns" className="mt-4">
          <DMTools {...props} />
        </TabsContent>

        <TabsContent value="initiative" className="mt-4">
          <DMTools {...props} />
        </TabsContent>

        <TabsContent value="items" className="mt-4">
          <ItemBrowser />
        </TabsContent>

        <TabsContent value="spells" className="mt-4">
          <SpellBrowser />
        </TabsContent>

        <TabsContent value="create-character" className="mt-4">
          <CharacterCreationForm onSuccess={props.onCharacterCreated} />
        </TabsContent>

        <TabsContent value="create-campaign" className="mt-4">
          <CampaignCreationForm onSuccess={props.onCampaignCreated} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

