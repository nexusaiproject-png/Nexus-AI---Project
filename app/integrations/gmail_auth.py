from dataclasses import dataclass

from app.integrations.oauth import InMemoryTokenStore, OAuthToken


@dataclass(frozen=True)
class GmailAccount:
    account_id: str
    email: str


class GmailAuthService:
    def __init__(self, token_store: InMemoryTokenStore) -> None:
        self._token_store = token_store

    async def connect(self, account: GmailAccount, access_token: str) -> None:
        await self._token_store.set(
            account.account_id,
            OAuthToken(access_token=access_token),
        )

    async def disconnect(self, account_id: str) -> None:
        await self._token_store.delete(account_id)

    async def is_connected(self, account_id: str) -> bool:
        return await self._token_store.get(account_id) is not None
