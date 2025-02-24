from dotenv import load_dotenv

load_dotenv()

class Environment:
    PRODUCTION = "prod"
    TESTING = "testing"
    DEVELOPMENT = "dev"
    QA = "qa"
    STAGING = "stage"


def get_env_config(env):
    CONFIG_MAPPER = {
        "production": ProductionConfig,  # for terraform
        Environment.TESTING: TestingConfig,
        Environment.DEVELOPMENT: DevelopmentConfig,
        Environment.QA: QAConfig,
        Environment.STAGING: StagingConfig,
        Environment.PRODUCTION: ProductionConfig,
    }
    return CONFIG_MAPPER[env]

class BaseConfig:
    APP_SECRET_KEY = "base-secret-key"
    # Add other common configuration here

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    # Add development-specific configuration

class ProductionConfig(BaseConfig):
    DEBUG = False
    # Add production-specific configuration

class TestingConfig(BaseConfig):
    TESTING = True
    # Add testing-specific configuration

class QAConfig(BaseConfig):
    # Add QA-specific configuration
    pass

class StagingConfig(BaseConfig):
    # Add staging-specific configuration
    pass