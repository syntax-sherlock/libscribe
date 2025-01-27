from src.ingestion.processing import create_namespace


def test_create_namespace_basic():
    assert create_namespace("owner", "repo") == "github_owner_repo"


def test_create_namespace_with_caps():
    assert create_namespace("Owner", "Repo") == "github_owner_repo"


def test_create_namespace_with_dashes():
    assert create_namespace("test-owner", "test-repo") == "github_test_owner_test_repo"


def test_create_namespace_mixed_case_and_dashes():
    assert create_namespace("Test-Owner", "Test-Repo") == "github_test_owner_test_repo"
