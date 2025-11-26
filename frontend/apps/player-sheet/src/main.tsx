import React from 'react';
import ReactDOM from 'react-dom/client';
import { PlayerSheet } from './PlayerSheet';

// For standalone development
const root = document.getElementById('root');
if (root) {
  ReactDOM.createRoot(root).render(
    <React.StrictMode>
      <PlayerSheet character={null} />
    </React.StrictMode>
  );
}

