# ADR 001: Copilot-First UI Pattern

## Status
**Accepted** - 2024-11-21

## Context

FoodFlow OS is an AI-first platform where machine learning and LLM capabilities are core to the value proposition. However, there are multiple ways to integrate AI into a web application:

1. **AI as Helper**: Optional help buttons or assistants that users can optionally engage with
2. **Direct AI Calls**: UI components directly call AI service endpoints
3. **Copilot-First**: All AI interactions go through a central Copilot orchestration layer

We need to choose an approach that maximizes AI value while maintaining good engineering practices.

## Decision

We will adopt a **Copilot-First** pattern where:

1. **Smart buttons and complex actions in the UI call the Copilot with specific prompts**, not directly call AI service endpoints
2. **The Copilot orchestration layer decides which tools to use** based on the user's intent
3. **All AI interactions are logged through the telemetry service** for ROI measurement and continuous improvement
4. **Users interact with AI conversationally** through the Copilot panel, not just through action results

## Rationale

### Advantages of Copilot-First

1. **Centralized Intelligence**
   - Single place to tune prompts and improve AI behavior
   - Consistent experience across all workspaces
   - Easier to add new capabilities without UI changes

2. **Comprehensive Telemetry**
   - Every interaction logged automatically
   - Can measure ROI: "AI saved $XX,XXX this month"
   - Build training datasets from real usage
   - A/B test different prompts and approaches

3. **Better User Experience**
   - Users can ask follow-up questions naturally
   - Copilot provides explanations, not just results
   - Context is preserved across interactions
   - Can handle ambiguity and ask clarifying questions

4. **Engineering Benefits**
   - UI code is simpler (just calls Copilot)
   - No need to manage complex AI service client logic in frontend
   - Easier to mock and test
   - Backend handles AI service failures gracefully

5. **Business Value**
   - Can demonstrate AI usage and impact to investors/customers
   - Identify which features users actually value
   - Continuous improvement based on feedback
   - Competitive differentiation: "AI-native" not "AI-added"

### Disadvantages & Mitigation

1. **Additional Latency** (Copilot → Tools → AI Service)
   - **Mitigation**: Copilot calls tools asynchronously, overall latency is similar
   - **Mitigation**: Cache common queries
   - **Mitigation**: Stream responses for better perceived performance

2. **More Complex Backend**
   - **Mitigation**: Complexity is in one place (Copilot), not spread across UI
   - **Mitigation**: Clear tool interfaces make it maintainable
   - **Mitigation**: Comprehensive testing of tool orchestration

3. **Requires LLM for Orchestration**
   - **Mitigation**: Can fall back to rule-based routing if LLM unavailable
   - **Mitigation**: LLM calls are fast (<500ms) for orchestration
   - **Mitigation**: Critical for our AI-first positioning anyway

## Alternatives Considered

### Alternative 1: Direct AI Service Calls from UI

**Approach**: React components directly call AI service endpoints
```typescript
const result = await aiService.analyzeScrap({ lineId, dates });
```

**Rejected because**:
- No telemetry by default
- Can't handle conversations
- UI code becomes AI-aware and complex
- Difficult to improve AI behavior without UI changes

### Alternative 2: AI as Optional Helper

**Approach**: Traditional UI with optional AI assistant sidebar

**Rejected because**:
- Relegates AI to secondary feature
- Users may not discover AI capabilities
- Doesn't match "AI-first" positioning
- Harder to demonstrate AI value/ROI

### Alternative 3: Hybrid Approach

**Approach**: Some features use Copilot, some use direct calls

**Rejected because**:
- Inconsistent user experience
- Split telemetry (some tracked, some not)
- More complex to maintain
- Confusing mental model for developers

## Implementation

### Smart Button Example

```typescript
// ✅ CORRECT: Call Copilot
<Button onClick={() => copilot.ask({
  workspace: "plantops",
  message: "Diagnose scrap spike on Line 3",
  context: { line_id, date_range: "last_7_days" }
})}>
  Diagnose Scrap Spike
</Button>

// ❌ WRONG: Direct AI call
<Button onClick={() => aiService.analyzeScrap(...)}>
  Diagnose Scrap Spike
</Button>
```

### Copilot Tool Registry

```python
# Backend: Copilot calls tools based on user intent
@tool("analyze_scrap")
async def analyze_scrap_tool(line_id: str, date_range: str):
    """Analyze scrap patterns for a production line."""
    result = await ai_client.analyze_scrap(...)
    return format_for_llm(result)
```

### Telemetry Automatic

```python
# Every Copilot interaction is automatically logged
await telemetry.log_copilot_interaction(
    tenant_id=tenant_id,
    user_id=user_id,
    workspace=workspace,
    question=message,
    answer=response,
    tools_used=tools_used,
    duration_ms=duration,
)
```

## Consequences

### Positive

1. **Complete Telemetry**: Every AI interaction tracked for ROI measurement
2. **Conversational AI**: Users can ask follow-ups, get explanations
3. **Rapid Iteration**: Improve AI by tuning prompts/tools, not changing UI
4. **Competitive Advantage**: True AI-native experience
5. **Easier Testing**: Mock Copilot instead of multiple AI endpoints

### Negative

1. **Learning Curve**: Developers must understand Copilot pattern
2. **Backend Complexity**: Need robust tool orchestration layer
3. **LLM Dependency**: Requires LLM for optimal orchestration (but can fallback)

### Neutral

1. **Different from Traditional Apps**: Requires mindset shift for developers familiar with direct API patterns

## Compliance

All new smart buttons and AI-powered features MUST:
- ✅ Call Copilot, not AI service directly
- ✅ Provide rich context objects
- ✅ Use clear, action-oriented prompts
- ✅ Show responses in Copilot panel
- ✅ Include in telemetry dashboards

**Exception Process**: If a feature absolutely must call AI service directly (e.g., real-time sensor processing), it requires architectural review and approval.

## References

- [COPILOT_FIRST_PATTERN.md](../COPILOT_FIRST_PATTERN.md) - Detailed implementation guide
- AI Contracts Documentation - `/docs/ai_contracts.md`
- Telemetry Service Documentation - `/backend/src/core/telemetry/`

## Review Schedule

This ADR will be reviewed:
- After first 1000 Copilot interactions (measure adoption)
- After 3 months (measure business impact)
- When major AI capabilities are added

---

**Author**: FoodFlow OS Architecture Team  
**Date**: 2024-11-21  
**Reviewers**: Engineering, Product, AI/ML leads

