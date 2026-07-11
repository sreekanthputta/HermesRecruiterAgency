import React from 'react';
import ReactDOM from 'react-dom/client';
import { ConvexProvider, ConvexReactClient } from 'convex/react';
import App from './App';

const convexUrl = import.meta.env.VITE_CONVEX_URL as string | undefined;
const convex = convexUrl ? new ConvexReactClient(convexUrl) : null;

const root = ReactDOM.createRoot(document.getElementById('root')!);

if (convex) {
  root.render(
    <React.StrictMode>
      <ConvexProvider client={convex}>
        <App demoMode={false} />
      </ConvexProvider>
    </React.StrictMode>
  );
} else {
  root.render(
    <React.StrictMode>
      <App demoMode={true} />
    </React.StrictMode>
  );
}
