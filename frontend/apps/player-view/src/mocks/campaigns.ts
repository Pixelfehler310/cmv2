import { Campaign } from './types';

export const campaigns: Campaign[] = [
  {
    id: 'campaign-1',
    name: 'Curse of Strahd',
    role: 'DM',
    image: 'https://images.unsplash.com/photo-1599058945522-28d584b6f0ff?q=80&w=2669&auto=format&fit=crop',
    nextSession: '2023-11-30T19:00:00Z',
    members: [
      { userId: 'user-1', role: 'DM' }, // Me
      { userId: 'dev-user', role: 'DM' }, // Dev User
      { userId: 'user-2', role: 'PLAYER' },
      { userId: 'user-3', role: 'PLAYER' },
    ]
  },
  {
    id: 'campaign-2',
    name: 'Lost Mine of Phandelver',
    role: 'PLAYER',
    image: 'https://images.unsplash.com/photo-1519074069444-1ba4fff66d16?q=80&w=2574&auto=format&fit=crop',
    nextSession: '2023-12-05T20:00:00Z',
    members: [
      { userId: 'user-4', role: 'DM' },
      { userId: 'user-1', role: 'PLAYER' }, // Me
      { userId: 'dev-user', role: 'PLAYER' }, // Dev User
      { userId: 'user-5', role: 'PLAYER' },
    ]
  }
];
