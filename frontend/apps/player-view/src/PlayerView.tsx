import React from 'react';
import { Layout, Model, TabNode, IJsonModel } from 'flexlayout-react';
import 'flexlayout-react/style/light.css';
import { IHostBridge } from '@rpg/bridge';
import { MapWindow } from './components/MapWindow';
import { NotesPanel } from './components/NotesPanel';
import { PartyPanel } from './components/PartyPanel';
import { ChatPanel } from './components/ChatPanel';
import { CombatPanel } from './components/CombatPanel';

import { CommandDeck } from './components/CommandDeck';

interface PlayerViewProps {
  bridge: IHostBridge;
  campaignId: string;
}

const jsonModel: IJsonModel = {
  global: {
    tabEnableClose: false,
    tabSetEnableMaximize: true,
    tabSetEnableTabStrip: true, // Show tabs
  },
  borders: [],
  layout: {
    type: 'row',
    weight: 100,
    children: [
      {
        type: 'tabset',
        weight: 20,
        children: [
          {
            type: 'tab',
            name: 'Notes',
            component: 'notes',
          },
          {
            type: 'tab',
            name: 'Party',
            component: 'party',
          },
        ],
      },
      {
        type: 'row',
        weight: 60,
        children: [
            {
                type: 'tabset',
                weight: 85,
                children: [
                {
                    type: 'tab',
                    name: 'Map',
                    component: 'map',
                    enableClose: false,
                },
                ],
            },
            {
                type: 'tabset',
                weight: 15,
                height: 120,
                enableMaximize: false,
                children: [
                {
                    type: 'tab',
                    name: 'Command Deck',
                    component: 'command-deck',
                    enableClose: false,
                },
                ],
            }
        ]
      },
      {
        type: 'tabset',
        weight: 20,
        children: [
          {
            type: 'tab',
            name: 'Chat',
            component: 'chat',
          },
          {
            type: 'tab',
            name: 'Combat',
            component: 'combat',
          },
        ],
      },
    ],
  },
};

export const PlayerView: React.FC<PlayerViewProps> = ({ bridge, campaignId }) => {
  // Use props to avoid lint error (and eventually pass them down)
  console.log('PlayerView initialized', { bridge, campaignId });

  const model = Model.fromJson(jsonModel);

  const factory = (node: TabNode) => {
    const component = node.getComponent();
    switch (component) {
      case 'notes':
        return <NotesPanel />;
      case 'party':
        return <PartyPanel />;
      case 'map':
        return <MapWindow />;
      case 'command-deck':
        return <CommandDeck />;
      case 'chat':
        return <ChatPanel />;
      case 'combat':
        return <CombatPanel />;
      default:
        return <div>Unknown Component</div>;
    }
  };

  return (
    <div className="h-full w-full relative">
      <Layout model={model} factory={factory} />
    </div>
  );
};
