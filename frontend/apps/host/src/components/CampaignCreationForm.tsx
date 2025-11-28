import React, { useState } from 'react';
import { campaignsApi } from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, Input, Button } from '@rpg/ui';

export type CampaignCreate = any;

export interface CampaignCreationFormProps {
  onSuccess?: (campaignId: string) => void;
  onCancel?: () => void;
}

export function CampaignCreationForm({ onSuccess, onCancel }: CampaignCreationFormProps) {
  const [formData, setFormData] = useState<Partial<CampaignCreate>>({
    name: '',
    description: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (!formData.name) {
        setError('Campaign name is required');
        setLoading(false);
        return;
      }

      const campaign = await campaignsApi.createCampaign(formData as CampaignCreate);
      onSuccess?.(campaign.id);
    } catch (err: any) {
      setError(err.message || 'Failed to create campaign');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: keyof CampaignCreate, value: any) => {
    setFormData((prev: any) => ({ ...prev, [field]: value }));
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create Campaign</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-1 block">Campaign Name *</label>
            <Input
              value={formData.name || ''}
              onChange={(e) => handleChange('name', e.target.value)}
              required
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-1 block">Description</label>
            <textarea
              value={formData.description || ''}
              onChange={(e) => handleChange('description', e.target.value)}
              className="w-full px-3 py-2 border rounded-md bg-background text-sm min-h-[100px]"
            />
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
              {loading ? 'Creating...' : 'Create Campaign'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}



