# App Runner plan-only renderer

This root exists so CI can run `terraform init -backend=false` and
`terraform validate` against the App Runner contract without creating AWS
resources.

It is not a deployment root. It has no AWS provider, backend, resources, apply
command, or customer credentials.
