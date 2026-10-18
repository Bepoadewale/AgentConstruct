# Argo CD contract

`davdeploy-application.yaml` is a static contract for future GitOps delivery. A future approved worker will publish a reviewed desired-state change; Argo CD will reconcile it and the observer will report the resulting state. The local V1 executor does not run Argo CD or Kubernetes.
