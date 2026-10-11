# AWS and Observability Requirements

The customer-facing V1 supports AWS planning only. The planner selects the cheapest, simplest viable AWS design and must not default to EKS.

Every executable customer plan will include Prometheus-compatible metrics collection and Grafana dashboards. The plan must state scrape targets, dashboard access controls, costs, and limitations. Local Compose already runs Prometheus and Grafana; customer-cloud monitoring resources are planned, not executed.

AWS estimates are ranges based on dated catalog assumptions. They are not AWS bills. A real AWS connection uses a customer-created, short-lived STS role for read-only discovery before any separately approved execution role exists.
