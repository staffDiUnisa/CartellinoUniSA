import keyring
import keyring.errors

_SERVICE_NAME = "cartellino-unisa"
_USERNAME_ACCOUNT = "username"
_PASSWORD_ACCOUNT = "password"


def get_credentials() -> tuple[str, str] | None:
    username = keyring.get_password(_SERVICE_NAME, _USERNAME_ACCOUNT)
    password = keyring.get_password(_SERVICE_NAME, _PASSWORD_ACCOUNT)
    if not username or not password:
        return None
    return username, password


def set_credentials(username: str, password: str) -> None:
    keyring.set_password(_SERVICE_NAME, _USERNAME_ACCOUNT, username)
    keyring.set_password(_SERVICE_NAME, _PASSWORD_ACCOUNT, password)


def delete_credentials() -> None:
    for account in (_USERNAME_ACCOUNT, _PASSWORD_ACCOUNT):
        try:
            keyring.delete_password(_SERVICE_NAME, account)
        except keyring.errors.PasswordDeleteError:
            pass
