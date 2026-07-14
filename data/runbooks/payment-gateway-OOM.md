# Incident Post-Mortem: Payment Gateway OOMKilled
**Service:** payment-gateway
**Error Code:** OOMKilled
**Date:** 2026-05-12

## Root Cause Analysis
During peak traffic hours, the payment-gateway container exceeded its allocated memory limit of 1Gi. The Kubernetes scheduler terminated the pod with an OOMKilled exception. This was traced back to a memory leak in the batch processing queue.

## Resolution / Runbook
To remediate this issue, you must edit the Kubernetes deployment YAML. 
1. Locate the `resources.limits.memory` block.
2. Increase the memory limit from `1Gi` to `2Gi`.
3. Restart the deployment. 

Do not restart the database. Only bump the deployment limits.