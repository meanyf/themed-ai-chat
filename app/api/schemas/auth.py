from pydantic import BaseModel, SecretStr


class LoginRequest(BaseModel):
    key: SecretStr
