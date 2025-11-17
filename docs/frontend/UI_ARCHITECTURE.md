# FoodFlow OS: UI/Frontend Architecture

**Document Version:** 1.0  
**Last Updated:** November 16, 2025  
**Author:** Manus AI  
**Status:** Production-Ready

---

## Table of Contents

1. [Frontend Overview](#frontend-overview)
2. [Technology Stack](#technology-stack)
3. [Application Structure](#application-structure)
4. [Component Library](#component-library)
5. [Page Layouts](#page-layouts)
6. [State Management](#state-management)
7. [API Integration](#api-integration)
8. [Authentication Flow](#authentication-flow)
9. [Routing Structure](#routing-structure)
10. [Theme & Design System](#theme--design-system)

---

## Frontend Overview

FoodFlow OS uses a **modern, enterprise-grade frontend stack** built with Next.js 15, React 19, and Refine framework. The UI is designed for food industry professionals (quality managers, production supervisors, supply chain analysts) with a focus on data visualization, real-time monitoring, and AI-powered insights.

### Design Principles

**1. Data-First Interface**

The UI prioritizes data visualization and actionable insights over decorative elements. Every screen is designed to help users make faster, better decisions.

**2. Mobile-Responsive**

All interfaces work seamlessly on desktop (1920x1080), tablet (1024x768), and mobile (375x667) devices. Plant managers can monitor production from anywhere.

**3. Real-Time Updates**

Critical metrics update in real-time using WebSockets. Users see live production status, sensor readings, and alerts without refreshing.

**4. AI Co-Pilot Integration**

Every page includes an AI co-pilot sidebar powered by the LLM Orchestration service. Users can ask questions in natural language and get instant answers.

**5. Accessibility (WCAG 2.1 AA)**

All components meet WCAG 2.1 AA standards with keyboard navigation, screen reader support, and sufficient color contrast.

---

## Technology Stack

### Core Framework

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 15.x | React framework with App Router, SSR, and API routes |
| **React** | 19.x | UI component library |
| **TypeScript** | 5.3+ | Type-safe development |
| **Refine** | 4.x | Enterprise admin framework with CRUD operations |
| **TailwindCSS** | 3.4+ | Utility-first CSS framework |
| **shadcn/ui** | Latest | Beautiful, accessible component library |

### Data Visualization

| Library | Purpose |
|---------|---------|
| **Recharts** | Charts and graphs (line, bar, pie, area) |
| **D3.js** | Custom visualizations (network graphs, heatmaps) |
| **React Flow** | Interactive flowcharts (traceability diagrams) |
| **Leaflet** | Maps (distribution tracking, plant locations) |

### State Management

| Tool | Purpose |
|------|---------|
| **TanStack Query** | Server state management, caching, optimistic updates |
| **Zustand** | Client state management (UI state, preferences) |
| **React Context** | Theme, authentication, tenant context |

### Real-Time Communication

| Technology | Purpose |
|------------|---------|
| **Socket.IO Client** | WebSocket connections for real-time updates |
| **Server-Sent Events (SSE)** | One-way streaming (sensor data, alerts) |

### Forms & Validation

| Library | Purpose |
|---------|---------|
| **React Hook Form** | Form state management |
| **Zod** | Schema validation |
| **React Dropzone** | File uploads (images, documents) |

---

## Application Structure

### Directory Structure

```
apps/web/                          # Next.js frontend application
├── src/
│   ├── app/                       # Next.js App Router
│   │   ├── (auth)/                # Authentication routes
│   │   │   ├── login/
│   │   │   ├── register/
│   │   │   └── forgot-password/
│   │   ├── (dashboard)/           # Main application routes
│   │   │   ├── layout.tsx         # Dashboard layout with sidebar
│   │   │   ├── page.tsx           # Dashboard home
│   │   │   ├── foodgraph/         # FoodGraph pages
│   │   │   │   ├── traceability/
│   │   │   │   ├── suppliers/
│   │   │   │   └── risk-analysis/
│   │   │   ├── production/        # Production pages
│   │   │   │   ├── orders/
│   │   │   │   ├── batches/
│   │   │   │   └── analytics/
│   │   │   ├── quality/           # Quality pages
│   │   │   │   ├── inspections/
│   │   │   │   ├── defects/
│   │   │   │   └── compliance/
│   │   │   ├── forecasting/       # Forecasting pages
│   │   │   │   ├── demand/
│   │   │   │   ├── inventory/
│   │   │   │   └── scenarios/
│   │   │   ├── sensors/           # Sensor monitoring pages
│   │   │   │   ├── real-time/
│   │   │   │   ├── alerts/
│   │   │   │   └── history/
│   │   │   ├── optimization/      # Optimization pages
│   │   │   │   ├── production-planning/
│   │   │   │   ├── inventory/
│   │   │   │   └── routing/
│   │   │   ├── data-room/         # Data sharing pages
│   │   │   │   ├── contracts/
│   │   │   │   ├── shared-data/
│   │   │   │   └── requests/
│   │   │   └── settings/          # Settings pages
│   │   │       ├── profile/
│   │   │       ├── team/
│   │   │       ├── integrations/
│   │   │       └── billing/
│   │   ├── api/                   # Next.js API routes (BFF pattern)
│   │   │   ├── auth
