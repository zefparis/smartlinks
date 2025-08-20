"""Policy-as-Code loader, validator, and differ."""

import yaml
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pydantic import ValidationError

from .schemas import (
    PacPolicy, PacValidationResult, PacPlanDiff, PacPlan, PacPlanCreate
)
from ..rcp.repository import RCPRepository
from ..rcp.schemas import RCPPolicy

class PacLoader:
    """Policy-as-Code loader and validator."""
    
    def __init__(self, rcp_repository: RCPRepository):
        self.rcp_repo = rcp_repository
    
    def validate_yaml(self, yaml_content: str) -> PacValidationResult:
        """Validate YAML policies and return normalized result."""
        errors = []
        warnings = []
        policies = []
        
        try:
            # Parse YAML
            docs = list(yaml.safe_load_all(yaml_content))
            
            for i, doc in enumerate(docs):
                if not doc:
                    continue
                    
                try:
                    # Validate against schema
                    policy = PacPolicy(**doc)
                    policies.append(policy)
                    
                    # Additional validation
                    self._validate_policy_logic(policy, warnings)
                    
                except ValidationError as e:
                    errors.append(f"Document {i+1}: {str(e)}")
                except Exception as e:
                    errors.append(f"Document {i+1}: Unexpected error - {str(e)}")
        
        except yaml.YAMLError as e:
            errors.append(f"YAML parsing error: {str(e)}")
        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")
        
        return PacValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            normalized=policies if len(errors) == 0 else None
        )
    
    def _validate_policy_logic(self, policy: PacPolicy, warnings: List[str]):
        """Validate policy business logic."""
        spec = policy.spec
        
        # Check rollout percentage
        if spec.rollout_percentage < 0 or spec.rollout_percentage > 100:
            warnings.append(f"Policy {policy.metadata.id}: rollout_percentage should be 0-100")
        
        # Check algorithm scope
        if spec.scope == "algorithm" and not spec.algo_key:
            warnings.append(f"Policy {policy.metadata.id}: algo_key required for algorithm scope")
        
        # Check selector consistency
        if spec.scope == "global" and spec.selector:
            warnings.append(f"Policy {policy.metadata.id}: selector ignored for global scope")
        
        # Check guard conflicts
        if spec.hard_guards and spec.soft_guards:
            if (spec.hard_guards.weight_delta_max and 
                spec.soft_guards.two_man_rule_threshold and
                spec.hard_guards.weight_delta_max < spec.soft_guards.two_man_rule_threshold):
                warnings.append(f"Policy {policy.metadata.id}: hard guard stricter than soft guard threshold")
    
    async def create_plan(self, plan_request: PacPlanCreate) -> Tuple[PacPlan, PacPlanDiff]:
        """Create deployment plan by diffing against current state."""
        
        # Get current policies
        current_policies = await self.rcp_repo.list_policies()
        current_by_id = {p.id: p for p in current_policies}
        
        # Calculate diff
        diff = PacPlanDiff()
        
        for pac_policy in plan_request.policies:
            policy_id = pac_policy.metadata.id
            
            if policy_id not in current_by_id:
                # New policy
                diff.create.append(policy_id)
            else:
                # Check if policy changed
                current_policy = current_by_id[policy_id]
                if self._policies_differ(pac_policy.spec, current_policy):
                    diff.update.append(policy_id)
        
        # Find deleted policies (not in new set)
        new_ids = {p.metadata.id for p in plan_request.policies}
        for policy_id in current_by_id:
            if policy_id not in new_ids:
                diff.delete.append(policy_id)
        
        # Create plan
        plan_id = self._generate_plan_id(plan_request.author)
        plan = PacPlan(
            id=plan_id,
            author=plan_request.author,
            diff=diff.dict(),
            dry_run=plan_request.dry_run,
            status="pending",
            created_at=datetime.utcnow()
        )
        
        return plan, diff
    
    def _policies_differ(self, new_policy: RCPPolicy, current_policy: RCPPolicy) -> bool:
        """Check if two policies differ significantly."""
        # Compare key fields (excluding version, timestamps)
        new_dict = new_policy.dict(exclude={'version', 'updated_at', 'updated_by'})
        current_dict = current_policy.dict(exclude={'version', 'updated_at', 'updated_by'})
        
        return new_dict != current_dict
    
    async def apply_plan(self, plan: PacPlan, policies: List[PacPolicy]) -> bool:
        """Apply deployment plan."""
        try:
            diff = PacPlanDiff(**plan.diff)
            
            # Apply creates and updates
            for pac_policy in policies:
                policy_id = pac_policy.metadata.id
                
                if policy_id in diff.create or policy_id in diff.update:
                    # Convert PacPolicy to RCPPolicy
                    rcp_policy = pac_policy.spec
                    rcp_policy.id = policy_id
                    
                    if policy_id in diff.create:
                        await self.rcp_repo.create_policy(rcp_policy)
                    else:
                        await self.rcp_repo.update_policy(policy_id, rcp_policy)
            
            # Apply deletes
            for policy_id in diff.delete:
                await self.rcp_repo.delete_policy(policy_id)
            
            return True
            
        except Exception as e:
            # Log error to plan
            plan.error_message = str(e)
            plan.status = "failed"
            return False
    
    def export_policies(self, policies: List[RCPPolicy]) -> str:
        """Export policies to YAML format."""
        docs = []
        
        for policy in policies:
            pac_policy = PacPolicy(
                metadata={"id": policy.id},
                spec=policy
            )
            docs.append(pac_policy.dict())
        
        return yaml.dump_all(docs, default_flow_style=False, sort_keys=False)
    
    def _generate_plan_id(self, author: str) -> str:
        """Generate unique plan ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        hash_input = f"{author}_{timestamp}_{datetime.utcnow().microsecond}"
        hash_suffix = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"plan_{timestamp}_{hash_suffix}"

class PacDiffer:
    """Policy differ for showing changes."""
    
    @staticmethod
    def diff_policies(old: Optional[RCPPolicy], new: Optional[RCPPolicy]) -> Dict[str, Any]:
        """Generate detailed diff between two policies."""
        if old is None and new is None:
            return {"type": "no_change"}
        
        if old is None:
            return {
                "type": "create",
                "policy": new.dict()
            }
        
        if new is None:
            return {
                "type": "delete",
                "policy": old.dict()
            }
        
        # Compare fields
        old_dict = old.dict(exclude={'version', 'updated_at', 'updated_by'})
        new_dict = new.dict(exclude={'version', 'updated_at', 'updated_by'})
        
        if old_dict == new_dict:
            return {"type": "no_change"}
        
        # Find specific changes
        changes = {}
        for key in set(old_dict.keys()) | set(new_dict.keys()):
            old_val = old_dict.get(key)
            new_val = new_dict.get(key)
            
            if old_val != new_val:
                changes[key] = {
                    "old": old_val,
                    "new": new_val
                }
        
        return {
            "type": "update",
            "changes": changes
        }

class PacCLI:
    """Command-line interface for Policy-as-Code."""
    
    def __init__(self, loader: PacLoader):
        self.loader = loader
    
    async def validate_command(self, file_path: str) -> None:
        """Validate policies from file."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            result = self.loader.validate_yaml(content)
            
            if result.valid:
                print(f"✅ Validation passed for {len(result.normalized)} policies")
                if result.warnings:
                    print("⚠️  Warnings:")
                    for warning in result.warnings:
                        print(f"  - {warning}")
            else:
                print("❌ Validation failed:")
                for error in result.errors:
                    print(f"  - {error}")
                    
        except FileNotFoundError:
            print(f"❌ File not found: {file_path}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    async def plan_command(self, file_path: str, author: str, dry_run: bool = True) -> None:
        """Create deployment plan."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Validate first
            validation = self.loader.validate_yaml(content)
            if not validation.valid:
                print("❌ Validation failed, cannot create plan")
                return
            
            # Create plan
            plan_request = PacPlanCreate(
                policies=validation.normalized,
                dry_run=dry_run,
                author=author
            )
            
            plan, diff = await self.loader.create_plan(plan_request)
            
            print(f"📋 Plan {plan.id} created")
            print(f"📊 Changes: {diff.total_changes}")
            print(f"  - Create: {len(diff.create)}")
            print(f"  - Update: {len(diff.update)}")
            print(f"  - Delete: {len(diff.delete)}")
            
            if dry_run:
                print("🔍 Dry run mode - no changes will be applied")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    async def apply_command(self, plan_id: str) -> None:
        """Apply deployment plan."""
        # Implementation would load plan from database and apply
        print(f"🚀 Applying plan {plan_id}...")
        # TODO: Implement plan application
