def main(config_path: str = "clock_settings.yaml") -> None:
    from .app import main as app_main

    app_main(config_path=config_path)


__all__ = ["main"]
