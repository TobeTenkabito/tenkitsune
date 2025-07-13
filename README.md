project introduction
This is a turn-based RPG game built on Python tkinter. Currently, basic functions have been implemented, including:
Graph-based map mobile system
Complete RPG combat system
Plot system and its branches
Separation of front-end and back-end logic
Expandable DLC module
DLC traits have been completed

Current Status
The game logic has been completed and the main functions have passed the test
The plot is not yet complete
Planning to migrate to Web + SQL architecture

Project Structure Description
The following are all core modules. Modules that are in the project files but not listed below are still under testing or old code
天狐修炼纪/
├── README.md
├── requirements.txt
├── synthesis_recipe.txt            # create the new product in the game by material
├── api.py                          # Still under development
├── game_engine.py                  # Still under development
├── run.py                          # here for staring
├── main.py                         # here is main programme
├── all/
│   ├── __init__.py
│   ├── dlcmanager.py
│   ├── gamestate.py
│   ├── load.py
│   ├── synthesis_recipes.py
│   └── transfer.py
├── chapter/                        # here is story data
├── common/                         # the each module and ui implementation
│   ├── character/
│   │   ├── __init__.py
│   │   ├── ally.py
│   │   ├── boss.py
│   │   ├── enemy.py
│   │   └── player.py
│   ├── interact/
│   │   ├── __init__.py
│   │   ├── dungeon_interact.py
│   │   ├── map_interact.py
│   │   └── npc_interact.py
│   ├── interface/
│   │   ├── __init__.py
│   │   ├── bag_interface.py
│   │   ├── cultivation_interface.py
│   │   ├── dungeon_interface.py
│   │   ├── lottery_interface.py
│   │   ├── map_interface.py
│   │   ├── market_interface.py
│   │   ├── npc_interface.py
│   │   ├── synthesis_interface.py
│   │   └── task_interface.py
│   ├── logic/
│   │   ├── __init__.py
│   │   ├── boss_logic_common1.py
│   │   └── boss_logic_common2.py
│   ├── module/
│   │   ├── __init__.py
│   │   ├── battle.py
│   │   ├── cultivation.py
│   │   ├── currency.py
│   │   ├── dungeon.py
│   │   ├── item.py
│   │   ├── lottery.py
│   │   ├── map.py
│   │   ├── market.py
│   │   ├── musicplayer.py
│   │   ├── npc.py
│   │   ├── story.py
│   │   ├── synthesis.py
│   │   └── task.py
│   └── ui/
│   │   ├── __init__.py
│   │   ├── bagui.py
│   │   ├── battleui.py
│   │   ├── cultivationui.py
│   │   ├── dungeonui.py
│   │   ├── lotteryui.py
│   │   ├── mapui.py
│   │   ├── storyui.py
│   │   └── synthesisui.py
├── common/
├── data/
│   ├── character/
│   │   ├── ally.json
│   │   ├── boss.json
│   │   └── boss.json
│   ├── interact/
│   │   ├── lottery.json
│   │   ├── market.json
│   │   ├── npc.json
│   │   └── task.json
│   ├── item/
│   │   ├── equipment.json
│   │   ├── material.json
│   │   ├── medicine.json
│   │   ├── product.json
│   │   ├── skill.json
│   │   └── warp.json
│   ├── save/
│   └── scenario/
│   │   ├── dungeon.json
│   │   └── map.json
├── dlc/
│   ├── __init__.py
│   ├── dlc_events.py
│   │   ├── __init__.py
│   │   └── events.py
│   └── dlc_traits/
├── resources/
│   ├── background/
│   ├── cartoon/
│   ├── commodity/
│   ├── figure/
│   ├── map/
│   └── music/
└── tests/
    ├── __init__.py
    └── game.log


Future plans
Use Flask + HTML to implement the front-end page
Use SQLite or other databases for archiving
Enrich the plot and realize automatic plot management

Environment
pillow 11.0.0
pygame 2.6.1

How to use
click the run.py to play the game

Note
This project is still under development, please feel free to make suggestions or participate in improvements!

