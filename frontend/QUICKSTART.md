# ConvoHub Frontend - Quick Start

## 🚀 Get Started in 3 Steps

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start Development Server
```bash
npm run dev
```

### 3. Open Browser
Navigate to `http://localhost:3000`

## 🎯 What You'll See

The application will load in **Demo Mode** with:
- **Two sample branches** with messages
- **Interactive DAG visualization** using React Flow
- **Two-pane layout**: Flow canvas (left) + Inspector panel (right)
- **Color-coded nodes**: User (green), Assistant (purple), System (blue), Merge (amber)

## 🎮 How to Use

### **Left Pane - Flow Visualization**
- **Pan & Zoom**: Use mouse/trackpad to navigate
- **Select Nodes**: Click any node to view details
- **Mini-map**: Bottom-left shows overview
- **Controls**: Bottom-right for zoom/fit

### **Right Pane - Inspector**
- **Messages Tab**: View conversation history
- **Summary Tab**: See conversation summaries
- **Memory Tab**: View extracted facts
- **Diff Tab**: Compare selected branches

### **Node Interactions**
- **Message Icon**: Click to open inline input
- **Plus Icon**: Create new branch from this node
- **Node Selection**: Click to view details

## 🔧 Features Working

✅ **Interactive DAG visualization**  
✅ **Two-pane layout (70%/30%)**  
✅ **Color-coded nodes by role**  
✅ **Inline message input on nodes**  
✅ **Branch creation from nodes**  
✅ **Node selection and inspection**  
✅ **Dark mode design**  
✅ **Responsive layout**  

## 🚧 Demo Mode vs Full Mode

### **Demo Mode (Current)**
- Works without backend
- Sample data included
- All UI features functional
- Console logging for actions

### **Full Mode (With Backend)**
- Real API integration
- Live updates via SSE
- Persistent data storage
- Complete merge/diff functionality

## 🐛 Troubleshooting

### **"Module not found" errors**
```bash
npm install
```

### **TypeScript errors**
```bash
npm run type-check
```

### **Linting issues**
```bash
npm run lint
```

### **Port already in use**
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/                 # Next.js App Router
│   ├── components/          # React components
│   │   ├── ui/             # Reusable UI components
│   │   └── flow/           # React Flow components
│   ├── hooks/              # Custom React hooks
│   ├── lib/                # Utilities and API
│   └── types/              # TypeScript definitions
├── package.json            # Dependencies
├── tailwind.config.js      # Styling configuration
└── tsconfig.json          # TypeScript configuration
```

## 🎨 Customization

### **Styling**
- Modify `tailwind.config.js` for theme changes
- Update `src/app/globals.css` for custom styles

### **Components**
- Add UI components in `src/components/ui/`
- Extend flow components in `src/components/flow/`

### **Data**
- Update sample data in `src/app/page.tsx`
- Add more branches/messages for testing

## 🔗 Next Steps

1. **Explore the UI**: Try clicking nodes, sending messages, creating branches
2. **Check Console**: Open browser dev tools to see action logs
3. **Start Backend**: Run the ConvoHub backend for full functionality
4. **Customize**: Modify components and styling as needed

## 📞 Support

- Check the main README for detailed documentation
- Review the component code for implementation details
- Open browser dev tools for debugging information

---

**Ready to explore!** 🎉
