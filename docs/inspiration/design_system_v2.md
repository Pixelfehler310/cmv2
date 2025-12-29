# Civic OS Design System V2: "Friendly Functionalism"

> **Version:** 2.1.0 ("Kurzgesagt Vision")
> **Status:** **Evolutionary Core** > **Philosophy:** Flat Design 2.0 + Kurzgesagt Storytelling Logic.
> **Directives:** Vibrant Clarity, Geometric Optimism, Fluid Feedback.

---

## 1. The Core Philosophy: Friendly Functionalism

### 1.1 The Definition

"Friendly Functionalism" is the synthesis of two opposing but complementary design schools:

1.  **Neo-Swiss (The Skeleton):** We rely on strict grids, mathematical whitespace, and objective clarity. This ensures the user never gets lost. The app feels like a precise tool—reliable, robust, and predictable.
    - _Keywords:_ Grid, Align, Neutral, Structured, Reliable.
2.  **Humanist Tech (The Soul):** We soften the rigor with organic curvature, warm interactions, and vibrant, semantic color. This ensures the user feels welcome. The app feels like a living room—safe, inviting, and alive.
    - _Keywords:_ Warm, Curved, Tactile, Playful, Forgiving.

### 1.2 The "Timeless" Directive

We reject fleeting trends.

- **No Glassmorphism:** We do not use excessive blur overlays that cause performance drags and accessibility contrast issues. We use solid surfaces with optimal contrast.
- **No Skeuomorphism:** We do not fake leather or wood.
- **Our Path (Flat Design 2.0):** We use **"Functional Vibrancy"**. A button looks pressable because of its color mass and "bounce" capability. We embrace **Kurzgesagt-style gradients**—subtle, high-saturation shifts that add depth without needing 3D textures. A card lifts via soft shadows, establishing a clear Z-index hierarchy that feels like paper layers.

### 1.3 The "Digital Living Room" Metaphor

The UI is not a "cockpit" (stressful, complex) nor a "billboard" (shouting, selling). It is a **Living Room**.

- **The Walls (Structure):** Neutral, calm, sturdy. (White/Black backgrounds).
- **The Furniture (Components):** Comfortable, usable, distinct. (Soft cards, pill buttons).
- **The Art (Content):** Vibrant, personal, meaningful. (User generated content, maps, illustrations).

---

## 2. Typography: The Voice of Civic

### 2.1 The Typeface: Plus Jakarta Sans

We utilize a **Single Typeface System**. This reduces cognitive load and strengthens our brand identity.
**Why Plus Jakarta Sans?**
It is a geometric sans-serif (like the Swiss style) but features distinct "Humanist" qualities:

- **The 'a' and 'g':** They are double-story, which improves readability and adds a playful, friendly character compared to the cold single-story shapes of Helvetica or Futura.
- **The x-height:** High x-height ensures superior readability on small mobile screens.
- **The spacing:** Open apertures prevent letters from visually merging at small sizes.

### 2.2 The Type Scale (Mathematical Hierarchy)

We use a **Minor Third (1.2)** ratio to ensure harmonious scaling.

| Token          | Size / Line Height | Weight          | Character Spacing | Usage                            |
| :------------- | :----------------- | :-------------- | :---------------- | :------------------------------- |
| **Display XL** | 32px / 120%        | ExtraBold (800) | -0.02em           | Hero Headlines, "Quest Complete" |
| **Display L**  | 28px / 120%        | Bold (700)      | -0.01em           | Section Headers                  |
| **Heading M**  | 24px / 130%        | Bold (700)      | 0                 | Card Titles, Modal Headers       |
| **Heading S**  | 20px / 140%        | SemiBold (600)  | 0                 | Subsection Titles                |
| **Body L**     | 18px / 160%        | Medium (500)    | 0                 | Lead Introductory Text           |
| **Body M**     | 16px / 160%        | Regular (400)   | 0                 | **Default Reading Text**         |
| **Label L**    | 16px / 100%        | Bold (700)      | +0.01em           | **Button Labels**                |
| **Label M**    | 14px / 120%        | SemiBold (600)  | +0.01em           | Metadata, Input Labels           |
| **Label S**    | 12px / 120%        | Medium (500)    | +0.02em           | Captions, Timestamps             |

### 2.3 Typographic Rules

1.  **Left Align Everything:** Centered text is harder to read. We imply structure through strong left alignment lines.
2.  **Color for Context:**
    - **Primary Text:** `gray-900` (Never pure black `#000000` - too harsh).
    - **Secondary Text:** `gray-500` (For descriptions).
    - **Interactive Text:** Brand Color (e.g., Purple link).
3.  **No All-Caps:** Avoid shouting. Use Sentence case for friendliness.

---

## 3. The Unified Color Palette: "The Civic Prism"

### 3.1 The Philosophy of Color

We operate on a **"Strict Neutral / Vibrant Signal"** split.

- **90% of the UI** is Monochrome (Slate/Zinc) for high legibility.
- **10% of the UI** is high-octane **Kurzgesagt Signal Color**.
- **The Gradient Rule:** Significant UI elements (Primary Buttons, Hero Headers, Active Badges) should use a **2-point linear gradient** (e.g., `primary-500` to `primary-600`) at 135° to mimic the depth of Kurzgesagt illustrations.

### 3.2 The Neutral Foundation (The Canvas)

We use **Slate** (Cool Grey) to maintain a crisp, technological feel.

| Token         | Metric Value | Usage                             |
| :------------ | :----------- | :-------------------------------- |
| `Canvas-0`    | `#FFFFFFFF`  | Global Background (Light)         |
| `Canvas-50`   | `#F8FAFC`    | Section Backgrounds / App Shell   |
| `Surface-100` | `#F1F5F9`    | **Input Fields**, Secondary Cards |
| `Surface-200` | `#E2E8F0`    | Dividers, Disabled States         |
| `Text-500`    | `#64748B`    | Secondary Text, Icons             |
| `Text-900`    | `#0F172A`    | Primary Text                      |
| `Dark-Canvas` | `#020617`    | Global Background (Dark)          |
| `Dark-Surf`   | `#1E293B`    | Cards (Dark)                      |

### 3.3 The Semantic Activity Spectrum (The Soul)

Every activity type has a **Dedicated Primary Color**. This allows users to scan a feed map and instantly understand context without reading text.

#### A. GAMING (High Energy / E-Sports)

- **Role:** Competitive Gaming, Tournaments, LAN Parties.
- **Color Family:** **Rally Red**.
- **Vibe:** Adrenaline, Alert, Power.
  - `Gaming-50`: `#FEF2F2` (Bg tint)
  - `Gaming-100`: `#FEE2E2`
  - `Gaming-500`: `#EF4444` (**Primary**)
  - `Gaming-600`: `#DC2626` (Hover)
  - `Gaming-900`: `#7F1D1D` (Text)

#### B. ACTION / SYSTEM ALERT (Critical)

- **Role:** Raids, Time-Sensitive Protests, System Errors, "Join Now or Miss Out".
- **Color Family:** **Cyber Pink**.
- **Vibe:** Urgency, Disruption, Notice.
  - `Alert-50`: `#FDF2F8`
  - `Alert-500`: `#EC4899` (**Primary**)
  - `Alert-900`: `#831843`

#### C. SOCIAL (Warmth / Connection)

- **Role:** Coffee, Picnics, Just Chatting, Board Games.
- **Color Family:** **Civic Orange**.
- **Vibe:** Friendly, Safe, Warm.
  - `Social-50`: `#FFF7ED`
  - `Social-500`: `#F97316` (**Primary**)
  - `Social-900`: `#7C2D12`

#### D. NATURE (Growth / Civic Duty)

- **Role:** Gardening, Cleanups, Sustainability, Quests.
- **Color Family:** **Forest Emerald**.
- **Vibe:** Calm, Growth, Positive.
  - `Nature-50`: `#ECFDF5`
  - `Nature-500`: `#10B981` (**Primary**)
  - `Nature-900`: `#064E3B`

#### E. NIGHTLIFE (Vibrancy / Party)

- **Role:** Clubbing, Bars, Festivals, "Hangout With Me".
- **Color Family:** **Electric Cyan**.
- **Vibe:** Electric, Neon, Night-time.
  - `Night-50`: `#ECFEFF`
  - `Night-500`: `#06B6D4` (**Primary**)
  - `Night-900`: `#164E63`

#### F. SPORTS (Activity / Motion)

- **Role:** Jogging, Football, Yoga, "Get Fit With Me".
- **Color Family:** **Volt Lime**.
- **Vibe:** High-Vis, Sporty, energetic.
  - `Sport-50`: `#F7FEE7`
  - `Sport-500`: `#84CC16` (**Primary**)
  - `Sport-900`: `#365314`

#### G. MUSIC / CREATIVITY (Flow / Art)

- **Role:** Jam Sessions, Art Workshops, Maker Spaces.
- **Color Family:** **Studio Violet**.
- **Vibe:** Creative, Deep, Artistic.
  - `Music-50`: `#F5F3FF`
  - `Music-500`: `#8B5CF6` (**Primary**)
  - `Music-900`: `#4C1D95`

#### H. DEMOCRACY / OFFICIAL (Trust)

- **Role:** Voting, Town Halls, Citizen Feedback.
- **Color Family:** **Diplomatic Blue**.
- **Vibe:** Official, Trustworthy, Serene.
  - `Trust-50`: `#F0F9FF`
  - `Trust-500`: `#0EA5E9` (**Primary**)
  - `Trust-900`: `#0C4A6E`

---

## 4. The Unified Component Library (The Lego Bricks)

### 4.1 Buttons: The "Solid Pill"

We do not use gradients. We do not use outlines for primary actions. We use pure color mass.

- **Shape:** Full Pill (`rounded-full`).
- **Height:** 56px (Large/Primary) or 48px (Medium). **Target Size matters.**
- **Visuals:** Kurzgesagt Gradient (135° top-left to bottom-right).
- **Interaction:**
  - _Hover:_ Slight scale up (102%) + shadow intensity increase (The "Engage" state).
  - _Active (Press):_ "The Boing" - Scale down to 94% with a high-tension spring effect.
- **Shadow:** `shadow-lg` using the button's primary color at 20% opacity (Glow Effect).
- **Label:** Plus Jakarta Sans Bold, White Text.

### 4.2 Inputs: The "Tactile Field"

Inputs should feel like physical slots you place information into.

- **Background:** `Surface-100` (`#F1F5F9`). **We do not use white backgrounds with borders.**
- **Shape:** `rounded-2xl` (16px). Slightly squarer than buttons to differentiate "Action" (Round) from "Data" (Squared).
- **Height:** 56px.
- **Focus State:** A thick, 2px ring of the _Current App's Primary Color_.
- **Labeling:** Input labels are outside the field, Top-Left, `Label M` size.

### 4.3 Cards: The "Borderless Surface"

A card defines a distinct piece of content.

- **Background:** White (`#FFFFFF`) on Light Mode. Dark Surface (`#1E293B`) on Dark Mode.
- **Border:** **0px**. No grey hairlines.
- **Separation:** Separation is achieved via **Contrast** against the definition `Canvas-50` background.
- **Shadow:** `shadow-sm` (Y-offset 1px, Blur 2px, Color Black/5%). Minimal lift.
- **Interaction:** On press, the card scales to 98% and shadow vanishes.
- **Border Radius:** `rounded-3xl` (24px). Friendly, soft corners.

### 4.4 The "Frame" (Global Layout)

Every screen follows the same architectural frame.

- **Safe Area:** 16px lateral padding.
- **Top Bar:** Minimal height 64px. Contains Page Title (Left) and Actions (Right).
- **Bottom Anchor:** The **Super Nav** area (80px height reserved at bottom).

---

## 5. Product UI Patterns: One System, Distinct Dialects

We strictly enforce consistency in components (buttons, type) but allow **Layout Dialects** to serve the specific needs of each distinct product.

### 5.1 Quest UI Pattern: "Map-First"

- **Goal:** Exploration of physical space.
- **Primary Surface:** The Map is the background of the _entire_ screen. There is no white canvas.
- **Layering:**
  - _Layer 0:_ Map Tiles (Darkened/Muted to let pins pop).
  - _Layer 1 (Pins):_ 48px Circles with Icons. Colors map directly to the Semantic Spectrum (Red=Game, Green=Nature).
  - _Layer 2 (Floating Controls):_ Glass-backed pills for Filters (Top) and Scan (Top Right).
  - _Layer 3 (Drawers):_ Bottom sheets that slide up to reveal details without leaving the map context.
- **Specific Interaction:** **"Scan-to-Unlock"**. The Scan button is the primary action, always accessible thumb-zone Top Right or Floating Bottom Right.

### 5.2 Connect UI Pattern: "Stream-First"

- **Goal:** High-velocity consumption of social signals.
- **Primary Surface:** A vertical scroll view.
- **The Signal Card Architecture:**
- **Header Strip:** Kurzgesagt Gradient Block (e.g., Red-500 to Red-600) containing the Icon + Activity Name.
- **Media Body:** Flat illustrations with thick 2px strokes and inner gradients.
- **Action Row:** "Chunky" avatar pile + Large "Join" button with "Boing" interaction.
- **Rhythm:** Heavy use of vertical spacing (24px gap) to let each signal breathe like a frame in a storyboard.

### 5.3 Love UI Pattern: "Read-First"

- **Goal:** Slowing down the user. Encouraging reading over judging.
- **Primary Surface:** A single-column text/media mix.
- **The "Anti-Swipe" Scroll:**
  - **Logic:** Standard vertical scrolling. You must physically move the screen to see more info.
- **The "Vibe-Slide" Module:**
  - Instead of "Left/Right" buttons, we use a **Horizontal Slider** pinned to the bottom.
  - _Rest State:_ Knob in center.
  - _Reject:_ Drag Left (Resistance increases, background turns Grey).
  - _Vibe:_ Drag Right (Snaps satisfyingly, background turns Burgundy, Haptic heavy tick).
  - _Rationale:_ Dragging requires more conscious effort than tapping, enforcing "Mindful Dating".

### 5.4 Life UI Pattern: "Grid-First"

- **Goal:** High density of utility information. A "Cockpit" for city life.
- **Primary Surface:** Masonry Grid (2-column).
- **The Widget Module:**
  - **Aspect Ratio:** Square (1:1) or Rectangular (2:1).
  - **Content:** Large Data Point (e.g., "08:00") + Small Label ("Trash Pickup").
  - **Visuals:** High contrast icons on tinted backgrounds (`bg-teal-50` for Life).
- **The "City Key":** A skeuomorphic nod. A card that physically "flips" on tap to reveal the QR code, mimicking a real ID card's tactile nature.

---

## 6. Accessiblity Standards (The Foundation)

### 6.1 Contrast Ratios

- We target **WCAG AA+** (4.5:1 for normal text).
- **Semantic Problem:** Neon Yellow or Cyan text on white is unreadable.
- **Solution:** We use the `-900` shade of the semantic color for text, and `-500` only for backgrounds/icons.
  - _Bad:_ Cyan-500 text on White.
  - _Good:_ Cyan-900 text on Cyan-50 background.

### 6.2 Touch Targets

- **Minimum Size:** 48x48px. No exception.
- **Spacing:** Minimum 8px between interactive elements to prevent "Fat Finger" errors.

### 6.3 Motion Sensitivity

- All animations (Bubble float, drawers) must respect `prefers-reduced-motion`.
- If enabled, bubbles stop floating; transitions become instant fades.

---

## 7. Dark Mode Strategy: "True Black vs Deep Blue"

- **Approach:** We do not use pure black (`#000000`) as it causes "smearing" on OLED screens and eye strain.
- **Our "Dark":** `Slate-950` (`#020617`). A very deep, rich navy-black.
- **Elevation in Dark Mode:**
  - We do not use shadows (invisible on black).
  - We use **Lightness Adjustment**.
  - _Background:_ Level 0.
  - _Card:_ Level 1 (Lighter).
  - _Modal:_ Level 2 (Lightest).

---

## 8. Summary of Tokens (Quick Reference)

### Radius

- `rounded-sm`: 4px (Checkboxes)
- `rounded-md`: 8px (Small tags)
- `rounded-2xl`: 16px (Inputs, Inner Cards)
- `rounded-3xl`: 24px (Main Cards, Drawers)
- `rounded-full`: 9999px (Buttons, Avatars)

### Spacing (The 4pt Grid)

- `gap-1`: 4px
- `gap-2`: 8px
- `gap-3`: 12px
- `gap-4`: 16px (Base Unit)
- `gap-6`: 24px (Section Gap)
- `gap-8`: 32px (Major Section Gap)
- `gap-12`: 48px (Page Gap)

### Shadows

- `shadow-sm`: `0 1px 2px 0 rgb(0 0 0 / 0.05)` (Cards)
- `shadow-lg`: `0 10px 15px -3px rgb(0 0 0 / 0.1)` (Floating Elements)
- `shadow-glow`: Colored shadow based on parent color (Used sparingly for "Active" states).

---

> **Design Sign-off:**
> This document represents the approved visual language for Civic OS. All UI implementation must adhere strictly to these token definitions. "Close enough" is not good enough.
