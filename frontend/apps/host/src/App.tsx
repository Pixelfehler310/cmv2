import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LoginRoute } from './routes/LoginRoute';
import { CampaignSelectorRoute } from './routes/CampaignSelectorRoute';
import { SessionRoute } from './routes/SessionRoute';
import { AuthService } from './lib/auth';
import { WebSocketManager } from './lib/websocket';

import { logger } from './lib/logger';

// Initialize Core Services
const queryClient = new QueryClient();
const authService = new AuthService();
const wsManager = new WebSocketManager('ws://localhost:8000');

function App() {
  logger.info('App starting...');
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-background text-foreground font-sans antialiased">
           <Routes>
             <Route path="/" element={<LoginRoute auth={authService} />} />
             <Route path="/campaigns" element={<CampaignSelectorRoute auth={authService} />} />
             <Route path="/session/:id" element={
               <SessionRoute 
                 auth={authService} 
                 ws={wsManager} 
                 queryClient={queryClient} 
               />
             } />
             {/* Fallback */}
             <Route path="*" element={<Navigate to="/" replace />} />
           </Routes>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App;
