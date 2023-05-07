# Generals game

This is a simple text-input game for 2 people.
A machine player is added doing fairly optimal moves

# Game rules

2 generals simultaneously pick a number of soldiers to move onto the field.
Whoever moves the most forces onto the field wins the round.
A soldier used in one round can not be used again.
Game is over after one side wins N rounds, or all soldiers are used

## Installation

```bash
$ virtualenv --system-site-packages env
$ source env/bin/activate
$ pip install -r requirements.txt
```

## Usage

```bash
$ python play_game.py -h
```
the above command will print all options.
