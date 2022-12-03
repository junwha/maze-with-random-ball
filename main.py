from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GL.shaders import *
import numpy as np
import maze 
from settings import *
from utils import *
from engine import *

class Viewer:
    def __init__(self):
        self.cameraMatrix = gen_np_f32_array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        self.mode = 0 # 0: default, 1: rotation, 2: translation
        self.rx = 0
        self.ry = 0
        self.fov = 60
        self.zoom = 1
        self.degx = 0.0
        self.degy = -90.0
        self.trans = gen_np_f32_array([-10*UNIT_LENGTH, UNIT_LENGTH*10, UNIT_LENGTH, .0])
        self.w = 800
        self.h = 800
        self.maze = maze.getMaze(MAP_SIZE)
        self.detectors = [[None]*MAP_SIZE]*MAP_SIZE
        
        self.sampleBalls = [
            Ball(pos=gen_np_f32_array([-1*UNIT_LENGTH, 1.5*UNIT_LENGTH, -1*UNIT_LENGTH]), v=gen_np_f32_array([0, 0.5, 0.5])),
            Ball(pos=gen_np_f32_array([-1*UNIT_LENGTH, 1*UNIT_LENGTH, 1*UNIT_LENGTH]), v=gen_np_f32_array([0, 0, 0.5])),
            Ball(pos=gen_np_f32_array([-1*UNIT_LENGTH, 0, 0]), v=gen_np_f32_array([0, -1, 0]))
        ]
        
        self.collisionDetector = CollisionDetector(gen_np_f32_array([[-3*UNIT_LENGTH, UNIT_LENGTH], [-3*UNIT_LENGTH, 3*UNIT_LENGTH], [-3*UNIT_LENGTH, 3*UNIT_LENGTH]]))
        for ball in self.sampleBalls:
            self.collisionDetector.addBall(ball)
        
        self.balls = []
        
        for i in range(MAP_SIZE):
            for j in range(MAP_SIZE):                
                if self.maze[i][j] == ROAD:
                    self.balls.append(Ball(radius=0.1*UNIT_LENGTH, pos=gen_np_f32_array([i*UNIT_LENGTH, ROAD_HEIGHT*UNIT_LENGTH + UNIT_LENGTH, j*UNIT_LENGTH]), v=np.random.rand(3), c=np.random.rand(3)))             
                    
        
    def light(self, pos=[0, 50, 100.0, 1]):
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST)

        # feel free to adjust light colors
        lightAmbient = [0.0, 0.0, 0.0, 1.0]
        lightDiffuse = [1.0, 1.0, 1.0, 1.0]
        lightSpecular = [0, 1, 0, 1.0]
        
        glLightfv(GL_LIGHT0, GL_AMBIENT, lightAmbient)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, lightDiffuse)
        glLightfv(GL_LIGHT0, GL_SPECULAR, lightSpecular)
        glLightfv(GL_LIGHT0, GL_LINEAR_ATTENUATION, 0.1)
        glLightfv(GL_LIGHT0, GL_POSITION, pos)
        glEnable(GL_LIGHT0)

    def constructCLines(self, i, j, unit):
        cLines = gen_np_f32_array([[-np.inf, np.inf]]*3)
    
        if i-1 < 0 or (i-1 >= 0 and self.maze[i-1][j] == WALL):
            cLines[0][0] = unit*(i-1)+0.5*unit

        if i+1 >= MAP_SIZE or (i+1 < MAP_SIZE and self.maze[i+1][j] == WALL):
            cLines[0][1] = unit*(i+1)-0.5*unit
            
        if j-1 < 0 or (j-1 >= 0 and self.maze[i][j-1] == WALL):
            cLines[2][0] = unit*(j-1)+0.5*unit
            
        if j+1 >= MAP_SIZE or (j+1 < MAP_SIZE and self.maze[i][j+1] == WALL):
            cLines[2][1] = unit*(j+1)-0.5*unit
        
        # cLines[0][0] = unit*(i-1)+0.5*unit
        # cLines[0][1] = unit*(i+1)-0.5*unit
        # cLines[2][0] = unit*(j-1)+0.5*unit
        # cLines[2][1] = unit*(j+1)-0.5*unit
        
        cLines[1][0] = UNIT_LENGTH*ROAD_HEIGHT
        cLines[1][1] = UNIT_LENGTH*WALL_HEIGHT*2
        return cLines
    
    def display(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(0, 0, 0, 1)
        d = 1
        if self.fov > 0:
            d = 1/np.tan(np.radians(self.fov / 2))

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        glScalef(self.zoom, self.zoom, 1)
   
        gluPerspective(self.fov, self.w/self.h, 0.0001, 10000)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        self.cameraMatrix = rotationx(self.degx) @ rotationy(self.degy)
        pos = gen_np_f32_array([0, 0, 0, 0]) @ self.cameraMatrix + self.trans 
        at = gen_np_f32_array([0, 0, -d, 0]) @ self.cameraMatrix + self.trans
        up = (gen_np_f32_array([0, 1, 0, 0])) @ self.cameraMatrix
        self.light(pos=(0, 0, 0, 1.0)) # (pos[0], pos[1], pos[2]
        gluLookAt(*(pos[:3]), *(at[:3]), *(up[:3]))

        glColor3f(1, 1, 1)
        # drawCube(size=(0.1, 0.1, 0.1),axi pos=(0.1, 0.1, 0.1))
        # glColor3f(0, 0, 1)
        # drawCube(size=(0.1, 0.1, 0.1), pos=(0.3, 0.1, 0.1))
        
        self.sampleBalls[0].update()
        self.sampleBalls[1].update()
        self.sampleBalls[2].update()
        
        for i in range(MAP_SIZE):
            for j in range(MAP_SIZE):                
                if self.maze[i][j] == WALL: # Wall
                    drawCube(size=(UNIT_LENGTH, UNIT_LENGTH*WALL_HEIGHT, UNIT_LENGTH), pos=(UNIT_LENGTH*i, UNIT_LENGTH*WALL_HEIGHT/2, UNIT_LENGTH*j))
                else: # Road
                    drawCube(size=(UNIT_LENGTH, UNIT_LENGTH*ROAD_HEIGHT, UNIT_LENGTH), pos=(UNIT_LENGTH*i, UNIT_LENGTH*ROAD_HEIGHT/2, UNIT_LENGTH*j))
                    self.detectors[i][j] = CollisionDetector(self.constructCLines(i, j, UNIT_LENGTH))
        
        for ball in self.balls:
            ball.update()
            try:
                i, j = round(ball.pos[0]/UNIT_LENGTH), round(ball.pos[2]/UNIT_LENGTH) # int((ball.pos[0]+0.5*UNIT_LENGTH)//UNIT_LENGTH), int((ball.pos[2]+0.5*UNIT_LENGTH)//UNIT_LENGTH)
            except:
                # print(ball.pos)
                pass
                
            if i < 0 or j < 0 or i >= MAP_SIZE or j >= MAP_SIZE or self.detectors[i][j] == None:
                # print(ball.pos)
                # print(i, j)
                pass
            else:
                self.detectors[i][j].addBall(ball)
        
        for i in range(MAP_SIZE):
            for j in range(MAP_SIZE):  
                if self.maze[i][j] == ROAD:
                    self.detectors[i][j].testAll()
                
        for ball in self.balls:
            ball.draw()    
        
        self.collisionDetector.testAll()
        
       
        
        self.sampleBalls[0].draw()
        self.sampleBalls[1].draw()
        self.sampleBalls[2].draw()
        
        glutSwapBuffers()

    def keyboard(self, key, x, y):
        d = 1
        if self.fov > 0:
            d = 1/np.tan(np.radians(self.fov / 2))
        pos = gen_np_f32_array([0, 0, 0, 0]) @ self.cameraMatrix + self.trans 
        at = gen_np_f32_array([0, 0, -d, 0]) @ self.cameraMatrix + self.trans
        up = (gen_np_f32_array([0, 1, 0, 0])) @ self.cameraMatrix
        left, _, front = getCameraVectors(*(pos[:3]), *(at[:3]), *(up[:3]))
        left[1] = 0
        if np.linalg.norm(left) != 0:
            left = left / np.linalg.norm(left)
        left = np.append(left, [0])
        front[1] = 0
        if np.linalg.norm(front) != 0:
            front = front / np.linalg.norm(front)
        front = np.append(front, [0])
        if key == MOVE_FRONT:
            self.trans -= front * VELOCITY
        if key == MOVE_BACK:
            self.trans += front * VELOCITY
        if key == MOVE_RIGHT:
            self.trans -= left * VELOCITY
        if key == MOVE_LEFT:
            self.trans += left * VELOCITY
        if key == b'\x1b':
            exit()

    def special(self, key, x, y):
        if key == 101:
            self.fov += 5
            self.fov = min(self.fov, 90)
        if key == 103:
            self.fov -= 5
            self.fov = max(self.fov, 0)

    def mouse(self, button, state, x, y):
        if button == GLUT_LEFT_BUTTON:
            if state == 0:
                self.mode = 1
                self.rx = x
                self.ry = y
            if state == 1:
                self.mode = 0

    def motion(self, x, y):
        if self.mode == 1:
            d = 1
            if x > self.rx:
                self.degy -= d
            if x < self.rx:
                self.degy += d
            if y > self.ry:
                self.degx += d
            if y < self.ry:
                self.degx -= d
            self.degx = max(self.degx, -90)
            self.degx = min(self.degx, 90)
            self.rx = x
            self.ry = y
        if self.mode == 2:
            pos = gen_np_f32_array([0, 0, 1, 0]) @ self.cameraMatrix + self.trans
            at = gen_np_f32_array([0, 0, 0, 0]) + self.trans
            up = gen_np_f32_array([0, 1, 0, 0]) @ self.cameraMatrix
            vx, vy, _ = getCameraVectors(*(pos[:3]), *(at[:3]), *(up[:3]))
            self.trans -= (x - self.rx) * np.append(vx, [0]) * 0.002
            self.trans += (y - self.ry) * np.append(vy, [0]) * 0.002
            self.rx = x
            self.ry = y

    def reshape(self, w, h):
        print(f"window size: {w} x {h}")
        t = min(w, h)
        glViewport(0, 0, w, h)
        self.w = w
        self.h = h

    def timer(self, value):
        glutPostRedisplay()
        glutTimerFunc(1000//FPS, self.timer, FPS)

    def run(self):
        glutInit()
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
        glutInitWindowSize(800, 800)
        glutInitWindowPosition(0, 0)
        glutCreateWindow(b"CS471 Computer Graphics #2")

        self.timer(FPS)
        glutDisplayFunc(self.display)
        glutKeyboardFunc(self.keyboard)
        glutSpecialFunc(self.special)
        glutMouseFunc(self.mouse)
        glutMotionFunc(self.motion)
        glutReshapeFunc(self.reshape)

        # self.light()

        glutMainLoop()


if __name__ == "__main__":
    viewer = Viewer()
    viewer.run()
