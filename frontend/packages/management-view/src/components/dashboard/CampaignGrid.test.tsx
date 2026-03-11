import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { CampaignGrid } from './CampaignGrid';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('CampaignGrid Component', () => {
  beforeEach(() => {
    // Clear mocks before each test
    mockFetch.mockReset();
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('sends the correct Authorization header from localStorage', async () => {
    // 1. Arrange: Setup localStorage with a simulated valid token
    const testToken = 'dev-token';
    localStorage.setItem('civic_auth_token', testToken);

    // Mock successful fetch response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [
        { id: 'camp1', name: 'Test Campaign', role: 'DM' },
      ],
    } as Response);

    // 2. Act: Render the component
    render(
      <MemoryRouter>
        <CampaignGrid />
      </MemoryRouter>
    );

    // 3. Assert: Verify the fetch was called correctly
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/campaigns', {
        headers: { Authorization: `Bearer ${testToken}` },
      });
    });

    // Check if campaign is rendered to confirm success
    expect(await screen.findByText('Test Campaign')).toBeDefined();
  });

  it('shows error or fallback if the token is missing and fetch gets 401', async () => {
    // 1. Arrange: localStorage is empty (simulating no login token)

    // Mock 401 Unauthorized response from fetch
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      json: async () => ({ detail: 'Not authenticated' })
    } as Response);

    // 2. Act: Render the component
    render(
      <MemoryRouter>
        <CampaignGrid />
      </MemoryRouter>
    );

    // 3. Assert: Verify fetch was called with a 'null' token
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/campaigns', {
        headers: { Authorization: 'Bearer null' },
      });
    });

    // Wait for the fallback campaigns to render
    expect(await screen.findByText('Curse of Strahd')).toBeDefined();
  });
});
