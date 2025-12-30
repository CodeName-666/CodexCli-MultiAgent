# Component 1: User Profile Card

## Goal
Design a modern user profile card component with avatar, bio, and social links

## Allowed paths
- designs/components/profile_card.figma
- designs/components/profile_card.md
- assets/icons/social_*.svg

## Requirements
- Avatar with status indicator (online/offline)
- User name and role badge
- Expandable bio section (max 280 chars)
- Social media links (GitHub, LinkedIn, Twitter)
- Responsive design (mobile & desktop)
- Dark mode support

## Design Specifications
- **Colors:** Primary (#3B82F6), Secondary (#8B5CF6), Background (#F9FAFB)
- **Typography:** Inter font, 14px body, 18px headings
- **Spacing:** 8px grid system
- **Border Radius:** 12px for card, 50% for avatar
- **Shadow:** 0 4px 6px rgba(0,0,0,0.1)

## Deliverables
- Figma component with variants (default, hover, active)
- Design spec document (Markdown)
- Icon assets (SVG)
- Accessibility notes (ARIA labels, contrast ratios)

---

# Component 2: Data Visualization Dashboard

## Goal
Create an interactive dashboard for displaying analytics data with charts and metrics

## Allowed paths
- designs/components/dashboard.figma
- designs/components/dashboard.md
- assets/charts/*.svg

## Requirements
- KPI metric cards (4 cards in grid)
- Line chart for trends (7-day view)
- Bar chart for comparisons
- Responsive layout (1 col mobile, 2x2 desktop)
- Interactive tooltips on hover
- Customizable color themes

## Design Specifications
- **Colors:** Success (#10B981), Warning (#F59E0B), Error (#EF4444), Info (#3B82F6)
- **Chart Style:** Smooth curves, gradient fills, animated transitions
- **Grid:** 4-column grid on desktop, 1-column on mobile
- **Spacing:** 16px padding, 24px gaps
- **Typography:** Tabular numbers for metrics

## Deliverables
- Dashboard layout in Figma
- Chart component library
- Design tokens (colors, spacing, typography)
- Interaction states (hover, active, loading)

---

# Component 3: Navigation Menu

## Goal
Design a responsive navigation menu with multi-level hierarchy and search

## Allowed paths
- designs/components/navigation.figma
- designs/components/navigation.md
- assets/icons/nav_*.svg

## Requirements
- Top-level navigation (6-8 items)
- Dropdown menus for sub-items (max 2 levels)
- Search bar with autocomplete
- Mobile hamburger menu
- Active state indicators
- Notification badges

## Design Specifications
- **Layout:** Horizontal on desktop, vertical drawer on mobile
- **Height:** 64px on desktop, full-screen on mobile
- **Colors:** Nav background (#1F2937), Active (#3B82F6), Hover (#374151)
- **Icons:** 24x24px, outlined style
- **Animation:** 200ms ease-in-out for dropdowns

## Deliverables
- Navigation component with all states
- Mobile menu variant
- Icon set (navigation icons)
- Animation specs
- Keyboard navigation guidelines
