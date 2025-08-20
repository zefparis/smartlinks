/**
 * Settings modal component for algorithm configuration
 */

import React, { useState, useEffect } from 'react';
import { X, Settings, Save, RotateCcw, Play, Eye, AlertTriangle } from 'lucide-react';
import autopilotAPI, { Algorithm, AlgorithmSettings, AIPolicy, PreviewResponse } from '@/api/autopilot';

interface SettingsSheetProps {
  algorithm: Algorithm;
  children: React.ReactNode;
}

export function SettingsSheet({ algorithm, children }: SettingsSheetProps) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [settings, setSettings] = useState<AlgorithmSettings | null>(null);
  const [policy, setPolicy] = useState<AIPolicy | null>(null);
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [activeTab, setActiveTab] = useState('common');
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    if (open) {
      loadData();
    }
  }, [open, algorithm.key]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [settingsData, policyData] = await Promise.all([
        autopilotAPI.getSettings(algorithm.key),
        autopilotAPI.getPolicy(algorithm.key),
      ]);
      setSettings(settingsData);
      setPolicy(policyData);
      setHasChanges(false);
    } catch (error) {
      toast.error('Failed to load settings');
      console.error('Settings load error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!settings || !policy) return;

    setLoading(true);
    try {
      await Promise.all([
        autopilotAPI.updateSettings(algorithm.key, settings.settings),
        autopilotAPI.updatePolicy(algorithm.key, policy),
      ]);
      toast.success('Settings saved successfully');
      setHasChanges(false);
    } catch (error) {
      toast.error('Failed to save settings');
      console.error('Settings save error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = async () => {
    setLoading(true);
    try {
      const previewData = await autopilotAPI.previewRun(algorithm.key);
      setPreview(previewData);
      setActiveTab('preview');
    } catch (error) {
      toast.error('Failed to generate preview');
      console.error('Preview error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRun = async () => {
    setLoading(true);
    try {
      const result = await autopilotAPI.triggerRun(algorithm.key);
      toast.success(`Algorithm run triggered: ${result.run_id}`);
      setOpen(false);
    } catch (error) {
      toast.error('Failed to trigger algorithm run');
      console.error('Run error:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateSetting = (path: string, value: any) => {
    if (!settings) return;
    
    const newSettings = { ...settings };
    const keys = path.split('.');
    let current = newSettings.settings;
    
    for (let i = 0; i < keys.length - 1; i++) {
      current = current[keys[i]];
    }
    current[keys[keys.length - 1]] = value;
    
    setSettings(newSettings);
    setHasChanges(true);
  };

  const updatePolicy = (field: keyof AIPolicy, value: any) => {
    if (!policy) return;
    setPolicy({ ...policy, [field]: value });
    setHasChanges(true);
  };

  const renderCommonSettings = () => {
    if (!settings) return null;

    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Basic Configuration</CardTitle>
            <CardDescription>Core algorithm settings</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="active">Algorithm Active</Label>
              <Switch
                id="active"
                checked={settings.settings.active || false}
                onCheckedChange={(checked) => updateSetting('active', checked)}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="interval">Run Interval (seconds)</Label>
              <Input
                id="interval"
                type="number"
                value={settings.settings.interval_seconds || 300}
                onChange={(e) => updateSetting('interval_seconds', parseInt(e.target.value))}
                min={60}
                max={3600}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="cooldown">Cooldown (seconds)</Label>
              <Input
                id="cooldown"
                type="number"
                value={settings.settings.cooldown_seconds || 120}
                onChange={(e) => updateSetting('cooldown_seconds', parseInt(e.target.value))}
                min={30}
                max={600}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="dry_run">Dry Run Mode</Label>
              <Switch
                id="dry_run"
                checked={settings.settings.dry_run || false}
                onCheckedChange={(checked) => updateSetting('dry_run', checked)}
              />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  const renderAdvancedSettings = () => {
    if (!settings) return null;

    // Render algorithm-specific settings based on schema
    const schema = settings.schema;
    const properties = schema.properties || {};

    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Advanced Configuration</CardTitle>
            <CardDescription>Algorithm-specific parameters</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {Object.entries(properties).map(([key, prop]: [string, any]) => {
              if (['active', 'interval_seconds', 'cooldown_seconds', 'dry_run'].includes(key)) {
                return null; // Skip common settings
              }

              const value = settings.settings[key];
              
              if (prop.type === 'boolean') {
                return (
                  <div key={key} className="flex items-center justify-between">
                    <Label htmlFor={key}>{prop.title || key}</Label>
                    <Switch
                      id={key}
                      checked={value || false}
                      onCheckedChange={(checked) => updateSetting(key, checked)}
                    />
                  </div>
                );
              }

              if (prop.type === 'number') {
                return (
                  <div key={key} className="space-y-2">
                    <Label htmlFor={key}>{prop.title || key}</Label>
                    {prop.minimum !== undefined && prop.maximum !== undefined ? (
                      <div className="space-y-2">
                        <Slider
                          value={[value || prop.default || 0]}
                          onValueChange={([newValue]) => updateSetting(key, newValue)}
                          min={prop.minimum}
                          max={prop.maximum}
                          step={0.01}
                          className="w-full"
                        />
                        <div className="text-sm text-muted-foreground">
                          {value || prop.default || 0} ({prop.minimum} - {prop.maximum})
                        </div>
                      </div>
                    ) : (
                      <Input
                        id={key}
                        type="number"
                        value={value || prop.default || 0}
                        onChange={(e) => updateSetting(key, parseFloat(e.target.value))}
                      />
                    )}
                  </div>
                );
              }

              if (prop.enum) {
                return (
                  <div key={key} className="space-y-2">
                    <Label htmlFor={key}>{prop.title || key}</Label>
                    <Select value={value || prop.default} onValueChange={(newValue) => updateSetting(key, newValue)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {prop.enum.map((option: string) => (
                          <SelectItem key={option} value={option}>
                            {option}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                );
              }

              return (
                <div key={key} className="space-y-2">
                  <Label htmlFor={key}>{prop.title || key}</Label>
                  <Input
                    id={key}
                    value={typeof value === 'object' ? JSON.stringify(value) : value || ''}
                    onChange={(e) => {
                      try {
                        const parsed = JSON.parse(e.target.value);
                        updateSetting(key, parsed);
                      } catch {
                        updateSetting(key, e.target.value);
                      }
                    }}
                  />
                </div>
              );
            })}
          </CardContent>
        </Card>
      </div>
    );
  };

  const renderAIGovernance = () => {
    if (!policy) return null;

    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>AI Authority & Risk Management</CardTitle>
            <CardDescription>DG AI governance controls</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="authority">Authority Level</Label>
              <Select value={policy.authority} onValueChange={(value) => updatePolicy('authority', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="advisory">Advisory Only</SelectItem>
                  <SelectItem value="safe_apply">Safe Apply</SelectItem>
                  <SelectItem value="full_control">Full Control</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="risk_budget">Daily Risk Budget</Label>
              <Input
                id="risk_budget"
                type="number"
                value={policy.risk_budget_daily}
                onChange={(e) => updatePolicy('risk_budget_daily', parseInt(e.target.value))}
                min={0}
                max={100}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="ai_dry_run">AI Dry Run Mode</Label>
              <Switch
                id="ai_dry_run"
                checked={policy.dry_run}
                onCheckedChange={(checked) => updatePolicy('dry_run', checked)}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Safety Guards</CardTitle>
            <CardDescription>Hard and soft limits for AI actions</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Hard Guards (JSON)</Label>
              <textarea
                className="w-full h-24 p-2 border rounded-md font-mono text-sm"
                value={JSON.stringify(policy.hard_guards, null, 2)}
                onChange={(e) => {
                  try {
                    const parsed = JSON.parse(e.target.value);
                    updatePolicy('hard_guards', parsed);
                  } catch {
                    // Invalid JSON, ignore
                  }
                }}
              />
            </div>

            <div className="space-y-2">
              <Label>Soft Guards (JSON)</Label>
              <textarea
                className="w-full h-24 p-2 border rounded-md font-mono text-sm"
                value={JSON.stringify(policy.soft_guards, null, 2)}
                onChange={(e) => {
                  try {
                    const parsed = JSON.parse(e.target.value);
                    updatePolicy('soft_guards', parsed);
                  } catch {
                    // Invalid JSON, ignore
                  }
                }}
              />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  const renderPreview = () => {
    if (!preview) return null;

    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Proposed Actions</CardTitle>
            <CardDescription>Preview of algorithm actions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {preview.actions.map((action, index) => (
                <div key={index} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <Badge variant="outline">{action.action_type}</Badge>
                    <Badge variant={action.risk_score > 0.5 ? "destructive" : "secondary"}>
                      Risk: {(action.risk_score * 100).toFixed(0)}%
                    </Badge>
                  </div>
                  <div className="text-sm space-y-1">
                    <div><strong>Target:</strong> {action.target}</div>
                    <div><strong>Change:</strong> {action.current_value} → {action.proposed_value}</div>
                    <div><strong>Reason:</strong> {action.justification}</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Impact Estimate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(preview.estimated_impact).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="capitalize">{key.replace('_', ' ')}:</span>
                  <span className="font-mono">{value}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {preview.warnings.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-yellow-500" />
                Warnings
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-1">
                {preview.warnings.map((warning, index) => (
                  <li key={index} className="text-sm text-yellow-600">
                    • {warning}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        {children}
      </SheetTrigger>
      <SheetContent className="w-[600px] sm:w-[800px]">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            {algorithm.name} Settings
          </SheetTitle>
          <SheetDescription>
            Configure algorithm parameters and AI governance policies
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 h-full flex flex-col">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="common">Common</TabsTrigger>
              <TabsTrigger value="advanced">Advanced</TabsTrigger>
              <TabsTrigger value="ai">DG AI</TabsTrigger>
              <TabsTrigger value="preview">Preview</TabsTrigger>
            </TabsList>

            <ScrollArea className="flex-1 mt-4">
              <TabsContent value="common" className="mt-0">
                {renderCommonSettings()}
              </TabsContent>

              <TabsContent value="advanced" className="mt-0">
                {renderAdvancedSettings()}
              </TabsContent>

              <TabsContent value="ai" className="mt-0">
                {renderAIGovernance()}
              </TabsContent>

              <TabsContent value="preview" className="mt-0">
                {renderPreview()}
              </TabsContent>
            </ScrollArea>
          </Tabs>

          <Separator className="my-4" />

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handlePreview}
                disabled={loading}
              >
                <Eye className="h-4 w-4 mr-2" />
                Preview
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={loadData}
                disabled={loading}
              >
                <RotateCcw className="h-4 w-4 mr-2" />
                Reset
              </Button>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                onClick={handleRun}
                disabled={loading}
              >
                <Play className="h-4 w-4 mr-2" />
                Run Now
              </Button>
              <Button
                onClick={handleSave}
                disabled={loading || !hasChanges}
              >
                <Save className="h-4 w-4 mr-2" />
                Save Changes
              </Button>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
