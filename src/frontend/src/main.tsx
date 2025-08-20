// src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';
import { AppProviders } from './AppProviders';
import { Toaster } from 'sonner';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AppProviders>
      <App />
      <Toaster position="top-right" />
    </AppProviders>
  </React.StrictMode>
);
