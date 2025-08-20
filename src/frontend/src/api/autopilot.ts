/**
 * API client for autopilot algorithm settings and AI governance
 */

import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Algorithm {
  key: string;
  name: string;
  description: string;
  status: string;
  last_run: string;
  performance: Record<string, any>;
}

export interface AlgorithmSettings {
  settings: Record<string, any>;
  schema: Record<string, any>;
  version: number;
  updated_by: string;
  updated_at: string;
}

export interface AIPolicy {
  authority: 'advisory' | 'safe_apply' | 'full_control';
  risk_budget_daily: number;
  dry_run: boolean;
  hard_guards: Record<string, any>;
  soft_guards: Record<string, any>;
}

export interface PreviewAction {
  action_type: string;
  target: string;
  current_value: any;
  proposed_value: any;
  risk_score: number;
  justification: string;
}

export interface PreviewResponse {
  actions: PreviewAction[];
  total_risk_score: number;
  estimated_impact: Record<string, any>;
  warnings: string[];
}

export interface AuditEntry {
  id: number;
  algo_key: string;
  actor: string;
  diff_json: Record<string, any>;
  created_at: string;
}

class AutopilotAPI {
  private client = axios.create({
    baseURL: `${API_BASE}/autopilot`,
    headers: {
      'Content-Type': 'application/json',
      'X-Role': 'admin', // TODO: Get from auth context
    },
  });

  async getAlgorithms(): Promise<{ algorithms: Algorithm[] }> {
    const response = await this.client.get('/algorithms');
    return response.data;
  }

  async getSettings(algoKey: string): Promise<AlgorithmSettings> {
    const response = await this.client.get(`/algorithms/${algoKey}/settings`);
    return response.data;
  }

  async updateSettings(
    algoKey: string,
    settings: Record<string, any>
  ): Promise<{ message: string; version: number; changes: number }> {
    const response = await this.client.put(`/algorithms/${algoKey}/settings`, settings);
    return response.data;
  }

  async getPolicy(algoKey: string): Promise<AIPolicy> {
    const response = await this.client.get(`/ai/policy/${algoKey}`);
    return response.data;
  }

  async updatePolicy(algoKey: string, policy: AIPolicy): Promise<{ message: string }> {
    const response = await this.client.put(`/ai/policy/${algoKey}`, policy);
    return response.data;
  }

  async triggerRun(algoKey: string): Promise<{ message: string; run_id: string; status: string }> {
    const response = await this.client.post(`/algorithms/${algoKey}/run`);
    return response.data;
  }

  async applyOverride(
    algoKey: string,
    overrideData: Record<string, any>
  ): Promise<{ message: string; override_id: string }> {
    const response = await this.client.post(`/algorithms/${algoKey}/override`, overrideData);
    return response.data;
  }

  async previewRun(algoKey: string): Promise<PreviewResponse> {
    const response = await this.client.get(`/algorithms/${algoKey}/preview`);
    return response.data;
  }

  async getAudit(algoKey: string, limit = 50): Promise<AuditEntry[]> {
    const response = await this.client.get(`/audit/${algoKey}?limit=${limit}`);
    return response.data;
  }
}

export const autopilotAPI = new AutopilotAPI();
export default autopilotAPI;
