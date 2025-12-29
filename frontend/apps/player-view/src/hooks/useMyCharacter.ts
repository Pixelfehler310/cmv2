import { useQuery } from '@tanstack/react-query';
import { IHostBridge } from '@rpg/bridge';
import { Character } from '../types';

export const useMyCharacter = (bridge: IHostBridge, campaignId: string) => {
  return useQuery({
    queryKey: ['my-character', campaignId],
    queryFn: async (): Promise<Character | null> => {
      const user = await bridge.auth.getUser();
      if (!user) return null;

      // Filter by player_id (user.username for now) and campaign_id
      const params = new URLSearchParams({
        player_id: user.username, 
        campaign_id: campaignId
      });

      // We need a way to get the token. 
      // Assuming bridge.auth has a way or we use a global fetch wrapper.
      // For now, let's try to cast or assume we can get it, or better, add it to interface.
      // @ts-ignore - We will add getToken to interface
      const token = bridge.auth.getToken ? bridge.auth.getToken() : null;

      const response = await fetch(`/api/characters?${params.toString()}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch character');
      }

      const characters = await response.json();
      return characters[0] || null;
    },
    enabled: !!campaignId
  });
};
