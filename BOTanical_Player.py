# Python libs
import os
import time
import logging
import copy
import threading
import sys

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
        FIRST_TILE_POSITION_FRONTYARD[0] + (BOARD_COLUMNS_SPACING * current_col), 
        FIRST_TILE_POSITION_FRONTYARD[1] + (BOARD_ROWS_SPACING * current_row), 
    ) for current_row in range(5)]
for current_col in range(9)]

HORIZONTAL_SLOTS_SPACING_INGAME = 105
FIRST_SLOT_HORIZONTAL_POSITION_INGAME = 467.5
SLOT_VERTICAL_POSITION_INGAME = 20
SLOTS_POSITIONS = [
    (FIRST_SLOT_HORIZONTAL_POSITION_INGAME + (HORIZONTAL_SLOTS_SPACING_INGAME * current_slot), SLOT_VERTICAL_POSITION_INGAME)
for current_slot in range(10)]


CLEAN_FRONTYARD_BOARD = [[{
    "tile_type": "grass",
    "current_plant": None,
    "has_zombie": False,
    "can_be_planted_in": True
} for _ in range(5)] for _ in range(9)]

CLEAN_POOL_BOARD = [[{
    "tile_type": "grass",
    "current_plant": None,
    "has_zombie": False,
    "can_be_planted_in": True
} for _ in range(2)] for _ in range(9)] + [[{
    "tile_type": "water",
    "current_plant": None,
    "has_zombie": False,
    "can_be_planted_in": True
} for _ in range(2)] for _ in range(9)] + [[{
    "tile_type": "grass",
    "current_plant": None,
    "has_zombie": False,
    "can_be_planted_in": True
} for _ in range(2)] for _ in range(9)]

PLANTS_DATA = {
    "peashooter": {
        "cost": 100,
        "recharge_time": "fast"
    },
    "sunflower": {
        "cost": 50,
        "recharge_time": "fast"
    }
}

RECHARGE_DATA = {
    "fast": {
        "initial_seconds": 0,
        "seconds": 7.5
    },
    "slow": {
        "initial_seconds": 20,
        "seconds": 30
    },
    "very_slow": {
        "initial_seconds": 35,
        "seconds": 50
    }
}

current_board = None
current_plant_slots = None

total_current_sun = 0

level_finished = False

def main():

    try:
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
        for column in current_board:
            for index_row, tile in enumerate(column):
                if index_row != 2: tile["can_be_planted_in"] = False
        current_plant_slots = [{
            "plant": "peashooter",
            "first_time_planting": True,
            "last_time_planted": time.time()
        }]

        print_log("Waiting intro animation to finish", "info")
        start_level_00 = pg.locateOnScreen(os.path.join("imgs", "levels", "0-0", "startLevel.png"), confidence=0.99)
        while not start_level_00:
            start_level_00 = pg.locateOnScreen(os.path.join("imgs", "levels", "0-0", "startLevel.png"), confidence=0.99)
        
        print_log("Level 0-0", "info")
        collect_sun_loop = threading.Thread(target=collect_sun)
        collect_sun_loop.start()
        level_loop = threading.Thread(target=loop_strategy, args={"0-0": "level"})
        level_loop.start()
        clear_level_00 = pg.locateOnScreen(os.path.join("imgs", "levels", "0-0", "clearLevel.png"), confidence=0.9)
        while not clear_level_00:
            clear_level_00 = pg.locateOnScreen(os.path.join("imgs", "levels", "0-0", "clearLevel.png"), confidence=0.9)
        level_finished = True
        time.sleep(2)
        clear_level_00 = pg.locateOnScreen(os.path.join("imgs", "levels", "0-0", "clearLevel.png"), confidence=0.9)
        pg.click(pg.center(clear_level_00))
        print_log("Level 0-0 finished", "info")

        print_log("Setting mental board", "info")
        total_current_sun = 50
        current_board = copy.deepcopy(CLEAN_FRONTYARD_BOARD)
        # Makes lanes 0 and 4 unavailable to plant
        for column in current_board:
            for index_row, tile in enumerate(column):
                if index_row in (0, 4): tile["can_be_planted_in"] = False

        print_log("Starting next level", "info")
        time.sleep(2)
        start_next_level = pg.locateOnScreen(os.path.join("imgs", "levels", "startNextLevel.png"), confidence=0.9)
        while not start_next_level:
            start_next_level = pg.locateOnScreen(os.path.join("imgs", "levels", "startNextLevel.png"), confidence=0.9)
        pg.click(pg.center(start_next_level))
        start_level_01 = pg.locateOnScreen(os.path.join("imgs", "levels", "0-1", "startLevel.png"), confidence=0.99)
        while not start_level_01:
            start_level_01 = pg.locateOnScreen(os.path.join("imgs", "levels", "0-1", "startLevel.png"), confidence=0.99)
        
        # current_plant_slots = [
        # {
        #     "plant": "peashooter",
        #     "last_time_planted": time.time(),
        #     "first_time_planting": True
        # }, 
        # {
        #     "plant": "sunflower",
        #     "last_time_planted": time.time(),
        #     "first_time_planting": True
        # }]

        # print_log("Level 0-1", "info")
        # level_loop = threading.Thread(target=loop_strategy, args={"0-1": "level"})
        # level_loop.start()
        # clear_level_01 = pg.locateOnScreen(os.path.join("imgs", "levels", "0-0", "clearLevel.png"), confidence=0.9)
        # while not clear_level_01:
        #     clear_level_01 = pg.locateOnScreen(os.path.join("imgs", "levels", "0-0", "clearLevel.png"), confidence=0.9)
        #     time.sleep(1)
        # level_finished = True
        # print_log("Level 0-0 finished", "info")
        # pg.click(pg.center(clear_level_01))

    except KeyboardInterrupt:

        level_finished = True

def tile_range_is_not_full(tile_range):

    initial_tile, end_tile = tile_range
    return len([
        column for index_col, column in enumerate(current_board) 
        if index_col >= initial_tile[0] and \
           index_col <= end_tile[0] and \
        len([
            row for index_row, row in enumerate(column) 
            if row["current_plant"] == None and \
               row["can_be_planted_in"] and \
               index_row >= initial_tile[1] and \
               index_row <= end_tile[1]
        ]) > 0
    ]) > 0

def loop_strategy(level):

    print_log(f"Looping strategy of level {level}", "info")
    if level == "0-0":

        print_log(f"Filling middle lane with peashooters", "info")
        while tile_range_is_not_full(((0, 2), (8, 2))) and not level_finished:
            if total_current_sun >= PLANTS_DATA["peashooter"]["cost"]:
                for index_col, column in enumerate(current_board):
                    if column[2]["current_plant"] == None: 
                        try_placing_plant_on_board((index_col, 2), 'peashooter')
                        break
                    

    # elif level == "0-1":

    #     print_log(f"Filling 2 back columns with sunflowers", "info")
    #     print_log(f"Planting first 3 sunflowers", "info")
    #     while tile_range_is_empty() and not level_finished:
    #         if total_current_sun >= PLANTS_DATA["peashooter"]["cost"]:
    #             current_column = 0
    #             while current_column < len(current_board[2]) and current_board[2][current_column]["current_plant"] == "peashooter": current_column += 1
    #             if current_column < len(current_board[2]): try_placing_plant_on_board((2, current_column), 'peashooter')



def try_placing_plant_on_board(tile, plant):

    global total_current_sun
    if total_current_sun >= PLANTS_DATA[plant]["cost"]:
        slot_index = [index for index in range(len(current_plant_slots)) if current_plant_slots[index]["plant"] == plant][0]
        plant_slot = current_plant_slots[slot_index]
        if (plant_slot["first_time_planting"] and time.time() - plant_slot["last_time_planted"] >= RECHARGE_DATA[PLANTS_DATA[plant_slot["plant"]]["recharge_time"]]["initial_seconds"]) or \
           (not plant_slot["first_time_planting"] and time.time() - plant_slot["last_time_planted"] >= RECHARGE_DATA[PLANTS_DATA[plant_slot["plant"]]["recharge_time"]]["seconds"]):
            column, row = tile
            print_log(f"Planting {plant} on tile ({column}, {row})", "info")
            pg.click(SLOTS_POSITIONS[slot_index])
            pg.click(TILE_POSITIONS_FRONTYARD[column][row])
            current_board[column][row]["current_plant"] = plant
            total_current_sun -= PLANTS_DATA[plant]["cost"]
        else:
            print_log(f"Plant {plant} hasn't fully recharged yet", "info")
    else:
        print_log(f"Not enough sun to plant a {plant}", "info")

def collect_sun():
    """Waits for the next sun to fall on the screen, collects it and adds to the ammount of sun the player currently has"""
    global total_current_sun
    while not level_finished:
        sun_drop = pg.locateOnScreen(os.path.join("imgs", "levels", "sundrop.png"), confidence=0.9)
        while not sun_drop and not level_finished:
            sun_drop = pg.locateOnScreen(os.path.join("imgs", "levels", "sundrop.png"), confidence=0.9)
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