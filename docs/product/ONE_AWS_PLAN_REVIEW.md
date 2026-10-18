# One AWS Plan Review

davdeploy evaluates its small AWS catalogue internally. The customer sees one selected design, not a menu of cloud providers or competing deployment cards.

The selected design must meet the typed request, security constraints, hard budget and availability requirements. Within the cheapest viable cost band, the planner chooses the lowest operational-complexity design. Kubernetes is not the default.

Each review draft binds the selected repository branch, AWS target, region, workload specification, available discovery snapshot and policy result. It shows the application analysis, resources, security controls, Prometheus-compatible metrics, Amazon Managed Grafana, cost range, deployment strategy, risks and limitations.

Every selected plan includes Prometheus-compatible metrics and Grafana. The current estimate is a local pricing fixture. The review is a draft only: it does not submit, approve or deploy cloud resources.
