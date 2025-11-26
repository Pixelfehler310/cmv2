import React from 'react';
import ReactDOM from 'react-dom/client';
import { Cartographer } from './Cartographer';

// For standalone development
const root = document.getElementById('root');
if (root) {
  ReactDOM.createRoot(root).render(
    <React.StrictMode>
      <Cartographer />
    </React.StrictMode>
  );
}

