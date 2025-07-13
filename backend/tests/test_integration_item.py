from integrations.integration_item import IntegrationItem

def test_clean_dict_drops_defaults():
    item = IntegrationItem(
        id="123",
        type="HubSpotContact",
        name="Test",
        email="test@example.com",
        directory=False,
        visibility=True
    )
    result = item.to_clean_dict()
    assert "directory" not in result
    assert "visibility" not in result
    assert result["email"] == "test@example.com"
