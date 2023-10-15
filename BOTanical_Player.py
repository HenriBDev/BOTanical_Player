# Python libs
import os
import time
import logging
import copy
import threading

# External libs
import pyautogui as pg
from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), '.env'))

DEBUG_MODE = bool(os.environ.get("DEBUG_MODE"))

if DEBUG_MODE:

    # Creating logger
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()

    # Creating log type map
    LOG_LEVEL_MAP = {
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

EXECUTABLE_FILE_NAME = "PlantsVsZombies"
GAME_FULL_PATH = os.path.join(os.environ.get("PVZ_PATH"), EXECUTABLE_FILE_NAME)

FIRST_TILE_POSITION_FRONTYARD = (383.5, 233.5)
BOARD_ROWS_SPACING = 144
BOARD_COLUMNS_SPACING = 178
TILE_POSITIONS_FRONTYARD = [
    [(
        FIRST_TILE_POSITION_FRONTYARD[0] + (BOARD_ROWS_SPACING * current_row), 
        FIRST_TILE_POSITION_FRONTYARD[1] + (BOARD_COLUMNS_SPACING * current_col), 
    ) for current_row in range(5)]
for current_col in range(5)]

HORIZONTAL_SLOTS_SPACING_INGAME = 105
FIRST_SLOT_HORIZONTAL_POSITION_INGAME = 467.5
SLOT_VERTICAL_POSITION_INGAME = 20
SLOTS_POSITIONS = [
    (FIRST_SLOT_HORIZONTAL_POSITION_INGAME + (HORIZONTAL_SLOTS_SPACING_INGAME * current_slot), SLOT_VERTICAL_POSITION_INGAME)
for current_slot in range(8)]


CLEAN_FRONTYARD_BOARD = [[{
    "tile_type": "grass",
    "current_plant": None,
    "has_zombie": False,
    "can_be_planted_in": True
} for _ in range(5)] for _ in range(5)]

CLEAN_POOL_BOARD = [[{
    "tile_type": "grass",
    "current_plant": None,
    "has_zombie": False,
    "can_be_planted_in": True
} for _ in range(5)] for _ in range(2)] + [[{
    "tile_type": "water",
    "current_plant": None,
    "has_zombie": False,
    "can_be_planted_in": True
} for _ in range(5)] for _ in range(2)] + [[{
    "tile_type": "grass",
    "current_plant": None,
    "has_zombie": False,
    "can_be_planted_in": True
} for _ in range(5)] for _ in range(2)]

PLANTS_DATA = {
    "peashooter": {
        "cost": 100
    }
}


current_board = None
current_plant_slots = None

total_current_sun = 0

level_finished = False

def main():

    global total_current_sun
    global current_board
    global current_plant_slots
    global level_finished

    # Starts game
    print_log("Starting game", "info")
    os.startfile(GAME_FULL_PATH)

    # Waits for start button to appear and be clickable
    print_log("Awaiting start button", "info")
    start_button = pg.locateOnScreen(os.path.join("imgs", "startButton.png"), confidence=0.9)
    while not start_button:
        start_button = pg.locateOnScreen(os.path.join("imgs", "startButton.png"), confidence=0.9)
    pg.click(pg.center(start_button))

    # Waits for user input to appear
    print_log("Awaiting new user input", "info")
    new_user_input = pg.locateOnScreen(os.path.join("imgs", "newUserInput.png"), confidence=0.9)
    while not new_user_input:
        new_user_input = pg.locateOnScreen(os.path.join("imgs", "newUserInput.png"), confidence=0.9)

    # Creates new user
    print_log("Creating new user", "info")
    pg.typewrite("BOTanical")
    pg.press("ENTER")

    # Waits for menu to completely load
    print_log("Loading menu", "info")
    menu_loaded_element = pg.locateOnScreen(os.path.join("imgs", "menuLoaded.png"), confidence=0.9)
    while not menu_loaded_element:
        menu_loaded_element = pg.locateOnScreen(os.path.join("imgs", "menuLoaded.png"), confidence=0.9)
    
    print_log("Starting adventure mode", "info")
    adventure_button = pg.locateOnScreen(os.path.join("imgs", "startAdventure.png"), confidence=0.9)
    pg.click(pg.center(adventure_button))

    print_log("Setting mental board", "info")
    total_current_sun = 150
    current_board = copy.deepcopy(CLEAN_FRONTYARD_BOARD)
    # Makes lanes 0, 1, 3 and 4 unavailable to plant
    for lane in (0, 1, 3, 4):
        for tile in current_board[lane]:
            tile["can_be_planted_in"] = False
    current_plant_slots = ["peashooter"]

    print_log("Waiting intro animation to finish", "info")
    start_level_0 = pg.locateOnScreen(os.path.join("imgs", "levels", "0-0", "startLevel.png"), confidence=0.99)
    while not start_level_0:
        start_level_0 = pg.locateOnScreen(os.path.join("imgs", "levels", "0-0", "startLevel.png"), confidence=0.99)
    
    print_log("Level 0-0", "info")
    level_loop = threading.Thread(target=loop_strategy, args={"0-0": "level"})
    level_loop.start()
    clear_level_0 = pg.locateOnScreen(os.path.join("imgs", "levels", "0-0", "clearLevel.png"), confidence=0.9)
    while not clear_level_0:
        clear_level_0 = pg.locateOnScreen(os.path.join("imgs", "levels", "0-0", "clearLevel.png"), confidence=0.9)
    level_finished = True
    print_log("Level 0-0 finished", "info")
    pg.click(pg.center(clear_level_0))

def loop_strategy(level):

    print_log(f"Looping strategy of level {level}", "info")
    if level == "0-0":

        print_log(f"Filling middle lane with peashooters", "info")
        while len([column for column in current_board[2] if column["current_plant"] == None]) > 1 and not level_finished:
            if total_current_sun < PLANTS_DATA["peashooter"]["cost"]:
                print_log(f"Not enough sun to plant a peashooter", "info")
                collect_sun()
            else:
                current_column = 0
                while current_column < len(current_board[2]) and current_board[2][current_column]["current_plant"] == "peashooter": current_column += 1
                if current_column < len(current_board[2]): place_plant_on_board((2, current_column), 'peashooter')

def place_plant_on_board(tile, plant):

    global total_current_sun
    if total_current_sun >= PLANTS_DATA[plant]["cost"]:
        row, column = tile
        print_log(f"Planting {plant} on tile ({row}, {column})", "info")
        pg.click(SLOTS_POSITIONS[current_plant_slots.index(plant)])
        pg.click(TILE_POSITIONS_FRONTYARD[row][column])
        current_board[row][column]["current_plant"] = plant
        total_current_sun -= PLANTS_DATA[plant]["cost"]
    else:
        print_log(f"Not enough sun to plant a {plant}", "info")

def collect_sun():
    """Waits for the next sun to fall on the screen, collects it and adds to the ammount of sun the player currently has"""
    global total_current_sun
    print_log("Collecting sun", "info")
    sun_drop = pg.locateOnScreen(os.path.join("imgs", "sundrop.png"), confidence=0.9)
    while not sun_drop and not level_finished:
        sun_drop = pg.locateOnScreen(os.path.join("imgs", "sunDrop.png"), confidence=0.9)
    if not level_finished:
        pg.click(pg.center(sun_drop))
        time.sleep(1)
        total_current_sun += 25
        print_log(f"Sun collected! Current ammount: {total_current_sun}", "info")

def print_log(msg, msg_type):

    if DEBUG_MODE:
        logger.log(LOG_LEVEL_MAP[msg_type], msg)

if __name__ == "__main__":
    main()