
import os
from pathlib import Path

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

ALIASES = {
    "APP_PORT": "port",
    "APP_WORKERS": "workers",
    "APP_DEBUG": "debug",
    "APP_LOG_LEVEL": "log_level",
    "APP_API_KEY": "api_key",
    "NUM_WORKERS": "workers",
}

def coerce(key, value):
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        return str(value).strip().lower() in {
            "true", "1", "yes", "on"
        }
    return str(value)

@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = DEFAULTS.copy()

    env_name = os.getenv("APP_ENV", "development")
    yaml_path = Path(f"config.{env_name}.yaml")

    if yaml_path.exists():
        with yaml_path.open(encoding="utf-8") as f:
            config.update(yaml.safe_load(f) or {})

    for name, value in dotenv_values(".env").items():
        if value is not None:
            key = ALIASES.get(name, name.lower())
            if key in config:
                config[key] = coerce(key, value)

    for name, value in os.environ.items():
        if name.startswith("APP_"):
            key = ALIASES.get(name)
            if key and key in config:
                config[key] = coerce(key, value)

    for item in set:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        if key in config:
            config[key] = coerce(key, value)

    config["api_key"] = "****"
    return config
