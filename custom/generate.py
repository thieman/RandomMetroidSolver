import datetime
import json
import subprocess
import os
import random

import requests

BATCH_SIZE = 10

TARGET_USER = "deck"
TARGET_HOST = "deck.lan"
TARGET_PATH = "/run/media/mmcblk0p1/Emulation/roms/snes/Super_Metroid_VARIA/"

SKILL_PRESET_PATH = "skill.json"
ROM_PATH = "rom.sfc"
PLAYLIST_PATH = "playlist.json"
RANDO_PRESET_PATH = os.path.abspath("../rando_presets/default.json")

PRESET_NAME = "TNTregular"


def additional_params():
    return {
        "majorsSplit": "Full",
        "music": PLAYLIST_PATH,
        "sprite": random_samus_sprite(),
        "ship": random_ship_sprite(),
        "palette": True,
        "min_degree": 90,
        "max_degree": 90,
        "invert": True,
        "no_shift_suit_palettes": True,
        "patch": ["refill_before_save.ips", "max_ammo_display.ips", "itemsounds.ips"],
        "progressionSpeed": "medium",
        "progressionDifficulty": "normal",
        "morphPlacement": "normal",
    }


def random_samus_sprite():
    name = random.choice(
        [
            "hack_ancient_chozo",
            "hack_ascent",
            "hack_decision",
            "hack_escape2",
            "hack_hyper",
            "hack_kaizo",
            "hack_nature",
            "hack_opposition",
            "hack_phazon",
            "hack_redesign",
            "hack_szm",
            "samus",
            "zero_mission",
            "trans",
            "enby",
            "dark_samus",
            "dread",
            "combat_armor_samus",
            "fusion_green_varia",
            "fusion_orange_varia",
        ]
    )
    return f"{name}.ips"


def random_ship_sprite():
    name = random.choice(
        [
            "MFFusionship",
            "Red-M0nk3ySMShip4",
            "enterprise",
            "lastresort_ship",
            "minitroid_ship",
            "the_baby",
            "Red-M0nk3ySMShip1",
            "Red-M0nk3ySMShip2",
            "Red-M0nk3ySMShip3",
            "Red-M0nk3ySMShip5",
            "am2r_ship",
            "ascent_ship",
            "hyperion_ship",
            "ice_metal_ship",
            "kirbyship",
            "lost_world_ship",
            "mario_ship",
            "metalslug_ship",
            "opposition_ship",
            "phazon_ship",
            "pocket_rocket",
            "top_hunter_ship",
            "xwing",
        ]
    )
    return f"{name}.ips"


def download_skill_preset():
    r = requests.post(
        "https://randommetroidsolver.pythonanywhere.com/presetWebService",
        data={"preset": PRESET_NAME},
    )
    r.raise_for_status()
    with open(SKILL_PRESET_PATH, "w") as f:
        json.dump(r.json(), f)


def clear_target():
    pass


def randomize():
    call = f"../randomizer.py -r {ROM_PATH} --param {SKILL_PRESET_PATH} --randoPreset {RANDO_PRESET_PATH}"
    for k, v in additional_params().items():
        if isinstance(v, bool):
            call += f" --{k}"
        elif isinstance(v, list):
            for i in v:
                call += f" --{k} {i}"
        else:
            call += f" --{k} {v}"
    subprocess.check_call(call, shell=True)
    for f in os.listdir():
        if f.startswith("VARIA") and f.endswith(".sfc"):
            return f


def upload():
    call = f"rsync --delete --recursive Super_VARIA*.sfc {TARGET_USER}@{TARGET_HOST}:{TARGET_PATH}"
    subprocess.check_call(call, shell=True)


def clean():
    for f in os.listdir():
        if f.startswith("Super_VARIA") and f.endswith(".sfc"):
            os.remove(f)


def main():
    download_skill_preset()
    clear_target()
    dt = datetime.datetime.now().strftime("%Y%m%d")
    for idx in range(BATCH_SIZE):
        rom_path = randomize()
        os.rename(rom_path, f"Super_VARIA_{dt}_{idx+1}.sfc")
    upload()
    clean()


if __name__ == "__main__":
    main()
