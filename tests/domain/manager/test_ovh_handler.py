import pytest
import logging
import ovh
from unittest.mock import MagicMock, patch
from src.domain.manager.ovh_handler import OVHDomainManager


class TestOVHDomainManager:
    @pytest.fixture(autouse=True)
    def setup(self, application_credential):
        with patch("src.domain.manager.ovh_handler.ovh.Client") as MockClient:
            client_instance = MockClient.return_value
            client_instance.get.return_value = {"dummy_key": "dummy_value"}  # Mock default get return value
            self.ovh_manager = OVHDomainManager(domain="example.com", target="some-target",
                                                application_credential=application_credential)

    @pytest.fixture
    def application_credential(self):
        return {
            "application_key": "key",
            "application_secret": "secret",
            "consumer_key": "consumer"
        }

    def test_init(self):
        assert self.ovh_manager.domain == "example.com"
        assert self.ovh_manager.target == "some-target"
        assert self.ovh_manager.field_type == "CNAME"
        assert self.ovh_manager.domain_parts == ["example", "com"]
        assert self.ovh_manager.domain_length == 2
        assert self.ovh_manager.zone == {"dummy_key": "dummy_value"}  # From the mocked get call

    def test_create_subdomain(self):
        self.ovh_manager.client.post = MagicMock()
        self.ovh_manager.create_subdomain("testsub", ttl=300)
        self.ovh_manager.client.post.assert_called_once_with(
            f'/domain/zone/example.com/record',
            fieldType='CNAME',
            subDomain='testsub',
            target='some-target',
            ttl=300
        )

    def test_create_subdomain_api_error(self, caplog):
        self.ovh_manager.client.post = MagicMock(side_effect=ovh.exceptions.APIError("API failure"))
        with caplog.at_level(logging.ERROR):
            self.ovh_manager.create_subdomain("testsub")
            assert '[OVHDomainManager] Failed to create subdomain testsub.example.com: API failure' in caplog.text

    def test_remove_subdomain(self):
        self.ovh_manager.client.get = MagicMock(return_value=[1, 2, 3])
        self.ovh_manager.client.delete = MagicMock()
        self.ovh_manager.remove_subdomain("testsub")

        self.ovh_manager.client.get.assert_called_once_with(
            f'/domain/zone/example.com/record',
            fieldType='CNAME',
            subDomain='testsub'
        )
        assert self.ovh_manager.client.delete.call_count == 3

    def test_remove_subdomain_api_error(self, caplog):
        self.ovh_manager.client.get = MagicMock(return_value=[1])
        self.ovh_manager.client.delete = MagicMock(side_effect=ovh.exceptions.APIError("API failure"))
        with caplog.at_level(logging.ERROR):
            self.ovh_manager.remove_subdomain("testsub")
            assert '[OVHDomainManager] Failed to remove subdomain testsub.example.com: API failure' in caplog.text

    def test_handle_api_error(self, caplog):
        with caplog.at_level(logging.ERROR):
            error = Exception("API failure")
            self.ovh_manager.handle_api_error("create", "sub.example.com", error)
            assert "[OVHDomainManager] Failed to create subdomain sub.example.com: API failure" in caplog.text

    @patch('src.domain.manager.ovh_handler.ovh.Client')
    def test_validate_init_domain_raises_error(self, mock_client, application_credential):
        client_instance = mock_client.return_value
        client_instance.get.side_effect = ovh.exceptions.ResourceNotFoundError("This service does not exist")

        with pytest.raises(ovh.exceptions.ResourceNotFoundError) as exc_info:
            OVHDomainManager(domain="invalid.com", target="some-target", application_credential=application_credential)

        assert "This service does not exist" in str(exc_info.value)

    def test_validate_domain_success(self):
        self.ovh_manager.client.get = MagicMock(return_value={"zone": "example.com"})
        self.ovh_manager._validate_domain()
        self.ovh_manager.client.get.assert_called_once_with(f"/domain/zone/example.com")

    def test_validate_domain_raises_type_error(self):
        # Mock client.get to simulate a ResourceNotFoundError
        self.ovh_manager.client.get = MagicMock(side_effect=[
            ovh.exceptions.ResourceNotFoundError("Domain not found"),
            ["domain1.com", "domain2.com"]  # Mock available domains response
        ])
        with pytest.raises(TypeError) as exc_info:
            self.ovh_manager._validate_domain()

        assert "The domain 'example.com' does not exist! Available domains: ['domain1.com', 'domain2.com']" in str(exc_info.value)
