import datetime
import json
import subprocess
import os
import random

import requests

BATCH_SIZE = 5

TARGET_USER = "deck"
TARGET_HOST = "deck.lan"
TARGET_PATH = "/run/media/mmcblk0p1/Emulation/roms/snes/Super_Metroid_VARIA/"

SKILL_PRESET_PATH = "skill.json"
ROM_PATH = "rom.sfc"
PLAYLIST_PATH = "playlist.json"
PATCHED_PLAYLIST_PATH = "playlist_patched.json"
RANDO_PRESET_PATH = os.path.abspath("../rando_presets/default.json")

PRESET_NAME = "TNTregular"


def patch_music_json():
    with open(PLAYLIST_PATH, "r") as f:
        data = json.load(f)
    mapping = {
        "Titlesequenceintro": "Title sequence intro",
        "Menutheme": "Menu theme",
        "CrateriaLandingThunderZebesasleep": "Crateria Landing - Thunder, Zebes asleep",
        "CrateriaLandingThunderZebesawake": "Crateria Landing - Thunder, Zebes awake",
        "CrateriaLandingNoThunder": "Crateria Landing - No Thunder",
        "CrateriaPirates": "Crateria Pirates",
        "TourianEntrance": "Tourian Entrance",
        "SamusTheme": "Samus Theme",
        "GreenBrinstar": "Green Brinstar",
        "RedBrinstar": "Red Brinstar",
        "UpperNorfair": "Upper Norfair",
        "LowerNorfair": "Lower Norfair",
        "EastMaridia": "East Maridia",
        "WestMaridia": "West Maridia",
        "TourianBubbles": "Tourian Bubbles",
        "MotherBrain2": "Mother Brain 2",
        "EscapeSequence": "Escape Sequence",
        "BossfightSporeSpawnBotwoon": "Boss fight - Botwoon",
        "WreckedShipPoweroff": "Wrecked Ship - Power off",
        "WreckedShipPoweron": "Wrecked Ship - Power on",
        "EndingCredits": "Ending/Credits",
        "MotherBrain3": "Mother Brain 3",
    }

    patched = {
        "params": {"varia": True, "area": True, "boss": True},
        "mapping": {},
    }

    for k, v in data.items():
        if k in mapping:
            patched["mapping"][mapping[k]] = v

    with open(PATCHED_PLAYLIST_PATH, "w") as f:
        json.dump(patched, f)


def randomizer_params():
    return {
        "majorsSplit": "Full",
        "progressionSpeed": "medium",
        "progressionDifficulty": "normal",
        "morphPlacement": "normal",
        "startLocation": "random",
        "maxDifficulty": "hardcore",
        "suitsRestriction": True,
        "missileQty": 3,
        "superQty": 2,
        "powerBombQty": 1,
        "minorQty": 100,
        "energyQty": "vanilla",
        "objective": ["kill all G4"],
        "tourian": "Vanilla",
        "startLocationList": ",".join(
            [
                "Gauntlet Top",
                "Green Brinstar Elevator",
                "Big Pink",
                "Etecoons Supers",
                "Wrecked Ship Main",
                "Firefleas Top",
                "Business Center",
                "Bubble Mountain",
                "Mama Turtle",
                "Watering Hole",
                "Aqueduct",
                "Red Brinstar Elevator",
                "Golden Four",
            ]
        ),
        "controls": "Y,B,A,X,Select,R,L",
    }


def customizer_params():
    return {
        "music": PATCHED_PLAYLIST_PATH,
        "sprite": random_samus_sprite(),
        "ship": random_ship_sprite(),
        "palette": True,
        "min_degree": -90,
        "max_degree": 90,
        "invert": True,
        "no_shift_suit_palettes": True,
        "patch": [
            "refill_before_save.ips",
            "max_ammo_display.ips",
            "itemsounds.ips",
            "fast_doors.ips",
            "elevators_speed.ips",
        ],
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
    call = f"../randomizer.py -r {ROM_PATH} --param {SKILL_PRESET_PATH}"
    for k, v in randomizer_params().items():
        if isinstance(v, bool):
            call += f" --{k}"
        elif isinstance(v, list):
            for i in v:
                call += f" --{k} '{i}'"
        else:
            call += f" --{k} '{v}'"
    subprocess.check_call(call, shell=True)
    for f in os.listdir():
        if f.startswith("VARIA") and f.endswith(".sfc"):
            return f


def customize(rom_path):
    call = f"../randomizer.py --rom {rom_path} --patchOnly"
    for k, v in customizer_params().items():
        if isinstance(v, bool):
            call += f" --{k}"
        elif isinstance(v, list):
            for i in v:
                call += f" --{k} {i}"
        else:
            call += f" --{k} {v}"
    subprocess.check_call(call, shell=True)
    os.rename("VARIA.sfc", rom_path)


def upload():
    call = f"rsync --include='Super*.sfc' --exclude='*' --delete-before --recursive Super_VARIA*.sfc {TARGET_USER}@{TARGET_HOST}:{TARGET_PATH}"
    subprocess.check_call(call, shell=True)


def clean():
    for f in os.listdir():
        if f.startswith("Super_VARIA") and f.endswith(".sfc"):
            os.remove(f)


def main():
    patch_music_json()
    download_skill_preset()
    clean()
    clear_target()
    dt = datetime.datetime.now().strftime("%Y%m%d")
    for idx in range(BATCH_SIZE):
        rom_path = randomize()
        customize(rom_path)
        os.rename(rom_path, f"Super_VARIA_{dt}_{idx+1}.sfc")
    upload()


if __name__ == "__main__":
    main()
