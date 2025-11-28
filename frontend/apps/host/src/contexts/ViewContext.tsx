import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useAuth } from './AuthContext';
import type { CampaignResponse as Campaign } from '@rpg/types';

type ViewType = 'player' | 'dm' | null;

interface ViewContextType {
  currentView: ViewType;
  selectedCampaign: Campaign | null;
  switchView: (view: ViewType) => void;
  setSelectedCampaign: (campaign: Campaign | null) => void;
  canAccessView: (view: ViewType) => boolean;
}

const ViewContext = createContext<ViewContextType | undefined>(undefined);

export function ViewProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [currentView, setCurrentView] = useState<ViewType>(null);
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);

  // TODO: Load last selected campaign from localStorage or API
  useEffect(() => {
    // For now, default to player view if user is authenticated
    // In the future, this will be based on campaign selection and user role
    if (user && !currentView) {
      // Default view selection logic will go here
    }
  }, [user, currentView]);

  const switchView = (view: ViewType) => {
    if (view && !selectedCampaign) {
      console.warn('Cannot switch view without a selected campaign');
      return;
    }
    setCurrentView(view);
  };

  const canAccessView = (view: ViewType): boolean => {
    if (!view) return false;
    if (!selectedCampaign) return false;
    if (!user) return false;
    
    // TODO: Add permission checks based on user role and campaign
    // For now, allow both views if campaign is selected
    return true;
  };

  return (
    <ViewContext.Provider
      value={{
        currentView,
        selectedCampaign,
        switchView,
        setSelectedCampaign,
        canAccessView,
      }}
    >
      {children}
    </ViewContext.Provider>
  );
}

export function useView() {
  const context = useContext(ViewContext);
  if (context === undefined) {
    throw new Error('useView must be used within a ViewProvider');
  }
  return context;
}

