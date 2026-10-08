# AWS Load Balancer Controller contract

The internal Ingress in `infrastructure/kubernetes/base/ingress.yaml` requires AWS Load Balancer Controller. A future runtime bootstrap installs a version-pinned controller chart with a dedicated IRSA service account and the AWS-maintained least-privilege policy for the selected controller version.

It is intentionally not installed or granted permissions by the local product. Before a cloud pilot, pin the controller version, vendor/review the corresponding AWS policy JSON, scope it to the pilot VPC/subnets/tags, and record the resulting role ARN in the runtime overlay.
