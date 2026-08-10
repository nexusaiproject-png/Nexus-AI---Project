from app.integrations.gmail_factory import GmailClientFactory


class FakeTransport:
    async def list_messages(self, max_results, query):
        return {"max_results": max_results, "query": query}

    async def get_message(self, message_id):
        return {"id": message_id}


def test_factory_builds_client_adapter_with_account_credentials() -> None:
    calls: list[tuple[str, str]] = []

    def make_transport(account_id: str, access_token: str) -> FakeTransport:
        calls.append((account_id, access_token))
        return FakeTransport()

    client = GmailClientFactory(make_transport).create("account-1", "token-1")

    assert calls == [("account-1", "token-1")]
