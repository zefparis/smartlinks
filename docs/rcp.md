# Runtime Control Policies (RCP) Documentation

## Overview

Runtime Control Policies (RCP) provide a comprehensive framework for controlling and governing algorithm actions in real-time. The system allows you to define policies that can monitor, modify, or block algorithm actions based on configurable rules, ensuring safe and controlled operation of automated systems.

## Key Concepts

### Policy Components

#### 1. Guards
Guards are conditions that must be met for actions to proceed:
- **Hard Guards**: Strictly enforced - actions are blocked if conditions fail
- **Soft Guards**: Advisory - generate warnings but don't block actions

```json
{
  "guards": {
    "hard_guards": [
      {
        "name": "cvr_minimum",
        "condition": "metrics.cvr_1h >= 0.02",
        "message": "CVR too low - blocking all actions"
      }
    ],
    "soft_guards": [
      {
        "name": "cvr_warning",
        "condition": "metrics.cvr_1h >= 0.03",
        "message": "CVR below optimal - consider caution"
      }
    ]
  }
}
```

#### 2. Limits
Limits control the rate and magnitude of actions:
- **Rate Limits**: Control how many actions can be performed in a time window
- **Risk Limits**: Control the maximum risk score per action

```json
{
  "limits": {
    "rate_limits": [
      {
        "name": "actions_per_hour",
        "limit": 50,
        "window_minutes": 60,
        "scope": "global"
      }
    ],
    "risk_limits": [
      {
        "name": "max_risk_per_action",
        "limit": 10.0,
        "message": "Action risk too high"
      }
    ]
  }
}
```

#### 3. Gates
Gates control when policies are active:
- **Time Gates**: Activate policies based on schedules
- **Condition Gates**: Activate based on runtime conditions

```json
{
  "gates": {
    "time_gates": [
      {
        "name": "business_hours_only",
        "schedule": "0 9-17 * * 1-5",
        "timezone": "Europe/Paris",
        "enabled": true
      }
    ],
    "condition_gates": [
      {
        "name": "traffic_volume_gate",
        "condition": "metrics.traffic_volume >= 500",
        "message": "Traffic volume too low for safe operation"
      }
    ]
  }
}
```

#### 4. Mutations
Mutations modify actions before execution:
- **Weight Mutations**: Modify weight values
- **Delta Mutations**: Limit change magnitudes

```json
{
  "mutations": {
    "weight_mutations": [
      {
        "name": "conservative_weights",
        "condition": "metrics.cvr_1h < 0.04",
        "action": "clamp",
        "field": "weight",
        "max_value": 0.8,
        "message": "Reducing weights due to low CVR"
      }
    ],
    "delta_mutations": [
      {
        "name": "limit_large_changes",
        "max_delta_percent": 20,
        "fields": ["weight", "bid"],
        "message": "Limiting large changes"
      }
    ]
  }
}
```

### Policy Scopes

#### Global Policies
Apply to all algorithms across the system:
```json
{
  "scope": "global",
  "selector": null
}
```

#### Algorithm Policies
Apply to specific algorithms:
```json
{
  "scope": "algorithm",
  "selector": {"algo_key": "traffic_optimizer"}
}
```

#### Segment Policies
Apply to specific user segments:
```json
{
  "scope": "segment",
  "selector": {"segment_data.device": "mobile"}
}
```

### Policy Modes

#### Monitor Mode
- Evaluates policies but doesn't block actions
- Generates audit logs and warnings
- Useful for testing and observability

#### Enforce Mode
- Actively blocks or modifies actions
- Enforces all guards and limits
- Production safety mode

### Authority Levels

Policies require different authority levels to create/modify:
- **viewer**: Read-only access
- **operator**: Basic policy management
- **admin**: Full policy management
- **dg_ai**: Global safety policies and emergency controls

## API Reference

### Policy Management

#### List Policies
```http
GET /api/rcp/policies?scope=global&enabled=true&page=1&per_page=50
```

#### Create Policy
```http
POST /api/rcp/policies
Content-Type: application/json
X-Role: admin

{
  "id": "my-policy-001",
  "name": "My Safety Policy",
  "description": "Custom safety policy",
  "scope": "algorithm",
  "selector": {"algo_key": "my_algorithm"},
  "mode": "enforce",
  "enabled": true,
  "authority_required": "admin",
  "guards": { ... },
  "limits": { ... },
  "gates": { ... },
  "mutations": { ... }
}
```

#### Update Policy
```http
PUT /api/rcp/policies/{policy_id}
Content-Type: application/json
X-Role: admin

{
  "enabled": false,
  "description": "Updated description"
}
```

#### Delete Policy
```http
DELETE /api/rcp/policies/{policy_id}
X-Role: admin
```

### Policy Evaluation

#### Preview Evaluation
Test policies without applying them:
```http
POST /api/rcp/preview
Content-Type: application/json
X-Role: operator

{
  "algo_key": "traffic_optimizer",
  "actions": [
    {
      "id": "action-001",
      "type": "reweight",
      "algo_key": "traffic_optimizer",
      "idempotency_key": "unique-key-001",
      "data": {
        "target": "destination_123",
        "weight": 0.8,
        "previous_weight": 0.6
      },
      "risk_score": 2.5
    }
  ],
  "ctx": {
    "metrics": {
      "cvr_1h": 0.045,
      "traffic_volume": 1000
    },
    "segment_data": {
      "device": "desktop",
      "geo": "US"
    }
  }
}
```

### Evaluation History

#### List Evaluations
```http
GET /api/rcp/evaluations?algo_key=traffic_optimizer&since=2024-01-01T00:00:00Z
```

#### Get Evaluation Stats
```http
GET /api/rcp/evaluations/stats?algo_key=traffic_optimizer
```

## Integration Guide

### Backend Integration

The RCP system is automatically integrated into the algorithm runner. When algorithms generate actions, they are evaluated against applicable policies before execution.

#### Manual Override
Manual overrides bypass RCP evaluation:
```python
result = await runner.run_algorithm("traffic_optimizer", manual_override=True)
```

#### Custom Metrics
Provide custom metrics for policy evaluation:
```python
async def _get_current_metrics(self, algo_key: str) -> Dict[str, float]:
    return {
        "cvr_1h": await get_hourly_cvr(algo_key),
        "traffic_volume": await get_traffic_volume(),
        "error_rate": await get_error_rate(algo_key)
    }
```

### Frontend Integration

#### Algorithm Settings
The RCP tab in algorithm settings allows configuring algorithm-specific policies:
- Guards configuration
- Limits setup
- Gates and scheduling
- Mutations definition
- Preview and testing

#### DG AI Control Page
Global RCP management interface:
- View all policies
- Create/edit global policies
- Monitor evaluation history
- View analytics and trends

## Best Practices

### Policy Design

1. **Start with Monitor Mode**
   - Test policies in monitor mode first
   - Analyze evaluation logs before enforcing

2. **Use Soft Guards for Warnings**
   - Implement soft guards for early warning signals
   - Reserve hard guards for critical safety conditions

3. **Implement Gradual Rollouts**
   - Use rollout percentages for canary deployments
   - Monitor impact before full rollout

4. **Set Appropriate Authority Levels**
   - Global safety policies require DG AI authority
   - Algorithm-specific policies can use admin authority

### Condition Writing

1. **Use Clear Variable Names**
   ```json
   "condition": "metrics.cvr_1h >= 0.02"  // Good
   "condition": "m.c >= 0.02"            // Bad
   ```

2. **Include Meaningful Messages**
   ```json
   "message": "CVR below safety threshold - blocking actions"  // Good
   "message": "Condition failed"                               // Bad
   ```

3. **Test Conditions Thoroughly**
   - Use the preview endpoint to test conditions
   - Verify edge cases and error handling

### Monitoring and Alerting

1. **Monitor Policy Effectiveness**
   - Track blocked/modified action rates
   - Analyze risk cost trends
   - Review evaluation statistics

2. **Set Up Alerts**
   - Alert on high block rates
   - Monitor policy evaluation failures
   - Track authority escalations

3. **Regular Policy Reviews**
   - Review policy effectiveness monthly
   - Update conditions based on system changes
   - Archive obsolete policies

## Troubleshooting

### Common Issues

#### Policy Not Triggering
1. Check policy scope and selector
2. Verify gates are open (time/condition gates)
3. Confirm rollout percentage includes current execution
4. Check policy enabled status

#### Actions Always Blocked
1. Review hard guard conditions
2. Check rate limits and current usage
3. Verify risk limits and action risk scores
4. Examine condition syntax

#### Mutations Not Applied
1. Confirm mutation conditions are met
2. Check field names match action data
3. Verify mutation action types (clamp, multiply, etc.)
4. Review mutation order and conflicts

### Debugging Tools

#### Preview Endpoint
Use the preview endpoint to test policies:
```bash
curl -X POST http://localhost:8000/api/rcp/preview \
  -H "Content-Type: application/json" \
  -H "X-Role: admin" \
  -d @test_policy.json
```

#### Evaluation Logs
Check evaluation history for debugging:
```bash
curl "http://localhost:8000/api/rcp/evaluations?algo_key=traffic_optimizer&since=2024-01-01T00:00:00Z" \
  -H "X-Role: admin"
```

#### Policy Validation
Validate policy syntax before creation:
```python
from src.soft.rcp.schemas import RCPPolicyCreate

try:
    policy = RCPPolicyCreate(**policy_data)
    print("Policy is valid")
except ValidationError as e:
    print(f"Policy validation failed: {e}")
```

## Security Considerations

### Access Control
- Policies require appropriate RBAC permissions
- DG AI authority required for global safety policies
- Audit all policy changes and evaluations

### Data Protection
- Sensitive data in conditions should be anonymized
- Policy evaluation logs may contain business data
- Implement data retention policies for evaluations

### Emergency Procedures
- Emergency circuit breaker policies for crisis situations
- Manual override capabilities for urgent situations
- Escalation procedures for policy failures

## Performance Considerations

### Evaluation Performance
- Policies are evaluated in memory for speed
- Rate limiting uses in-memory caching
- Complex conditions may impact performance

### Scaling
- Policy evaluation scales with action volume
- Consider policy complexity vs. evaluation frequency
- Monitor evaluation latency and optimize as needed

### Caching
- Policy definitions are cached for performance
- Rate limit counters use time-windowed caching
- Clear caches when policies are updated

## Examples

See the seed data file (`src/soft/rcp/seed_data.py`) for complete policy examples including:
- Global safety guards
- Algorithm-specific controls
- Segment-based policies
- Emergency circuit breakers

## Support

For questions or issues with RCP:
- Check the troubleshooting section above
- Review evaluation logs and statistics
- Contact the DG AI team for global policy issues
- Submit issues through the standard support channels
