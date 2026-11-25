# GamerzDen Manager V8 — PRD

## Original Problem Statement
Professional offline gaming café management system (single-file HTML/CSS/JS + LocalStorage) for a café with 5 gaming stations: 4 Regular PCs + 1 Steering Wheel/Racing Station + 2 PS5 consoles. Plus QR-code mobile food ordering, dues tracking, custom passes, and full billing suite.

## Architecture
- **Main file**: `/app/frontend/public/GamerzDen_Manager_V8.html` (single monolithic HTML — 5000+ lines)
- **QR mobile menu**: `/app/frontend/public/menu.html`
- **Backend (QR relay)**: `/app/backend/server.py` (FastAPI)
- **Persistence**: LocalStorage (offline-first)
- **Runtime**: Pure vanilla JS, no build tools, no CDN
- **Icons**: Inline SVG (offline-safe)

## LocalStorage Keys
`gd_settings`, `gd_systems`, `gd_active`, `gd_history`, `gd_reports`, `gd_currentDay`, `gd_foodMenu`, `gd_categories`, `gd_partners`, `gd_partnerPaidAt`, `gd_partnerAdjustments`, `gd_stock`, `gd_stockHistory`, `gd_customers`, `gd_dues`, `gd_passes`, `gd_tabs`, `gd_billSeq`, `gd_calcHistory`, `gd_theme`

## Stations (hardcoded)
- PC 1, PC 2, PC 3, PC 4  (Regular PC)
- Steering Wheel  (STEERING type — flat ₹200/hr)
- PS5-1, PS5-2  (PS5 with 1/2/Extra controller)

## Pricing (all editable in Settings)
- **PC**: ₹120/hr ≤5h · ₹100/hr @ 5h+ (tiered)
- **Steering Wheel**: ₹200/hr flat (no tier)
- **PS5**: 1 ctrl ₹100/hr · 2 ctrl ₹180/hr · Extra ctrl ₹100/hr
- **Day Pass**: ₹600 · **Night Pass**: ₹800
- **Custom Pass** default: ₹2,999 / 30 days / 60 hours (fully customizable per sale)
- New sessions use latest price; existing/completed sessions keep their `priceSnapshot`

## Feature Matrix

### ✅ Implemented (Phase 1 + 2 — Feb 2026)
- [x] Sidebar per PRD 16 (Dashboard · Active Sessions · Session History · Customers · Billing · Due Payments · Food Menu · Food Orders · Food Vendors · In-House Stock · QR Orders · QR Management · Passes · Reports · Calculator · Settings)
- [x] Steering Wheel replaces PC 5 (type=STEERING, flat ₹200/hr)
- [x] PS5 Extra Controller option (1/2/Extra)
- [x] Dashboard rewritten: Total Billed / Received / Due / Earnings / Food Profit / Active Sessions / Active Food Orders / Low Stock / Peak Hours / Most Used Stations / Recent Transactions / Recent Orders / Live station status
- [x] Earnings logic per PRD 13: Gaming Earnings + Food Profit (sell − vendor cost) = GamerzDen Earnings
- [x] Payment methods: Cash, UPI, Card, Split, Due
- [x] Combined Billing (PRD 7): tabs across PC + PS5 + Steering + Food + Manual + Discount → one unified receipt
- [x] Sessions can attach to Combined Bills (or stand alone)
- [x] Customers directory with auto-upsert on session start
- [x] Custom / Monthly Passes (PRD 11-12): prepaid hours, deducts on custompass sessions, statuses Active/Expired/Exhausted, rolls over until expiry
- [x] Due Payments (PRD 9): mark bills as Due · Collect payment page · Cash/UPI/Card partial or full · statuses Due/Partial/Paid/Cancelled · survives End Day
- [x] Calculator on dedicated page with keyboard support, history, copy result (PRD 10)
- [x] Business info (café name, contact, address) on receipts (PRD 15)
- [x] Receipts hide vendor cost / partner cost / internal notes (PRD 14)
- [x] Bill numbering (GD-1001+ sequence)
- [x] End Day retains: active sessions, open tabs, unpaid dues (PRD 17)
- [x] Price snapshot per session (existing sessions keep original prices when Settings change) (PRD 3)

### 🟢 Retained from V1
- [x] Session lifecycle: Start / Pause / Resume / Extend / End
- [x] Food menu with categories, partners (vendors), variants
- [x] Food ordering into session (walk-in + attached)
- [x] Partner-cost tracking for accurate profit split
- [x] Stock management (In-House Stock) with auto/manual status badges
- [x] Stock history log
- [x] QR-code food ordering (mobile menu.html)
- [x] Backend polling for live orders
- [x] Export/Import JSON backup
- [x] Dark/Light theme toggle
- [x] Print QR sheets

## Data Model (extended)
```js
system: { id, name, type: 'PC'|'PS5'|'STEERING', status, sessionId }
session: { id, customerName, systemId, systemName, systemType, controllers(1|2|3), slot, paymentMethod, startTime, foodItems, tabId?, passId?, priceSnapshot, extendedHours, pausedAt, pausedTotal }
history: session + { billNumber, endTime, duration, baseAmount, foodAmount, breakdown, bill, discount, paymentMethod, cash, upi, card, billStatus:'paid'|'partial'|'due', dueAmount, isWalkIn, isCombined?, tabId?, closedSessions?, usedPass? }
customer: { id, name, phone, notes, visits, spent, due, createdAt }
tab: { id, customerName, status:'open'|'closed'|'cancelled', sessions:[id], closedSessions:[frozenSession], foodItems, manualCharges:[{label, amount}], discount, notes, createdAt, closedAt? }
due: { id, billNumber, historyId, customerName, amount, collected, status:'due'|'partial'|'paid'|'cancelled', payments:[{amount, method, at}], createdAt }
pass: { id, billNumber, customerName, passName, pricePaid, validityDays, totalHours, usedHours, status:'active'|'exhausted'|'expired'|'cancelled', startDate, expiryDate, paymentMethod }
settings: { pcNormal, pcAfter5, ps5one, ps5two, ps5extra, steering, dayPass, nightPass, customPass:{name,price,validityDays,hours}, business:{cafeName,contact,address} }
```

## Backlog / Future (Phase 3+)
- Manual controller conflict check on PS5 sessions (currently only occupancy blocked)
- Real-time collaborative multi-device sync (currently LocalStorage silo)
- Automated email/SMS receipts
- Cash drawer reconciliation
- Employee logins & shift reports
- Full loyalty program

## Test Credentials
No auth — offline single-user app.

## Manual Verification (Feb 2026)
- Combined Bill for Rahul (PC 1, 1h) shows ₹120 ✓
- Steering Wheel for Priya (2h) → ₹400 flat ✓
- Custom Pass ₹2999 sold to Amit → reflected as ₹2,999 in Billed/Received/Earnings ✓
- Calculator 5+3=8 with keyboard ✓
- Sidebar has all 16 PRD nav items ✓
- Dashboard tiles match PRD 2 ✓
- All settings save/load correctly ✓
