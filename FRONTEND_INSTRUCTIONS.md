# Frontend Implementation Guide

## Overview

The PR Surgeon frontend is a Next.js 14 application with TypeScript, React Flow for graph visualization, and Tailwind CSS for styling. This document describes the current implementation and setup instructions.

## Current Implementation

### Pages

1. **`frontend/app/page.tsx`** — Landing page
   - PR URL input with validation
   - Three example PR cards (Django, Desbordante, Feedback-v2)
   - Real-time loading states during analysis
   - Dark mode toggle
   - IBM Bob branding

2. **`frontend/app/analysis/page.tsx`** — Analysis results page
   - React Flow dependency graph with color-coded clusters
   - Sub-PR cards with file lists and descriptions
   - Interactive node selection
   - Metadata bar (files count, sub-PRs, layers, duration)
   - Dark mode support

3. **`frontend/app/layout.tsx`** — Root layout
   - IBM Plex Sans and Mono fonts
   - Metadata configuration
   - Dark mode class management

4. **`frontend/app/globals.css`** — Global styles
   - IBM Plex font imports
   - React Flow custom styling
   - Dark mode color variables
   - Tailwind base styles

## Setup Instructions

### 1. Install Dependencies

```bash
cd frontend
npm install
```

**Key dependencies:**
- `next@^14.2.0` - Next.js framework
- `react@^18.3.0` - React library
- `reactflow@^11.11.0` - Graph visualization
- `lucide-react@^0.344.0` - Icon library
- `tailwindcss@^3.4.0` - CSS framework
- `framer-motion@^11.0.0` - Animations
- `react-markdown@^9.0.0` - Markdown rendering

### 2. Configure Environment

```bash
cp .env.local.example .env.local
```

Edit `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Note:** `.env.local` is gitignored. Never commit API keys or secrets.

### 3. Run Development Server

```bash
npm run dev
```

Frontend runs at http://localhost:3000

### 4. Verify Backend Connection

Ensure backend is running at http://localhost:8000:

**Windows PowerShell:**
```powershell
cd backend
.venv\Scripts\Activate.ps1
uvicorn main:app --reload
```

**Unix/Linux/macOS:**
```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload
```

### 5. Test the Application

1. Open http://localhost:3000
2. Click "Django: CompositePrimaryKey" example
3. Watch the analysis progress
4. Review the dependency graph and sub-PRs

## Features

### Landing Page

**Layout:**
- Centered hero section with gradient background
- PR URL input with validation
- "Analyze PR" button with loading states
- Three example PR cards
- Dark mode toggle (top-right)
- IBM Bob badge (top-right)

**Loading States:**
1. Fetching PR data from GitHub
2. Parsing files
3. Building dependency graph
4. Detecting clusters
5. Enriching sub-PRs

**Example PRs:**
- Django Composite Primary Key (43 files) - Recommended
- Desbordante AR validation (61 files)
- Feedback-v2 Next.js upgrade (64 files)

### Analysis Page

**Layout:**
- Top metadata bar (files, sub-PRs, layers, duration)
- Left panel: React Flow graph (60% width)
- Right panel: Sub-PR list and details (40% width)

**Graph Features:**
- Color-coded nodes by layer (schema, backend, frontend, tests)
- Interactive node selection
- Zoom and pan controls
- Dark mode support
- Cluster grouping with visual boundaries

**Sub-PR Cards:**
- Sequential numbering (merge order)
- Layer badge with color
- File count
- File list (expandable)
- Description and recommendations
- Risk level indicator

**Interactions:**
- Click node → highlight in sub-PR list
- Click sub-PR card → show details panel
- Hover effects on all interactive elements

## Design System

### Typography
- **Body**: IBM Plex Sans (400, 500, 600, 700)
- **Code**: IBM Plex Mono (400, 500)
- **Headings**: IBM Plex Sans (600, 700)

### Colors

**Light Mode:**
- Background: `#ffffff`
- Text: `#161616`
- Primary: `#0f62fe` (IBM Blue)
- Border: `#e0e0e0`

**Dark Mode:**
- Background: `#161616`
- Text: `#f4f4f4`
- Primary: `#78a9ff` (IBM Blue 40)
- Border: `#393939`

**Layer Colors:**
- Schema: `#8a3ffc` (Purple)
- Backend: `#0f62fe` (Blue)
- Frontend: `#24a148` (Green)
- Tests: `#fa4d56` (Red)
- Config: `#ff7eb6` (Magenta)
- Docs: `#f1c21b` (Yellow)

### Layout Principles
- Generous whitespace (16px, 24px, 32px, 48px)
- Sharp corners (no border-radius except buttons: 4px)
- Grid-based alignment
- Consistent padding and margins
- Enterprise-focused, professional aesthetic

## Troubleshooting

### Installation Issues

**"Module not found: reactflow"**
```bash
npm install reactflow lucide-react
```

**"Cannot find module 'next'"**
```bash
rm -rf node_modules package-lock.json
npm install
```

**TypeScript errors**
```bash
npm install --save-dev @types/react @types/node
```

### Runtime Issues

**CORS error in browser console**
- Verify backend is running at http://localhost:8000
- Check CORS configuration in `backend/main.py`
- Ensure `NEXT_PUBLIC_API_URL` is correct in `.env.local`

**"Cannot connect to backend"**
- Backend must be running: `uvicorn main:app --reload`
- Check backend health: http://localhost:8000/health
- Verify port 8000 is not in use by another process

**Graph not rendering**
- Check browser console for errors
- Verify React Flow is installed
- Try clearing browser cache
- Ensure analysis completed successfully

**Dark mode not working**
- Check localStorage: `pr-surgeon-theme`
- Clear browser storage and reload
- Verify `globals.css` is loaded

### Analysis Issues

**"No dependencies found"**
- Expected for PRs with minimal cross-file imports
- Try Django PR #18056 (well-connected)
- Check that PR has 20+ files

**Loading stuck**
- Check backend logs for errors
- Verify GitHub API rate limit not exceeded
- Try a different PR
- Restart backend and frontend

**Graph too large/slow**
- Expected for 300+ file PRs
- React Flow performance degrades past ~500 nodes
- Consider implementing node collapsing (future work)

## Development Workflow

### Making Changes

1. **Edit components**: Files in `frontend/app/` and `frontend/components/`
2. **Hot reload**: Next.js automatically reloads on save
3. **Check types**: `npm run build` to verify TypeScript
4. **Test locally**: Use example PRs to verify changes

### Adding New Features

**New page:**
```bash
# Create new route
mkdir -p app/new-page
touch app/new-page/page.tsx
```

**New component:**
```bash
# Create in components directory
touch components/NewComponent.tsx
```

**New API endpoint:**
- Add to backend first
- Update frontend API client in `lib/api.ts`
- Add TypeScript types

### Code Style

- Use TypeScript strict mode
- Follow Next.js 14 App Router conventions
- Use `'use client'` only when needed (interactivity)
- Prefer server components for static content
- Use Tailwind CSS classes (no inline styles)
- Keep components focused and small

## Deployment (In Progress)

### Vercel (Frontend)

**Setup:**
1. Push to GitHub
2. Import repository at https://vercel.com/new
3. Configure:
   - Root directory: `frontend`
   - Framework: Next.js (auto-detect)
   - Build command: `npm run build`
   - Output directory: `.next`

**Environment variables:**
```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

### Railway (Backend)

**Setup:**
1. Deploy from GitHub at https://railway.app/new
2. Configure:
   - Root directory: `backend`
   - Build: `pip install -e ".[dev]"`
   - Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Environment variables:**
```
GITHUB_TOKEN=your_github_token
LLM_MODE=bob_pregenerated
FRONTEND_URL=https://your-app.vercel.app
```

**Note:** Deployment is currently in progress. Local development is fully functional.

## Additional Resources

- [Next.js 14 Documentation](https://nextjs.org/docs)
- [React Flow Documentation](https://reactflow.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [IBM Plex Fonts](https://github.com/IBM/plex)

## Support

For issues or questions:
1. Check this documentation
2. Review `README.md` in project root
3. Check `AGENTS.md` for architecture details
4. Review backend API docs at http://localhost:8000/docs
