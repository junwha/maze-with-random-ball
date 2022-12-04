
import random

VALUE_UNDEF = 0
VALUE_WALL = 1
VALUE_PATH = 2

EAST = 0
WEST = 1
SOUTH = 2
NORTH = 3

def setWall(greed, map_size):
    for i in range(map_size):
        greed[0][i] = VALUE_WALL 
        greed[map_size-1][i] = VALUE_WALL 
        greed[i][0] = VALUE_WALL 
        greed[i][map_size-1] = VALUE_WALL 
    
    for row in range(0, map_size, 2):
        for col in range(0, map_size, 2):
            greed[row][col] = VALUE_WALL
     

def makePath(greed, myX, myY, pathDirection, map_size):
    directions = [-1]*3

    #  Find new direction for each direction (except path direction it was from)
    for k in range(3):
        n = -1
        while(n == -1):
            n = random.randrange(0, 4)
            for j in range(3):
                if n==directions[j] or n==pathDirection:
                    n = -1
        directions[k] = n

    for i in range(3):
        checkX = myX
        checkY = myY
        wallX = myX
        wallY = myY

        if directions[i] == EAST:
            checkX = myX + 2
            wallX = myX + 1
            nextDir = WEST
        elif directions[i] == WEST:
            checkX = myX - 2
            wallX = myX - 1
            nextDir = EAST
        elif directions[i] == SOUTH:
            checkY = myY - 2
            wallY = myY - 1
            nextDir = NORTH
        elif directions[i] == NORTH:
            checkY = myY + 2
            wallY = myY + 1
            nextDir = SOUTH

        if 0 < checkX and checkX < map_size and 0 < checkY and checkY < map_size: 
            if greed[checkX][checkY]==VALUE_UNDEF: #  if next direction was undefined, construct new path
                greed[checkX][checkY] = VALUE_PATH
                makePath(greed, checkX, checkY, nextDir, map_size)
            else: #  if next direction was pre-defined, construct wall there 
                greed[wallX][wallY] = VALUE_WALL

def getMaze(map_size):
    #  Initialize greed
    greed = []
    for i in range(map_size):
        greed.append([0]*map_size)
      
    #  Construct Wall
    setWall(greed, map_size)

    #  Make Path
    makePath(greed, 1, 1, SOUTH, map_size) #  Start from 1, 1
    greed[2][1] = 0 #  Destroy only one direction from 1, 1
    greed[0][1] = 0 #  Destroy one wall on outer barrier
    greed[map_size-1][map_size-2] = 0
    greed[map_size-2][map_size-2] = 0
    #  Mark path as 0
    for row in range(map_size):
        for col in range(map_size):
            if greed[col][row] == 2:
                 greed[col][row] = 0
   
    return greed

# maze = getMaze(21)

# for i in range(21):
#     for j in range(21):
#         print(maze[i][j], end="")
#     print()