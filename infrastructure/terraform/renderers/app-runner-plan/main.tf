module "agentconstruct_app_runner_plan_contract" {
  source = "../../modules/app-runner-plan-contract"

  project_id                = "fixture-project"
  revision_id               = "fixture-revision"
  source_deployment_plan_id = "fixture-deployment-plan"
  plan_digest               = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
  profile                   = "aws-app-runner"
  service_name              = "agentconstruct-fastapi"
  repository_url            = "https://github.com/example/fastapi-ai-api"
  repository_branch         = "main"
  aws_account_id            = "customer-account-selected-at-apply-time"
  aws_region                = "us-east-1"
  source_boundary           = "Plan-only contract. A later reviewed build must publish an immutable image before any execution."
  image_repository          = "customer-account-selected-at-apply-time.dkr.ecr.us-east-1.amazonaws.com/agentconstruct-fastapi"

  environment_variables = {
    AGENTCONSTRUCT_PLAN_DIGEST = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    AGENTCONSTRUCT_PROFILE     = "aws-app-runner"
    APP_ENVIRONMENTS           = "staging,production"
  }

  secret_references = {
    application = "aws-secretsmanager://agentconstruct/app-runner/application"
  }

  https_access = {
    ingress               = "managed App Runner HTTPS endpoint"
    custom_domain         = "optional later Route 53/ACM contract"
    private_data_boundary = "customer data remains in the selected AWS account"
  }

  iam = {
    runtime_role    = "least-privilege App Runner instance role"
    deployment_role = "future explicit execution role; unavailable in this local renderer"
  }

  observability = {
    metrics_backend = "Prometheus-compatible metrics"
    grafana         = "Amazon Managed Grafana"
    scrape_targets = [
      "app-runner-service",
      "application-/metrics",
    ]
    baseline_dashboard = {
      title  = "AgentConstruct App Runner baseline"
      panels = ["request rate", "latency", "error rate", "service health"]
    }
    access_boundary = "private authenticated Grafana access; no public unauthenticated dashboards"
    limitations     = ["plan-only contract; metrics are not collected until an approved runtime exists"]
    cost_assumption = "monitoring estimate is a planning assumption, not an AWS bill"
  }

  tags = {
    ManagedBy                = "AgentConstruct"
    AgentConstructPlanDigest = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    AgentConstructProjectId  = "fixture-project"
    AgentConstructRevisionId = "fixture-revision"
    AgentConstructProfile    = "aws-app-runner"
  }
}

output "contract" {
  value = module.agentconstruct_app_runner_plan_contract.contract
}

output "execution_boundary" {
  value = module.agentconstruct_app_runner_plan_contract.execution_boundary
}
