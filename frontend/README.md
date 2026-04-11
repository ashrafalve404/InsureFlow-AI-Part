# InsureFlow AI Frontend

Next.js frontend for the InsureFlow AI Real-Time Sales Assistant.

## Overview

A modern, production-structured Next.js dashboard for insurance sales agents. Features live call assistance, CRM context integration, RAG-based knowledge retrieval, and real-time transcript streaming.

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Animation**: Framer Motion
- **State**: Zustand
- **Charts**: Recharts

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will be available at http://localhost:3000

### Build for Production

```bash
npm run build
npm start
```

## Configuration

### Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_DEMO_MODE=false
```

- `NEXT_PUBLIC_BACKEND_URL`: Your Python backend URL
- `NEXT_PUBLIC_WS_URL`: WebSocket URL for live updates
- `NEXT_PUBLIC_DEMO_MODE`: Set to true to use mock data

## Pages

| Route | Description |
|-------|-------------|
| `/dashboard` | Main dashboard with stats overview |
| `/dashboard/live` | Live call assistant (most important) |
| `/dashboard/calls` | Call session history |
| `/dashboard/crm` | CRM context/lead lookup |
| `/dashboard/knowledge` | RAG knowledge base status |
| `/dashboard/alerts` | Compliance alerts |
| `/dashboard/settings` | System settings |
| `/dashboard/demo` | Demo/testing mode |

## Live Call Assistant

The heart of the app - `/dashboard/live` provides:

- **Left Panel**: Real-time transcript stream with speaker labels
- **Center Panel**: AI-generated suggestions with objection detection & compliance warnings  
- **Right Panel**: CRM context (name, tags, notes, pipeline stage)

## Backend Integration

The frontend expects these backend endpoints:

```
POST /api/calls/start      - Start new call session
GET  /api/calls           - List sessions
GET  /api/calls/{id}      - Get session details
POST /api/calls/{id}/end - End session
POST /api/transcripts     - Send transcript
GET  /api/rag/status     - RAG status
GET  /api/crm/status    - CRM status
GET  /api/crm/contact/by-phone?phone=... - Lookup contact
WS  /ws/calls/{session_id] - WebSocket for live updates
```

## Demo Mode

When backend is unavailable, use Demo Mode:

1. Go to `/dashboard/demo`
2. Click "Start Demo Session"
3. Type messages to simulate conversation
4. See AI responses update in real-time

## Mock Data

Mock data is provided in `lib/mock-data.ts` for:
- Call sessions
- Transcripts
- AI suggestions
- CRM contacts
- Dashboard stats

## Project Structure

```
frontend/
├── app/                    # Next.js pages
│   ├── dashboard/          # Main app pages
│   │   ├── live/           # Live call assistant
│   │   ├── calls/         # Call history
│   │   ├── demo/          # Demo mode
│   │   └── ...
│   ├── globals.css         # Global styles
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Redirects to dashboard
├── components/
│   └── layout/            # Layout components
├── lib/
│   ├── api.ts             # Backend API client
│   ├── mock-data.ts       # Mock data
│   ├── types.ts           # TypeScript types
│   ├── utils.ts           # Utility functions
│   └── services/
│       └── ws.ts          # WebSocket manager
└── store/
    └── live-session-store.ts  # Zustand store
```

## Features

- Real-time transcript streaming
- AI response suggestions
- Objection detection display
- Compliance/risk warnings
- CRM context integration
- Call stage detection
- WebSocket live updates
- Demo mode for testing
- Responsive design

## Troubleshooting

**Frontend not connecting to backend:**
- Check `NEXT_PUBLIC_BACKEND_URL` in `.env.local`
- Ensure backend is running at that URL

**WebSocket not working:**
- Check `NEXT_PUBLIC_WS_URL`
- Ensure CORS is configured on backend

**Missing data:**
- Run the RAG ingestion: `python -m app.rag.ingest`
- Check CRM credentials in `.env`

## License

Internal use only - InsureFlow AI