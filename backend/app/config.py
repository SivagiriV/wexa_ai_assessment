import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    COGNODB_URI: str = os.environ.get("COGNODB_URI", "")
    COGNODB_USER: str = os.environ.get("COGNODB_USER", "cognodb")
    COGNODB_PASSWORD: str = os.environ.get("COGNODB_PASSWORD", "")
    COGNODB_DATABASE: str = os.environ.get("COGNODB_DATABASE", "neo4j")
    CORS_ORIGINS: list[str] = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")

    def validate(self) -> list[str]:
        missing = []
        if not self.COGNODB_URI:
            missing.append("COGNODB_URI")
        if not self.COGNODB_PASSWORD:
            missing.append("COGNODB_PASSWORD")
        return missing


settings = Settings()
