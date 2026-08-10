from dataclasses import dataclass


@dataclass(frozen=True)
class OAuthToken:
    access_token: str
    refresh_token: str | None = None


class InMemoryTokenStore:
    def __init__(self) -> None:
        self._tokens: dict[str, OAuthToken] = {}

    async def get(self, account_id: str) -> OAuthToken | None:
        return self._tokens.get(account_id)

    async def set(self, account_id: str, token: OAuthToken) -> None:
        self._tokens[account_id] = token

    async def delete(self, account_id: str) -> None:
        self._tokens.pop(account_id, None)
