import { ChatMessage } from './types';

export const chatHistory: ChatMessage[] = [
  {
    id: 'msg-1',
    sender: 'System',
    content: 'Welcome to the session!',
    timestamp: '19:00',
    type: 'system'
  },
  {
    id: 'msg-2',
    sender: 'DM',
    content: 'You see two goblins guarding the entrance.',
    timestamp: '19:05',
    type: 'text'
  },
  {
    id: 'msg-3',
    sender: 'Gandalf',
    content: 'I cast Fireball!',
    timestamp: '19:06',
    type: 'text'
  },
  {
    id: 'msg-4',
    sender: 'Gandalf',
    content: 'Rolling damage...',
    timestamp: '19:06',
    type: 'roll',
    roll: {
      expression: '8d6',
      total: 28,
      breakdown: '[3, 5, 1, 6, 4, 2, 5, 2]',
      result: [3, 5, 1, 6, 4, 2, 5, 2]
    }
  },
  {
    id: 'msg-5',
    sender: 'DM',
    content: 'The goblins are incinerated.',
    timestamp: '19:07',
    type: 'text'
  }
];
