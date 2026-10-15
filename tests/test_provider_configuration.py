from agentconstruct.providers import ProviderConfiguration


def test_provider_defaults_are_local_and_safe():
    config = ProviderConfiguration("local", "disabled", "manual", "local", None)
    assert config.validation_errors(hosted=False) == []
    assert config.validation_errors(hosted=True) == ["hosted mode requires google_workspace or cognito identity"]


def test_google_workspace_requires_a_verified_domain_configuration():
    config = ProviderConfiguration("google_workspace", "gmail_api", "manual", "local", None)
    assert config.validation_errors(hosted=True) == ["Google Workspace identity requires AGENTCONSTRUCT_GOOGLE_WORKSPACE_DOMAIN"]
