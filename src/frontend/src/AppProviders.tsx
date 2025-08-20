// src/AppProviders.tsx
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import { ServiceStatusProvider } from './contexts/ServiceStatusContext';
import { ConfigProvider, theme as antdTheme } from 'antd';

type Props = {
  children: React.ReactNode;
};

function AntdThemer({ children }: Props) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <ConfigProvider
      theme={{
        algorithm: isDark ? [antdTheme.darkAlgorithm] : [antdTheme.defaultAlgorithm],
      }}
    >
      {children}
    </ConfigProvider>
  );
}

export function AppProviders({ children }: Props) {
  return (
    <ThemeProvider>
      <AntdThemer>
        <ServiceStatusProvider>
          <BrowserRouter>
            {children}
          </BrowserRouter>
        </ServiceStatusProvider>
      </AntdThemer>
    </ThemeProvider>
  );
}
