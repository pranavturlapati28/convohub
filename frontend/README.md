# ConvoHub Frontend

A Next.js + React application for visualizing conversation DAGs using React Flow. This frontend provides an interactive interface for managing threaded conversations with branching and merging capabilities.

## Features

### 🎯 **Core Functionality**
- **Interactive DAG Visualization**: React Flow-based graph with pan/zoom, mini-map, and controls
- **Two-Pane Layout**: 70% flow canvas, 30% inspector panel
- **Real-time Updates**: Server-Sent Events (SSE) for live updates
- **Branch Management**: Create, view, and manage conversation branches
- **Message Handling**: Send messages with inline popover input
- **Merge Operations**: Intelligent branch merging with multiple strategies
- **Diff Visualization**: Compare branches with three-way diff

### 🎨 **UI/UX**
- **Dark Mode**: Optimized for dark theme with proper contrast
- **Responsive Design**: Works on desktop and tablet devices
- **Color-coded Nodes**: System (blue), User (green), Assistant (purple), Merge (amber)
- **Interactive Elements**: Clickable nodes, inline message input, action buttons
- **Visual Feedback**: Loading states, error handling, connection status

### 🔧 **Technical Stack**
- **Next.js 14**: App Router with TypeScript
- **React 18**: Latest React features and hooks
- **React Flow**: Professional graph visualization
- **TailwindCSS**: Utility-first CSS framework
- **shadcn/ui**: High-quality component library
- **React Query**: Server state management and caching
- **Axios**: HTTP client for API communication

## Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn
- ConvoHub backend running on `http://127.0.0.1:8000`

### Installation

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Start the development server**:
   ```bash
   npm run dev
   ```

3. **Open your browser**:
   Navigate to `http://localhost:3000`

### Environment Setup

The application automatically connects to the ConvoHub backend. Make sure:
- Backend is running on `http://127.0.0.1:8000`
- Database is properly configured
- Default admin user exists (`admin@default.local` / `test`)

## Usage

### 1. **Authentication**
- App automatically logs in with default credentials
- Connection status shown in header (green dot = connected)

### 2. **Creating Threads**
- Click "Create Thread" to start a new conversation
- Initial main branch is created automatically

### 3. **Managing Branches**
- **Create Branch**: Click the "+" button on any node
- **Send Message**: Click the message icon to open inline input
- **Select Node**: Click any node to view details in inspector

### 4. **Inspector Panel**
The right panel shows detailed information with tabs:

#### **Messages Tab**
- View all messages in the selected branch
- Color-coded by role (user/assistant/system)
- Timestamps and content preview

#### **Summary Tab**
- Rolling summaries of conversations
- Token counts and content
- Updated automatically after assistant messages

#### **Memory Tab**
- Structured facts extracted from conversations
- Memory types and confidence levels
- Key-value pairs for context

#### **Diff Tab**
- Compare two selected branches
- Three-way diff (memory, summary, messages)
- Merge button for selected branches

### 5. **Branch Operations**
- **Multi-select**: Click two branches to compare
- **Merge**: Use the merge button in diff tab
- **Visual Flow**: Edges show branch relationships

## Architecture

### **Component Structure**
```
src/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout with providers
│   ├── page.tsx           # Main application page
│   └── globals.css        # Global styles
├── components/
│   ├── ui/                # Reusable UI components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   └── tabs.tsx
│   └── flow/              # React Flow components
│       ├── ConversationFlow.tsx
│       ├── MessageNode.tsx
│       └── InspectorPanel.tsx
├── hooks/                 # Custom React hooks
│   ├── useConvoHub.ts     # React Query hooks
│   └── useSSE.ts          # Server-Sent Events
├── lib/                   # Utilities and API
│   ├── api.ts            # API client
│   └── utils.ts          # Helper functions
└── types/                 # TypeScript definitions
    ├── api.ts            # API types
    └── flow.ts           # React Flow types
```

### **State Management**
- **React Query**: Server state, caching, and synchronization
- **Local State**: UI state, selections, and temporary data
- **SSE**: Real-time updates for live collaboration

### **Data Flow**
1. **API Calls**: React Query hooks handle all API communication
2. **State Updates**: Local state updates for immediate UI feedback
3. **Live Updates**: SSE invalidates queries for real-time sync
4. **Optimistic Updates**: UI updates immediately, syncs with server

## API Integration

### **Endpoints Used**
- `POST /v1/auth/login` - Authentication
- `POST /v1/threads` - Create threads
- `POST /v1/threads/{id}/branches` - Create branches
- `POST /v1/branches/{id}/messages` - Send messages
- `POST /v1/merge` - Merge branches
- `GET /v1/diff` - Compare branches
- `GET /v1/context/{id}` - Get conversation context
- `GET /v1/threads/{id}/summaries` - Get summaries
- `GET /v1/threads/{id}/memories` - Get memories

### **Real-time Features**
- **SSE Connection**: `GET /v1/threads/{id}/events`
- **Event Types**: message_created, branch_created, merge_completed
- **Auto-reconnection**: Handles connection drops gracefully

## Development

### **Available Scripts**
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run format       # Format code with Prettier
npm run type-check   # TypeScript type checking
```

### **Code Quality**
- **ESLint**: Strict linting rules
- **Prettier**: Code formatting
- **TypeScript**: Strict type checking
- **React Query DevTools**: Development debugging

### **Customization**

#### **Styling**
- Modify `tailwind.config.js` for theme changes
- Update `globals.css` for custom styles
- Use CSS variables for consistent theming

#### **Components**
- Add new UI components in `components/ui/`
- Extend flow components in `components/flow/`
- Create custom hooks in `hooks/`

#### **API Integration**
- Add new endpoints in `lib/api.ts`
- Create corresponding React Query hooks
- Update TypeScript types as needed

## Deployment

### **Production Build**
```bash
npm run build
npm run start
```

### **Environment Variables**
Create `.env.local` for custom configuration:
```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_SSE_URL=http://127.0.0.1:8000
```

### **Docker Deployment**
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## Troubleshooting

### **Common Issues**

1. **Connection Failed**
   - Check if backend is running on `http://127.0.0.1:8000`
   - Verify database is properly configured
   - Check authentication credentials

2. **SSE Not Working**
   - Ensure backend supports Server-Sent Events
   - Check network connectivity
   - Verify CORS configuration

3. **React Flow Issues**
   - Clear browser cache
   - Check for conflicting CSS
   - Verify node types are properly registered

4. **TypeScript Errors**
   - Run `npm run type-check`
   - Update type definitions if needed
   - Check for missing dependencies

### **Debug Mode**
Enable React Query DevTools for debugging:
- Open browser dev tools
- Look for React Query tab
- Monitor queries and mutations

## Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Add tests if applicable**
5. **Run linting and type checking**
6. **Submit a pull request**

## License

MIT License - see LICENSE file for details.
