import { describe, it, expect, vi, beforeEach } from 'vitest';
import { itemsApi, ApiError } from '../client';

// Mock fetch globally
global.fetch = vi.fn();

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('itemsApi', () => {
    it('should fetch items successfully', async () => {
      const mockItems = [
        { id: '1', name: 'Sword', description: 'A sword', type: 'weapon', rarity: 'common', weight: 3, price: 100, properties: {}, effects: [] },
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockItems,
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      const result = await itemsApi.getItems();
      expect(result).toEqual(mockItems);
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/items/',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
    });

    it('should handle API errors', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => ({ detail: 'Item not found' }),
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      await expect(itemsApi.getItem('invalid-id')).rejects.toThrow(ApiError);
    });
  });
});

