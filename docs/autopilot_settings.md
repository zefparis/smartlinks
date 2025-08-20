# Autopilot Algorithm Settings Documentation

## Overview

The SmartLinks Autopilot system provides advanced algorithm configuration with AI governance controls. Each algorithm can be configured with specific parameters and governed by DG AI policies to ensure safe and controlled autonomous operations.

## Algorithm Types

### 1. Traffic Optimizer
**Purpose**: Optimizes traffic routing based on conversion rate (CVR), revenue, or click-through rate (CTR).

**Key Settings**:
- `objective`: Target metric (`cvr`, `revenue`, `ctr`)
- `exploration_ratio`: Percentage of traffic for exploration (0.0-0.5)
- `learning_rate`: Speed of adaptation (0.01-1.0)
- `reweight_max_delta`: Maximum weight change per action (0.01-0.5)
- `min_conversions_for_action`: Minimum conversions before taking action
- `segmenting`: Enable segmentation by geo, device, source
- `canary_percent`: Percentage of traffic for testing (0.0-0.2)

**Effects**:
- Automatically adjusts traffic weights based on performance
- Implements A/B testing with statistical significance
- Respects daily caps and whitelist/blacklist rules

### 2. Anomaly Detector
**Purpose**: Detects traffic anomalies and triggers automatic mitigations.

**Key Settings**:
- `watched_metrics`: Metrics to monitor (`cvr`, `clicks`, `errors`, `latency_ms`)
- `sensitivity`: Detection sensitivity (`low`, `medium`, `high`)
- `baseline`: Comparison baseline (`24h_mean`, `7d_seasonal`)
- `detect_window_minutes`: Detection window (5-240 minutes)
- `auto_mitigations`: Automatic responses to anomalies
- `mitigation_limits`: Daily limits for automatic actions

**Effects**:
- Monitors metrics in real-time
- Automatically pauses problematic destinations
- Reroutes traffic during performance drops
- Sends alerts via configured channels

### 3. Budget Arbitrage
**Purpose**: Reallocates budget based on performance and ROI constraints.

**Key Settings**:
- `pacing`: Budget distribution strategy (`uniform`, `asap`, `smart`)
- `roi_constraint`: ROI optimization target (`none`, `cpa`, `cpl`, `roas`)
- `roi_target_value`: Target ROI value
- `priority_tiers`: Campaign priority groupings
- `reallocation_min_step`: Minimum budget move (0.01-0.5)
- `overspend_guard_percent`: Protection against overspending

**Effects**:
- Moves budget from underperforming to high-performing campaigns
- Respects ROI constraints and priority tiers
- Implements pacing strategies throughout the day
- Prevents overspending with guard rails

### 4. Predictive Alerting
**Purpose**: Predicts issues before they occur and triggers preventive actions.

**Key Settings**:
- `targets`: Prediction targets (`traffic_spike`, `conversion_drop`, `error_surge`)
- `horizon_minutes`: Prediction time horizon (15-720 minutes)
- `confidence_threshold`: Minimum confidence for alerts (0.5-0.99)
- `min_lead_time_minutes`: Minimum warning time (5-120 minutes)
- `playbooks`: Automated response actions
- `quiet_hours`: Disable alerts during specified hours

**Effects**:
- Predicts traffic spikes and scales infrastructure
- Warns of conversion drops before they impact revenue
- Triggers preventive actions based on playbooks
- Respects quiet hours for non-critical alerts

### 5. Self-Healing
**Purpose**: Automatically fixes detected system issues.

**Key Settings**:
- `detectors`: Health check types (`healthz`, `latency`, `error_rate`)
- `remediation`: Available fix actions (`restart_service`, `disable_probe`, `rollback_route`)
- `retry_policy`: Retry configuration and backoff
- `blast_radius_cap_percent`: Maximum impact limit (0.01-0.5)
- `escalation`: Human escalation settings
- `freeze_after_failures`: Stop after N consecutive failures

**Effects**:
- Automatically restarts failing services
- Disables problematic health probes
- Rolls back problematic route changes
- Escalates to humans when automated fixes fail

## Common Settings

All algorithms share these base settings:

- `active`: Enable/disable the algorithm
- `interval_seconds`: Run frequency (60-3600 seconds)
- `cooldown_seconds`: Minimum time between actions (30-600 seconds)
- `dry_run`: Preview mode without actual changes
- `audit_tag`: Custom tag for audit logging
- `max_actions_per_tick`: Maximum actions per run (1-1000)
- `max_risk_score_per_tick`: Maximum risk budget per run (0.0-1.0)

## AI Governance (DG AI)

### Authority Levels
- **Advisory**: AI provides recommendations only, no automatic actions
- **Safe Apply**: AI can execute low-risk actions automatically
- **Full Control**: AI has full autonomy within configured guards

### Risk Management
- `risk_budget_daily`: Maximum daily risk budget (0-100)
- `dry_run`: Force preview mode for all AI actions
- `hard_guards`: Strict limits that cannot be exceeded
- `soft_guards`: Warnings and additional checks

### Hard Guards Examples
```json
{
  "weight_delta_max": 0.2,           // Max 20% weight change
  "budget_shift_max_percent": 0.2,   // Max 20% budget shift
  "pause_dest_max_per_day": 2        // Max 2 destination pauses/day
}
```

### Soft Guards Examples
```json
{
  "require_explain": true,           // Require AI explanation
  "require_plan_id": true           // Require execution plan ID
}
```

## Risk Scoring

Each algorithm action is assigned a risk score (0.0-1.0):
- **0.0-0.3**: Low risk (minor adjustments)
- **0.3-0.7**: Medium risk (significant changes)
- **0.7-1.0**: High risk (major impacts)

Daily risk budgets prevent excessive automated changes.

## Audit Logging

All algorithm actions are logged with:
- Timestamp and actor (algorithm or user)
- Before/after values for all changes
- Risk score and justification
- Execution status and any errors
- Impact measurements where available

## Best Practices

### Configuration
1. Start with conservative settings and gradually increase autonomy
2. Use dry_run mode to validate algorithm behavior
3. Set appropriate risk budgets based on business impact
4. Configure hard guards for critical business rules

### Monitoring
1. Review audit logs regularly for unexpected behavior
2. Monitor risk budget usage and adjust as needed
3. Set up alerts for algorithm failures or guard violations
4. Use preview mode to understand proposed actions

### Governance
1. Assign appropriate authority levels based on algorithm maturity
2. Implement hard guards for non-negotiable business rules
3. Use soft guards for additional oversight and explanations
4. Regular review of AI policies and guard effectiveness

## API Endpoints

- `GET /autopilot/algorithms` - List all algorithms
- `GET /autopilot/algorithms/{key}/settings` - Get algorithm settings
- `PUT /autopilot/algorithms/{key}/settings` - Update algorithm settings
- `GET /autopilot/ai/policy/{key}` - Get AI governance policy
- `PUT /autopilot/ai/policy/{key}` - Update AI governance policy
- `POST /autopilot/algorithms/{key}/run` - Trigger manual run
- `GET /autopilot/algorithms/{key}/preview` - Preview algorithm actions
- `GET /autopilot/audit/{key}` - Get audit history

## Troubleshooting

### Algorithm Not Running
1. Check `active` setting is enabled
2. Verify `interval_seconds` configuration
3. Check for recent failures in audit logs
4. Ensure risk budget is not exhausted

### Actions Not Executing
1. Verify authority level allows execution
2. Check if `dry_run` mode is enabled
3. Review hard guard violations in logs
4. Confirm risk budget availability

### Unexpected Behavior
1. Review algorithm settings for misconfigurations
2. Check recent changes in audit history
3. Verify input data quality and availability
4. Consider reducing sensitivity or increasing thresholds
