from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://cdp:cdppassword@localhost:5432/cdpdb"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # JWT
    jwt_secret_key: str = "changeme"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # External DB sources
    loyalty_db_url: str = ""
    sales_db_url: str = ""

    # Activation
    sendgrid_api_key: str = ""
    esms_api_key: str = ""
    esms_secret_key: str = ""
    esms_brand_name: str = ""
    meta_access_token: str = ""
    meta_ad_account_id: str = ""
    google_ads_developer_token: str = ""
    google_ads_customer_id: str = ""


settings = Settings()
