# 天狐修炼纪 (Tianhu Cultivation Chronicle)

This is a turn-based RPG game built using Python and Tkinter. The game currently includes the following core features:

- Graph-based map navigation system
- Complete RPG combat system
- Plot system with branching narratives
- Separation of front-end and back-end logic
- Expandable DLC module with completed DLC traits

## Current Status
- **Game Logic**: Core functionality implemented and tested.
- **Plot**: Still under development, not yet complete.
- **Future Migration**: Planning to transition to a Web + SQL architecture.

## Project Structure
Below is the structure of the core modules. Files not listed are either under testing or deprecated.
'''
tenkitsune/
├── README.md
├── requirements.txt
├── synthesis_recipe.txt            # Defines crafting recipes for in-game items
├── api.py                          # API module (under development)
├── game_engine.py                  # Game engine (under development)
├── run.py                          # Entry point to start the game
├── main.py                         # Main program logic
├── all/
│   ├── init.py
│   ├── dlcmanager.py               # Manages DLC content
│   ├── gamestate.py                # Tracks game state
│   ├── load.py                     # Handles loading of game data
│   ├── synthesis_recipes.py        # Manages crafting system
│   └── transfer.py                 # Data transfer utilities
├── chapter/                        # Story data and plot content
├── common/                         # Core modules and UI implementations
│   ├── character/
│   │   ├── init.py
│   │   ├── ally.py                 # Ally character logic
│   │   ├── boss.py                 # Boss character logic
│   │   ├── enemy.py                # Enemy character logic
│   │   └── player.py               # Player character logic
│   ├── interact/
│   │   ├── init.py
│   │   ├── dungeon_interact.py     # Dungeon interaction logic
│   │   ├── map_interact.py         # Map interaction logic
│   │   └── npc_interact.py         # NPC interaction logic
│   ├── interface/
│   │   ├── init.py
│   │   ├── bag_interface.py        # Inventory UI
│   │   ├── cultivation_interface.py # Cultivation system UI
│   │   ├── dungeon_interface.py    # Dungeon UI
│   │   ├── lottery_interface.py    # Lottery system UI
│   │   ├── map_interface.py        # Map UI
│   │   ├── market_interface.py     # Market UI
│   │   ├── npc_interface.py        # NPC interaction UI
│   │   ├── synthesis_interface.py  # Crafting system UI
│   │   └── task_interface.py       # Task system UI
│   ├── logic/
│   │   ├── init.py
│   │   ├── boss_logic_common1.py   # Common boss logic (part 1)
│   │   └── boss_logic_common2.py   # Common boss logic (part 2)
│   ├── module/
│   │   ├── init.py
│   │   ├── battle.py               # Battle system logic
│   │   ├── cultivation.py          # Cultivation system logic
│   │   ├── currency.py             # Currency system logic
│   │   ├── dungeon.py              # Dungeon system logic
│   │   ├── item.py                 # Item system logic
│   │   ├── lottery.py              # Lottery system logic
│   │   ├── map.py                  # Map system logic
│   │   ├── market.py               # Market system logic
│   │   ├── musicplayer.py          # Music playback system
│   │   ├── npc.py                  # NPC system logic
│   │   ├── story.py                # Story system logic
│   │   ├── synthesis.py            # Crafting system logic
│   │   └── task.py                 # Task system logic
│   └── ui/
│       ├── init.py
│       ├── bagui.py                # Inventory UI implementation
│       ├── battleui.py             # Battle UI implementation
│       ├── cultivationui.py        # Cultivation UI implementation
│       ├── dungeonui.py            # Dungeon UI implementation
│       ├── lotteryui.py            # Lottery UI implementation
│       ├── mapui.py                # Map UI implementation
│       ├── storyui.py              # Story UI implementation
│       └── synthesisui.py          # Crafting UI implementation
├── data/
│   ├── character/
│   │   ├── ally.json               # Ally character data
│   │   ├── boss.json               # Boss character data
│   │   └── enemy.json              # Enemy character data
│   ├── interact/
│   │   ├── lottery.json            # Lottery system data
│   │   ├── market.json             # Market system data
│   │   ├── npc.json                # NPC data
│   │   └── task.json               # Task system data
│   ├── item/
│   │   ├── equipment.json          # Equipment item data
│   │   ├── material.json           # Crafting material data
│   │   ├── medicine.json           # Medicine item data
│   │   ├── product.json            # Crafted product data
│   │   ├── skill.json              # Skill data
│   │   └── warp.json               # Warp/teleport data
│   ├── save/                       # Game save data
│   └── scenario/
│       ├── dungeon.json            # Dungeon scenario data
│       └── map.json                # Map scenario data
├── dlc/
│   ├── init.py
│   ├── dlc_events/
│   │   ├── init.py
│   │   └── events.py               # DLC event logic
│   └── dlc_traits/                 # DLC trait implementations
├── resources/
│   ├── background/                 # Background assets
│   ├── cartoon/                    # Cartoon-style assets
│   ├── commodity/                  # In-game commodity assets
│   ├── figure/                     # Character figure assets
│   ├── map/                        # Map assets
│   └── music/                      # Music and sound assets
└── tests/
    ├── init.py
    └── game.log                    # Game log for testing
'''

## Future Plans
- Migrate the front-end to **Flask + HTML** for web-based rendering.
- Implement **SQLite** or another database for game data storage.
- Enrich the plot and develop an automated plot management system.

## Environment
- **Pillow**: 11.0.0
- **Pygame**: 2.6.1

## How to Use
1. Ensure all dependencies in `requirements.txt` are installed.
2. Run the game by executing `run.py`.

## Note

This project is still under active development. Suggestions and contributions are welcome! Feel free to open issues or submit pull requests to help improve the game.
