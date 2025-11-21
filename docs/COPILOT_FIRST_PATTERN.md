# Copilot-First UI Pattern

## Overview

FoodFlow OS follows a **Copilot-First** design pattern where AI assistance is the primary interface for complex actions, rather than an afterthought or "help button."

**Key Principle**: Smart buttons and complex actions in the UI should call the Copilot with specific prompts and context, NOT directly call AI service endpoints or complex backend logic.

---

## Why Copilot-First?

### 1. **Centralized Intelligence**
- All AI interactions go through one orchestration layer
- Easier to tune prompts and improve AI behavior
- Consistent user experience across all workspaces

### 2. **Telemetry & Learning**
- Every interaction is logged for ROI measurement
- We can track which features users actually use
- Build training datasets from real usage
- A/B test different prompts and tools

### 3. **Graceful Degradation**
- If AI service is down, Copilot can still respond helpfully
- Can fallback to simpler logic or cached results
- Better error messages and user guidance

### 4. **Context-Aware**
- Copilot has access to full workspace context
- Can combine multiple tool calls intelligently
- Can ask clarifying questions if needed

---

## The Pattern

### ❌ WRONG: Direct AI Service Call from UI

```typescript
// BAD - Don't do this!
async function diagnoseScrapSpike() {
  const result = await aiService.analyzeScrap({
    lineId: currentLine.id,
    startDate: last7Days.start,
    endDate: last7Days.end,
  });
  
  showResults(result);
}
```

**Problems:**
- No telemetry
- No conversational context
- Can't handle complex scenarios
- Brittle error handling
- User can't ask follow-up questions

### ✅ RIGHT: Call Copilot with Intent

```typescript
// GOOD - Do this!
async function diagnoseScrapSpike() {
  const response = await copilotService.ask({
    workspace: "plantops",
    message: "Diagnose the scrap spike on Line 3 over the last 7 days",
    context: {
      line_id: currentLine.id,
      date_range: "last_7_days",
      current_view: "line_overview",
      user_role: currentUser.role,
    },
  });
  
  // Show response in Copilot panel (opens automatically if needed)
  showCopilotResponse(response);
}
```

**Benefits:**
- Full telemetry logging
- Can provide richer response with explanation
- User can ask follow-ups naturally
- Copilot decides which tools to use
- Context is preserved for conversation

---

## Implementation Guide

### Step 1: Identify Smart Button Candidates

Smart buttons are actions that:
- Involve AI/ML analysis
- Require multiple data sources
- Benefit from explanation/reasoning
- Users might want to ask follow-ups about

**Examples:**
- "Diagnose scrap spike"
- "Suggest trial parameters"
- "Find similar batches"
- "Run mock recall"
- "Optimize production plan"
- "Recommend replenishment"

### Step 2: Define Copilot Prompts

Create clear, specific prompts that convey user intent:

```typescript
// prompts/plantops.ts
export const PLANTOPS_PROMPTS = {
  diagnoseScrap: (lineId: string, period: string) => 
    `Analyze scrap patterns for Line ${lineId} over ${period}. 
     What are the top causes and what should we do about it?`,
  
  suggestTrial: (lineId: string, goal: string) => 
    `I want to ${goal} on Line ${lineId}. 
     What trial parameters do you recommend?`,
  
  compareCurrentBatch: (batchId: string) => 
    `Compare the current batch ${batchId} to similar historical batches. 
     Are we on track or seeing any unusual patterns?`,
};
```

### Step 3: Implement Smart Button Handler

```typescript
// components/SmartButton.tsx
import { useCopilot } from '@/hooks/useCopilot';
import { PLANTOPS_PROMPTS } from '@/prompts/plantops';

export function DiagnoseScrapButton({ line }: { line: Line }) {
  const { ask, isLoading } = useCopilot();
  
  const handleClick = async () => {
    await ask({
      workspace: "plantops",
      message: PLANTOPS_PROMPTS.diagnoseScrap(line.id, "last_7_days"),
      context: {
        line_id: line.id,
        line_name: line.name,
        plant_id: line.plant_id,
        date_range: "last_7_days",
        // Include relevant metrics user is looking at
        current_scrap_rate: line.metrics.scrap_rate,
        avg_scrap_rate: line.metrics.avg_scrap_rate,
      },
      // Optional: Provide suggested tools Copilot might need
      suggestedTools: ["analyze_scrap", "get_line_events"],
    });
  };
  
  return (
    <Button 
      onClick={handleClick} 
      disabled={isLoading}
      variant="ai"
      icon={<SparklesIcon />}
    >
      Diagnose Scrap Spike
    </Button>
  );
}
```

### Step 4: Show Response in Copilot Panel

```typescript
// hooks/useCopilot.ts
export function useCopilot() {
  const { openPanel } = useCopilotPanel();
  
  const ask = async (request: CopilotRequest) => {
    // Open Copilot panel if not already open
    openPanel();
    
    // Send request
    const response = await api.post('/api/v1/copilot', request);
    
    // Response automatically appears in panel
    return response.data;
  };
  
  return { ask, isLoading, ... };
}
```

---

## Copilot Context Object

Always provide rich context to help Copilot make better decisions:

```typescript
interface CopilotContext {
  // Identity
  workspace: "plantops" | "fsq" | "planning" | "brand" | "retail";
  
  // Current view/page
  current_view?: string;  // e.g., "line_overview", "batch_details"
  
  // Entity IDs (what user is looking at)
  line_id?: string;
  batch_id?: string;
  lot_id?: string;
  plant_id?: string;
  
  // Time context
  date_range?: string;  // "last_7_days", "this_month", etc.
  
  // User context
  user_role?: string;
  user_permissions?: string[];
  
  // Visible data (what user can see on screen)
  visible_metrics?: Record<string, any>;
  visible_alerts?: any[];
  
  // User's recent actions (helps with "that" and "this")
  recent_selections?: string[];
  previous_context?: CopilotContext;
}
```

---

## When NOT to Use Copilot

Some actions should still be direct API calls:

### 1. **Simple CRUD Operations**
```typescript
// Simple create/update/delete - just use regular API
async function createBatch(data: BatchCreate) {
  return await api.post('/api/v1/plant-ops/batches', data);
}
```

### 2. **Real-Time Data Fetching**
```typescript
// Fetching list data, metrics - use regular API
async function getLineMetrics(lineId: string) {
  return await api.get(`/api/v1/plant-ops/lines/${lineId}/metrics`);
}
```

### 3. **User Preferences/Settings**
```typescript
// Settings changes - use regular API
async function updateUserPreferences(prefs: Preferences) {
  return await api.patch('/api/v1/users/me/preferences', prefs);
}
```

**Rule of Thumb**: If the action involves analysis, recommendations, or complex reasoning → use Copilot. If it's straightforward data manipulation → use direct API.

---

## Copilot Response Format

Copilot responses should be rich and actionable:

```typescript
interface CopilotResponse {
  // The answer
  message: string;  // Markdown-formatted
  
  // Optional: Suggested actions user can take
  actions?: Array<{
    label: string;
    action_type: "navigate" | "api_call" | "open_modal";
    parameters: Record<string, any>;
  }>;
  
  // Optional: Data visualizations
  visualizations?: Array<{
    type: "chart" | "table" | "metric_card";
    data: any;
  }>;
  
  // Tools that were called
  tools_used?: string[];
  
  // Suggestions for follow-up questions
  suggestions?: string[];
  
  // Telemetry
  interaction_id: string;
  confidence: number;
}
```

---

## Examples by Workspace

### PlantOps Workspace

```typescript
// Line Overview Page
<SmartButton 
  label="Diagnose Scrap Spike"
  prompt="Analyze scrap patterns for this line over the last 7 days. What are the top causes and recommended actions?"
  context={{ line_id, date_range: "last_7_days" }}
/>

<SmartButton
  label="Optimize Line Speed"
  prompt="Suggest optimal line speed and parameters to maximize OEE while maintaining quality."
  context={{ line_id, current_speed, current_oee }}
/>

// Batch Details Page
<SmartButton
  label="Compare to Similar Batches"
  prompt="Compare this batch to historically similar batches. Are we on track?"
  context={{ batch_id, sku_id, line_id }}
/>
```

### FSQ Workspace

```typescript
// Lot Details Page
<SmartButton
  label="Assess Lot Risk"
  prompt="Calculate the risk score for this lot and tell me if we need additional testing or actions."
  context={{ lot_id, supplier_id, production_date }}
/>

// Mock Recall Tool
<SmartButton
  label="Run Mock Recall"
  prompt="Simulate a recall starting from this lot. Show me the full impact and what we'd need to do."
  context={{ lot_id, scope_type: "lot" }}
/>

// Document Search
<SmartButton
  label="Ask FSQ Question"
  prompt={userQuestion}
  context={{ workspace: "fsq", doc_ids: uploadedDocIds }}
/>
```

### Planning Workspace

```typescript
// Forecast Page
<SmartButton
  label="Generate Forecast"
  prompt="Generate a demand forecast for the next 12 weeks for these SKUs."
  context={{ sku_ids, horizon_weeks: 12 }}
/>

// Production Planning
<SmartButton
  label="Optimize Production Plan"
  prompt="Create an optimal production plan for next month based on the current forecast."
  context={{ forecast_version_id, plant_ids, horizon_weeks: 4 }}
/>
```

---

## Testing Copilot-First Features

### Unit Tests
```typescript
describe('DiagnoseScrapButton', () => {
  it('calls Copilot with correct prompt and context', async () => {
    const mockAsk = jest.fn();
    render(<DiagnoseScrapButton line={mockLine} />, {
      copilotContext: { ask: mockAsk },
    });
    
    await userEvent.click(screen.getByText('Diagnose Scrap Spike'));
    
    expect(mockAsk).toHaveBeenCalledWith({
      workspace: 'plantops',
      message: expect.stringContaining('Analyze scrap patterns'),
      context: expect.objectContaining({
        line_id: mockLine.id,
      }),
    });
  });
});
```

### Integration Tests
```typescript
describe('Copilot Integration', () => {
  it('full flow: button click → Copilot call → response display', async () => {
    // Setup mock Copilot endpoint
    server.use(
      http.post('/api/v1/copilot', () => {
        return HttpResponse.json({
          message: 'Top scrap reason is temperature deviation...',
          tools_used: ['analyze_scrap'],
          confidence: 0.85,
        });
      })
    );
    
    render(<LineOverviewPage />);
    
    // Click smart button
    await userEvent.click(screen.getByText('Diagnose Scrap Spike'));
    
    // Verify Copilot panel opens
    expect(screen.getByTestId('copilot-panel')).toBeVisible();
    
    // Verify response appears
    await waitFor(() => {
      expect(screen.getByText(/temperature deviation/i)).toBeInTheDocument();
    });
  });
});
```

---

## Monitoring & Metrics

Track Copilot-First adoption:

```sql
-- Smart button usage by type
SELECT 
  workspace,
  COUNT(*) as total_interactions,
  AVG(confidence) as avg_confidence,
  COUNT(DISTINCT user_id) as unique_users
FROM copilot_interactions
WHERE tools_used IS NOT NULL  -- Smart button calls use tools
GROUP BY workspace
ORDER BY total_interactions DESC;

-- Most used prompts (for optimization)
SELECT 
  SUBSTRING(question, 1, 50) as prompt_start,
  COUNT(*) as usage_count,
  AVG(feedback_score) as avg_feedback
FROM copilot_interactions
WHERE feedback_score IS NOT NULL
GROUP BY SUBSTRING(question, 1, 50)
ORDER BY usage_count DESC
LIMIT 20;
```

---

## Migration Guide

If you have existing direct AI service calls:

### Before (Direct Call)
```typescript
const result = await fetch('/api/v1/ai/analyze-scrap', {
  method: 'POST',
  body: JSON.stringify({ line_id, start_date, end_date }),
});
```

### After (Copilot-First)
```typescript
const response = await copilot.ask({
  workspace: 'plantops',
  message: `Analyze scrap for Line ${lineName} from ${formatDate(start)} to ${formatDate(end)}`,
  context: { line_id, start_date, end_date },
});
```

**Migration Checklist:**
1. ✅ Identify all direct AI service calls in UI code
2. ✅ Convert to Copilot prompts
3. ✅ Add appropriate context objects
4. ✅ Update UI to show responses in Copilot panel
5. ✅ Remove direct AI service imports from UI components
6. ✅ Update tests to mock Copilot instead of AI service

---

## Best Practices

### 1. **Clear, Action-Oriented Prompts**
- ❌ "scrap analysis" (vague)
- ✅ "Analyze scrap patterns for Line 3 over the last 7 days. What are the top causes and what should we do?"

### 2. **Rich Context**
- Include entity IDs, names, and relevant metrics
- Provide time ranges explicitly
- Include user's current view/page

### 3. **Telemetry-Friendly**
- Every smart button click = logged interaction
- Can track ROI: "Users who clicked X saw Y improvement"

### 4. **User Education**
- Label buttons clearly: "Ask AI" or add sparkle ✨ icon
- Show that Copilot is thinking (loading state)
- Surface Copilot panel when smart button clicked

### 5. **Graceful Degradation**
- If Copilot errors, show helpful message
- Provide fallback to manual actions
- Log errors for monitoring

---

## Success Metrics

**Adoption:**
- % of eligible actions going through Copilot (target: >70%)
- Smart button click-through rate
- Repeat usage rate

**Quality:**
- Average feedback score on Copilot responses (target: >4.0/5.0)
- % of interactions that lead to user action (target: >60%)
- Time saved vs manual analysis

**Business Impact:**
- Reduction in analysis time (target: -40%)
- Increase in issue identification (target: +25%)
- User satisfaction scores

---

## Summary

**The Copilot-First Pattern Ensures:**
- ✅ All AI interactions are logged and measured
- ✅ Consistent, high-quality AI experience
- ✅ Users can have conversations, not just get results
- ✅ We can continuously improve based on real usage
- ✅ Better ROI demonstration to stakeholders

**Remember**: Smart buttons should talk to Copilot, not directly to AI services. This is the "secret sauce" that makes FoodFlow OS truly AI-native.

---

**Last Updated**: 2024-11-21  
**Version**: 1.0  
**Applies To**: All FoodFlow OS workspaces

