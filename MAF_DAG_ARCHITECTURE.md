# MAF DAG Workflow Architecture

## True MAF DAG Implementation ✅

This implementation now uses **Microsoft Agent Framework's native DAG orchestration** with:

### Core Components

#### 1. **Executor Nodes** (Processing Units)
Each agent is wrapped as an `Executor` with `@handler` methods:
- `StrategyExecutor` - Campaign strategy generation
- `ResearchExecutor` - Contextual research
- `BrandVoiceExecutor` - Brand voice definition
- `ContentGeneratorExecutor` - Parallel content creation
- `CalendarExecutor` - Content scheduling
- `PublisherExecutor` - Publishing simulation

#### 2. **Typed Messages** (Data Flow)
Strongly-typed dataclasses for message passing:
- `StrategyMessage`
- `ResearchMessage`
- `BrandVoiceMessage`
- `ContentMessage`
- `CalendarMessage`
- `FinalResult`

#### 3. **WorkflowBuilder** (DAG Construction)
```python
builder = WorkflowBuilder()
builder.set_start_executor(strategy_executor)
builder.add_edge(strategy_executor, research_executor)
builder.add_edge(research_executor, brand_voice_executor)
builder.add_edge(brand_voice_executor, content_executor)
builder.add_edge(content_executor, calendar_executor)
builder.add_edge(calendar_executor, publisher_executor)
workflow = builder.build()
```

## DAG Visualization

```
┌────────────────────┐
│ CampaignRequest    │ (User Input)
└──────────┬─────────┘
           ↓
┌──────────────────────────┐
│  StrategyExecutor        │
│  @handler: process_request│
└──────────┬───────────────┘
           ↓ StrategyMessage
┌──────────────────────────┐
│  ResearchExecutor        │
│  @handler: process_strategy│
└──────────┬───────────────┘
           ↓ ResearchMessage
┌──────────────────────────┐
│  BrandVoiceExecutor      │
│  @handler: process_research│
└──────────┬───────────────┘
           ↓ BrandVoiceMessage
┌──────────────────────────┐
│  ContentGeneratorExecutor│ (internally parallel)
│  @handler: process_brand_voice│
└──────────┬───────────────┘
           ↓ ContentMessage
┌──────────────────────────┐
│  CalendarExecutor        │
│  @handler: process_content│
└──────────┬───────────────┘
           ↓ CalendarMessage
┌──────────────────────────┐
│  PublisherExecutor       │
│  @handler: process_calendar│
└──────────┬───────────────┘
           ↓ FinalResult
┌──────────────────────────┐
│  API Response            │
└──────────────────────────┘
```

## Key MAF Features Used

### ✅ Executor Pattern
- Each node is an `Executor` class
- Strongly-typed `@handler` methods
- Type-safe message passing

### ✅ WorkflowBuilder
- Declarative DAG construction
- Explicit edge definition
- Start executor specification

### ✅ Message Passing
- Dataclass-based messages
- Automatic serialization
- Type validation

### ✅ State Management
- Messages carry context through the workflow
- Each executor receives typed input
- Produces typed output for next executor

## Benefits Over Previous Implementation

| Previous (Async) | New (MAF DAG) |
|------------------|---------------|
| Manual `await` chains | Declarative edges |
| No type safety | Strongly-typed messages |
| Ad-hoc state passing | Structured message flow |
| No native checkpointing | MAF checkpointing support |
| Custom orchestration | MAF runtime orchestration |
| Limited observability | Built-in MAF telemetry |

## Running the Workflow

```python
# Create workflow
workflow = CampaignWorkflow()

# Execute DAG
result = await workflow.run_campaign(campaign_request)
```

The `WorkflowBuilder` handles:
- Executor initialization
- Message routing
- Error propagation
- Type validation
- State management

## Future Enhancements

1. **Conditional Branching**: Add conditional edges based on strategy
2. **Parallel Branches**: Multiple paths (e.g., simultaneous analytics)
3. **Human-in-the-Loop**: Add approval gates
4. **Checkpointing**: Save/resume long-running workflows
5. **Error Handling**: Add error recovery executors
6. **Observability**: Integrate MAF telemetry for monitoring

## Notes

This is now a **true MAF DAG orchestration** leveraging the framework's native capabilities for building production-grade multi-agent systems.
