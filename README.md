# 💎 Etimo Diamonds 2

Diamonds is a programming challenge. Program a bot and compete to get the highest score. For more information:

- [Project Specification](https://docs.google.com/document/d/13cbmMVXviyu8eKQ6heqgDzt4JNNMeAZO/edit)
- [Get Started with Diamonds](https://docs.google.com/document/d/1L92Axb89yIkom0b24D350Z1QAr8rujvHof7-kXRAp7c/edit)

## A. Used Algorithm

### Greedy by Distance

#### How it Works?

Just by calculate the manhattan distances, then choose the closest Diamonds based on how many step it is\
The Formula Used to Calculate Manhattan Distances is just
    ```
abs(a.x - b.x) + abs(a.y - b.y)
    ```
 which is so simple.

We also have some fallback action if something bad happen, it is Random move
it would move randomly if our bot got stuck in the same place for more than 3 times (we set the default are 3, it can be changed tho)

it only will return to the base, if it points reach greater or equal point that we'll declare in configuration which is at
    ```
src/game/logic/NazarickSublogic/nazarick_config.py
    ```

#### Reason To Use

- the most simplest greedy aproaches
- because we work the talk, just few hours before its deadline
- im afraid that i hit some heuristic aproaches instead of greedy, because border between those two just close

## B. Requirements

1. Clone this repository and move to the root of this project's source directory

    ```
    git clone https://github.com/sinavarasina/Tubes1_MakamNazarick.git && cd Tubes1_MakamNazarick/src/
    ```

2. Install dependencies

    ```
    pip install -r requirements.txt

3. Just make sure you have the game engine running

## C. How To Run

1. To run one bot

    ```
    python main.py --logic Nazarick --email=your_email@example.com --name=your_name --password=your_password --team etimo
    ```

2. To run multiple bots simultaneously

    For Windows

    ```
    ./run-bots.bat
    ```

    For Linux / (possibly) macOS

    ```
    ./run-bots.sh
    ```

    <b>Before executing the script, make sure to change the permission of the shell script to enable executing the script (for linux/macOS)</b>

    ```
    chmod +x run-bots.sh
    ```

#### Note

- If you run multiple bots, make sure each emails and names are unique
- The email could be anything as long as it follows a correct email syntax
- The name, and password could be anything without any space

## D. Author Identity

### The Bot Templates & Game Engine maker (the goat)

- ETIMO

### Bot Logic & Tubes Maker

1. Roberto Charlos Sagala      - 123140113
2. Brahmantio Abimayu          - 123140122
3. Zacky Ghozi Al miqdad       - 123140130

## Credits 🪙

This repository is adapted from <https://github.com/Etimo/diamonds2>

Some code in this repository is adjusted to fix some issues in the original repository and to adapt to the requirements of Algorithm Strategies course (IF2211), Informatics Undergraduate Program, ITB.

©️ All rights and credits reserved to [Etimo](https://github.com/Etimo)
