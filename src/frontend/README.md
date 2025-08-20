# SmartLinks Admin Panel

A modern, responsive admin dashboard for managing SmartLinks with real-time metrics, analytics, and an AI assistant.

## Features

- **Real-time Monitoring**: View system health and metrics in real-time
- **Interactive Charts**: Visualize traffic patterns and performance metrics
- **AI Assistant**: Get insights and perform actions using natural language
- **Responsive Design**: Works on desktop and tablet devices
- **Dark Mode**: Easy on the eyes during late-night monitoring sessions

## Tech Stack

- **Frontend**: React 18, TypeScript, Vite
- **Styling**: Tailwind CSS with custom theming
- **Charts**: Chart.js with react-chartjs-2
- **UI Components**: Headless UI, Heroicons
- **State Management**: React Context API
- **HTTP Client**: Axios
- **Markdown Rendering**: react-markdown

## Prerequisites

- Node.js 16+ and npm 8+
- SmartLinks backend service running (for API calls)

## Getting Started

1. **Install Dependencies**

```bash
cd src/frontend
npm install
```

2. **Environment Variables**

Create a `.env` file in the `frontend` directory with the following variables:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_OPENAI_API_KEY=your_openai_api_key_here
```

3. **Development Server**

```bash
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

4. **Production Build**

```bash
npm run build
```

The build artifacts will be stored in the `dist/` directory.

## Project Structure

```
src/
  ├── components/         # Reusable UI components
  │   ├── ai/            # AI Assistant components
  │   ├── dashboard/     # Dashboard specific components
  │   └── layout/        # Layout components (header, sidebar, etc.)
  ├── contexts/          # React contexts
  ├── lib/               # Utility functions and API client
  ├── pages/             # Page components
  └── App.tsx            # Main application component
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

## Backend Integration

The admin panel expects the following API endpoints to be available:

- `GET /admin/health` - System health status
- `GET /admin/metrics` - Traffic and performance metrics
- `GET /admin/stats` - Statistics and analytics
- `POST /admin/seed` - Seed the database with test data
- `POST /admin/payout` - Update payout rates
- `POST /admin/db/flush` - Flush the database (development only)
- `POST /admin/assistant` - AI Assistant endpoint

## License

MIT
