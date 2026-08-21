# NegoPay Frontend Specification

This is the complete frontend specification for the NegoPay dashboard.
Tech stack: Next.js 14+ (App Router), React 18+, Tailwind CSS, shadcn/ui components.

## 1. Design System

### Color Palette
- **Primary**: Razorpay Blue (#0066FF) — Used for primary buttons, active states, and user message bubbles.
- **Success**: Green (#22C55E) — Used for success toasts, successful payment badges, and positive outcomes.
- **Warning**: Amber (#F59E0B) — Used for deadlocks, warnings, and near-limit mandate states.
- **Error**: Red (#EF4444) — Used for errors, failed payments, and mandate denials.
- **Buyer Agent**: Red (#FF6B6B) — Specific to buyer agent messages, icons, and negotiation bubbles.
- **Seller Agent**: Green (#6BCB77) — Specific to seller agent messages, icons, and negotiation bubbles.
- **Mandate**: Yellow (#FFD93D) — Used for mandate-related UI elements like progress bars.
- **Razorpay**: Blue (#4D96FF) — Used for payment-related UI.
- **Background**: Dark (#0F172A) or Light (#FFFFFF) — Support both themes.
- **Text**: Primary (#F8FAFC on dark, #0F172A on light).

### Typography
- **Font**: Inter (Next.js default) or system font stack.
- **Headings**: semibold, tracking-tight.
- **Body**: regular, text-sm or text-base for readability.
- **Code/Logs**: JetBrains Mono or any monospace font text-xs for audit logs and JSON.

### Component Library (shadcn/ui)
Ensure the following are initialized in the project:
- `Button`, `Card`, `Badge`, `Input`, `ScrollArea`, `Tabs`, `Sheet`, `Dialog`, `Toast`, `Avatar`, `Separator`, `Progress`, `Tooltip`

Custom components to be built on top of these:
- `ChatMessage`, `AgentActivityItem`, `NegotiationBubble`, `MandateBar`, `AuditEvent`, `ProductCard`

---

## 2. Page Layout

### Main Dashboard Layout (Single Page App)
```text
┌─────────────────────────────────────────────────────┐
│  HEADER: NegoPay logo | Merchant selector | Mandate status bar  │
├──────────────────────┬──────────────────────────────┤
│                      │                              │
│   CHAT PANEL         │   ACTIVITY PANEL             │
│   (40% width)        │   (60% width)                │
│                      │                              │
│   - Message list     │   Tabs:                      │
│   - Typing indicator │   [Activity] [Negotiation]   │
│   - Input box        │   [Audit] [Mandate]          │
│                      │                              │
│                      │                              │
│                      │                              │
│                      │                              │
├──────────────────────┴──────────────────────────────┤
│  FOOTER: Connection status | Daily spend | Razorpay badge         │
└─────────────────────────────────────────────────────┘
```

---

## 3. Component Specifications

### 3.1 Header (`components/layout/Header.tsx`)
- **NegoPay Logo**: Text-based, stylized with Primary color. Link to root.
- **Merchant Selector**: shadcn `Select` component. Options: 'TechMart', 'SoundStore', 'BookHaven', 'All Merchants'. Controls context for manual overrides or specific testing.
- **Mandate Status Pill**: A `Badge` or small `Card` showing remaining daily budget (e.g., '₹3,901 / ₹5,000 remaining'). Turns Warning (Amber) if < 20% remaining, Error (Red) if 0.
- **Connection Status**: Small SVG circle (Green = WebSocket connected, Red = Disconnected, Amber = Connecting).

### 3.2 Chat Panel (`components/chat/ChatPanel.tsx`) (Left Side, 40%)
- **Message List (`components/chat/ChatMessage.tsx`)**: Scrollable `ScrollArea`. 
  - **User Messages**: Right-aligned, blue background (`bg-blue-600`), white text.
  - **Agent Messages**: Left-aligned, dark/gray background (`bg-slate-800`), white text.
  - **Structured Content**:
    - **Product Cards**: Inline `Card` with image, title, price (₹), stock status.
    - **Comparison Tables**: Rendered as simple markdown or a grid component.
    - **Action Confirmations**: E.g., "Order created: #order_KjHG83" with a Razorpay link icon.
    - **Error Messages**: Red border/accent, clear recovery options.
  - **Typing Indicator (`components/chat/TypingIndicator.tsx`)**: Animated dots (bounce) when `isProcessing` is true.
- **Input Area (`components/chat/ChatInput.tsx`)**: 
  - `Input` field (placeholder: 'Tell NegoPay what to buy...').
  - Send `Button` (Primary icon).
  - Voice input button (Microphone icon using Web Speech API).
  - Quick action chips below input: `Badge` components wrapped in a flex row ('Buy earbuds', 'Check my orders').

### 3.3 Activity Panel (`components/activity/ActivityPanel.tsx`) (Right Side, 60%)
Uses shadcn `Tabs` component.

#### Tab 1: Activity Feed (`components/activity/ActivityFeed.tsx`)
- Real-time feed via WebSocket.
- **Activity Item (`ActivityItem.tsx`)**:
  - Timestamp (`text-xs text-muted-foreground`).
  - Avatar: Buyer (Red robot), Seller (Green robot), System (Blue gear).
  - Description string.
  - Status `Badge`: pending (⏳), success (✅), failed (❌), warning (⚠️).
  - Expandable `Collapsible`: Shows raw JSON of MCP tool call.
- Behavior: Auto-scroll to bottom on new event using a React ref.

#### Tab 2: Negotiation (`components/negotiation/NegotiationView.tsx`)
- Displays current active negotiation state.
- **Negotiation Bubble (`NegotiationBubble.tsx`)**:
  - Buyer: Left-aligned, red border/accent.
  - Seller: Right-aligned, green border/accent.
  - Content: Offer text, highlighted price, expandable reasoning (italic).
  - Round Badge: e.g., "Round 1/3".
- **Progress Bar (`NegotiationProgress.tsx`)**: shadcn `Progress` (rounds used / max rounds).
- **Outcome Badge**: DEAL ✅ | DEADLOCK ⚠️ | WALKING AWAY 🚶.

#### Tab 3: Audit Trail (`components/audit/AuditTrailView.tsx`)
- **Filters (`AuditFilters.tsx`)**: Select dropdowns for Event Type and Agent, DatePicker for Time range.
- **Table/List**: Column headers (Time, Type, Agent, Summary).
- **Row Expansion**: Clicking row opens full JSON event data formatted with `pre` and `code`.
- **Export**: Button triggers a file download of current filtered list as `audit.json`.

#### Tab 4: Mandate (`components/mandate/MandatePanel.tsx`)
- **Current Configuration**:
  - Read-only view of Per-transaction limit, Daily limit.
  - Allowed/Blocked categories shown as flex-wrapped `Badge`s.
  - Auto-approve / Require-approval thresholds.
- **Visualizations (`SpendingBar.tsx`)**:
  - `Progress` bar showing daily spend. Color shifts green -> yellow -> red.
  - Recent transactions list (amount, category, timestamp).
- **Edit Modal (`MandateEditor.tsx`)**: shadcn `Dialog` with a form to update limits and categories.

### 3.4 Footer (`components/layout/Footer.tsx`)
- Simple flex container, `border-t`.
- Connection Status (text + dot).
- Daily spend text summary.
- Razorpay Test Mode branding.

---

## 4. Interactive Flows

### Flow 1: Happy Path Purchase
1. User types in `ChatInput` and submits.
2. `ChatMessage` renders user text.
3. `TypingIndicator` renders.
4. `ActivityFeed` streams updates: Parsing intent -> Searching -> Found -> Negotiating.
5. `Tabs` switches to or highlights Negotiation tab.
6. `NegotiationView` populates rounds in real-time.
7. Deal reached -> `ActivityFeed` logs Mandate Check.
8. Payment processed -> shadcn `Toast` success notification.
9. `ChatMessage` renders order confirmation `ProductCard`.
10. `MandatePanel` updates spend state globally.

### Flow 2: Mandate Denial
1. Agent attempts purchase over limit.
2. `ActivityFeed` logs "Mandate check: ❌ DENIED".
3. `ChatMessage` renders error/denial explanation.
4. `MandatePanel` icon/tab flashes briefly using CSS keyframes.

### Flow 3: Negotiation Deadlock
1. `NegotiationView` reaches max rounds. `Progress` is 100%.
2. DEADLOCK badge shown.
3. `ActivityFeed` shows fallback logic (checking alternative merchants).

### Flow 4: Payment Failure
1. `ActivityFeed` logs "Payment attempt 1: ❌ BANK_SERVER_ERROR".
2. Error `Toast` shown with "Retrying...".
3. Success on retry -> Success `Toast` and `ActivityFeed` updates.

---

## 5. Responsive Behavior
- **Desktop (>1024px)**: 40/60 Split Layout using CSS Grid/Flex.
- **Tablet (768-1024px)**: Chat Panel 100% width. Activity Panel accessible via a right-side shadcn `Sheet`.
- **Mobile (<768px)**: Chat full screen. Activity panel via bottom navigation tabs or bottom `Sheet`.

---

## 6. State Management
Zustand is recommended for modular global state:
- **chatStore**: `messages`, `isProcessing`, `sendMessage()`.
- **activityStore**: `events`, `addEvent()`.
- **negotiationStore**: `rounds`, `status`, `maxRounds`.
- **mandateStore**: `config`, `dailySpend`, `updateConfig()`.
- **systemStore**: `wsConnected`, `activeMerchant`.

---

## 7. API Integration (Endpoints)
- `POST /api/chat`: Send user message, receive streamed agent response.
- `GET /api/merchants`: List merchants for selector.
- `GET /api/mandates/{id}`: Get current mandate state.
- `PUT /api/mandates/{id}`: Update mandate config.
- `GET /api/audit?session={id}&type={type}`: Query audit events.
- `GET /api/negotiations/{id}`: Get negotiation transcript.
- `WebSocket /ws/agent-activity`: Real-time event stream.

---

## 8. Component File Structure

```text
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   └── globals.css
├── components/
│   ├── layout/
│   │   ├── Header.tsx
│   │   ├── Footer.tsx
│   │   └── SplitLayout.tsx
│   ├── chat/
│   │   ├── ChatPanel.tsx
│   │   ├── ChatMessage.tsx
│   │   ├── ChatInput.tsx
│   │   ├── TypingIndicator.tsx
│   │   ├── ProductCard.tsx
│   │   └── OrderConfirmation.tsx
│   ├── activity/
│   │   ├── ActivityPanel.tsx
│   │   ├── ActivityFeed.tsx
│   │   ├── ActivityItem.tsx
│   │   └── ActivityDetail.tsx
│   ├── negotiation/
│   │   ├── NegotiationView.tsx
│   │   ├── NegotiationBubble.tsx
│   │   ├── NegotiationProgress.tsx
│   │   └── NegotiationOutcome.tsx
│   ├── audit/
│   │   ├── AuditTrailView.tsx
│   │   ├── AuditEventRow.tsx
│   │   ├── AuditFilters.tsx
│   │   └── AuditExport.tsx
│   ├── mandate/
│   │   ├── MandatePanel.tsx
│   │   ├── MandateEditor.tsx
│   │   ├── SpendingBar.tsx
│   │   └── CategoryBadges.tsx
│   └── shared/
│       ├── AgentAvatar.tsx
│       ├── StatusBadge.tsx
│       ├── PriceBadge.tsx
│       └── TimeStamp.tsx
├── hooks/
│   ├── useWebSocket.ts
│   ├── useChat.ts
│   ├── useMandate.ts
│   └── useAudit.ts
├── lib/
│   ├── api.ts
│   ├── types.ts
│   ├── constants.ts
│   └── utils.ts
└── stores/
    ├── chatStore.ts
    ├── activityStore.ts
    ├── mandateStore.ts
    └── negotiationStore.ts
```
