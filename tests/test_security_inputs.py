from unittest.mock import Mock, patch

import pytest
from fastapi.security import HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.errors import AppError
from app.core.security import require_api_key


def test_unicode_bearer_token_is_unauthorized_instead_of_a_server_error():
    request = Mock()
    with patch('app.core.security.ApiClientRepository') as repository:
        repository.return_value.get_by_token_hash.return_value = None
        with pytest.raises(AppError) as error:
            require_api_key(request, Mock(), HTTPAuthorizationCredentials(scheme='Bearer', credentials='é-invalid-key'))
    assert error.value.status_code == 401
    assert error.value.code == 'unauthorized'


def test_bootstrap_token_still_authenticates_without_database_lookup():
    request = Mock()
    with patch('app.core.security.ApiClientRepository') as repository:
        context = require_api_key(request, Mock(), HTTPAuthorizationCredentials(scheme='Bearer', credentials=settings.bootstrap_api_key))
    assert context.bootstrap is True
    assert request.state.auth is context
    repository.assert_not_called()
