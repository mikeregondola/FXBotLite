from .fxcm_driver import FXCMDriver
from .sim_driver import SimDriver


def load_driver(config):

    mode = config.get("mode", "fxcm").lower()

    print(f"[BROKER] Loading driver mode: {mode}")

    if mode == "sim":
        driver = SimDriver(config)
    else:
        broker_cfg = config.get("broker", {})
        driver = FXCMDriver(broker_cfg)

    # attach full config (important)
    driver.full_config = config

    return driver