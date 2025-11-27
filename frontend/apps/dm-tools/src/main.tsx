import React from 'react';
import ReactDOM from 'react-dom/client';
import { DMTools } from './DMTools';

// For standalone development
const root = document.getElementById('root');
if (root) {
  ReactDOM.createRoot(root).render(
    <React.StrictMode>
      <DMTools />
    </React.StrictMode>
  );
}



