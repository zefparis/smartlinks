import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

// Minimal admin guard based on a stored role. Integrate with your real auth/token.
// Set localStorage.setItem('role', 'admin') for dev access.
export default function RequireAdmin({ children }: { children: React.ReactElement }) {
  const location = useLocation();
  const role = (localStorage.getItem('role') || '').toLowerCase();

  if (role !== 'admin') {
    return (
      <div className="p-6">
        <h2 className="text-xl font-semibold text-red-600">Accès refusé</h2>
        <p className="text-sm text-gray-600 dark:text-gray-300 mt-2">
          Cette page est réservée aux administrateurs.
        </p>
        <pre className="mt-4 text-xs text-gray-500">Route: {location.pathname}</pre>
      </div>
    );
  }

  return children;
}
