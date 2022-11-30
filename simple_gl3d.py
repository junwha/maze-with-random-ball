from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import numpy as np
import maze 

FPS = 15

MOUSE_MODE_ROTATION = 0
MOUSE_MODE_TRANSLATION = 1

KEY_ZOOM_IN = b"+"
KEY_ZOOM_OUT = b"-"
KEY_FOV_INC = 101
KEY_FOV_DEC = 103
KEY_RESET = b"d"
KEY_RESET_PROJECTION = b"0"
KEY_EXIT = b"\x1b"

SCALE_MIN = 0.1
SCALE_MAX = 5

FOV_MIN = 0
FOV_MAX = 90

Z_NEAR = 0.01
Z_FAR = 100000
ROTATION_FACTOR = 100 # Track ball speed
MAP_SIZE =21

MOVE_FRONT = b'w'
MOVE_BACK = b's'
MOVE_RIGHT = b'a'
MOVE_LEFT = b'd'

VELOCITY = 0.1

BOTTOM_LEFT_FRONT = 0
BOTTOM_LEFT_BACK = 1
BOTTOM_RIGHT_BACK = 2
BOTTOM_RIGHT_FRONT = 3
TOP_LEFT_FRONT = 4
TOP_LEFT_BACK = 5
TOP_RIGHT_BACK = 6
TOP_RIGHT_FRONT = 7

def abs(x):
    if x < 0:
        return -x
    return x

def getCameraView(px, py, pz, ax, ay, az, ux, uy, uz, trans):
    p = np.array([px, py, pz])
    at = np.array([ax, ay, az])
    up = np.array([ux, uy, uz])
    z = p - at
    z = z / np.linalg.norm(z)
    x = np.cross(up, z)
    x = x / np.linalg.norm(x)
    y = np.cross(z, x)
    R = np.array([[x[0], y[0], z[0], 0],
                  [x[1], y[1], z[1], 0],
                  [x[2], y[2], z[2], 0],
                  [-np.dot(p, x), -np.dot(p, y), -np.dot(p, z), 1]
    ])
    return R

def getCameraVectors(px, py, pz, ax, ay, az, ux, uy, uz):
    p = np.array([px, py, pz])
    at = np.array([ax, ay, az])
    up = np.array([ux, uy, uz])
    z = p - at
    z = z / np.linalg.norm(z)
    x = np.cross(up, z)
    x = x / np.linalg.norm(x)
    y = np.cross(z, x)
    return (x, y, z)

def rotationy(deg):
    deg *= np.pi / 180
    c = np.cos(deg)
    s = np.sin(deg)
    return np.array([[c, 0, -s, 0],
                    [0, 1, 0, 0],
                    [s, 0, c, 0],
                    [0, 0, 0, 1]], dtype=np.float32)

def rotationx(deg):
    deg *= np.pi / 180
    c = np.cos(deg)
    s = np.sin(deg)
    return np.array([[1, 0, 0, 0],
                    [0, c, -s, 0],
                    [0, s, c, 0],
                    [0, 0, 0, 1]], dtype=np.float32)

def f(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])

def drawCube(size=[0.1, 0.1, 0.1], pos=(0, 0, 0)):
    x, y, z = size
    vertices = (
        (x/2, y/2, -z/2), (x/2, -y/2, -z/2), (-x/2, -y/2, -z/2), (-x/2, y/2, -z/2), 
        (x/2, y/2, z/2), (x/2, -y/2, z/2), (-x/2, -y/2, z/2), (-x/2, y/2, z/2),
    )
    surfaces = (
        (BOTTOM_LEFT_FRONT, BOTTOM_LEFT_BACK, BOTTOM_RIGHT_BACK, BOTTOM_RIGHT_FRONT),
        (BOTTOM_LEFT_FRONT, BOTTOM_LEFT_BACK, TOP_LEFT_BACK, TOP_LEFT_FRONT),
        (BOTTOM_LEFT_FRONT, BOTTOM_RIGHT_FRONT, TOP_RIGHT_FRONT, TOP_LEFT_FRONT),
        (TOP_LEFT_FRONT, TOP_LEFT_BACK, TOP_RIGHT_BACK, TOP_RIGHT_FRONT),
        (BOTTOM_LEFT_BACK, BOTTOM_RIGHT_BACK, TOP_RIGHT_BACK, TOP_LEFT_BACK),
        (BOTTOM_RIGHT_BACK, BOTTOM_RIGHT_FRONT, TOP_RIGHT_FRONT, TOP_RIGHT_BACK)
    )
    colors = (
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
        (1, 1, 0),
        (0, 1, 1),
        (1, 0, 1),
    )
    glBegin(GL_QUADS)
    c = 0
    for surface in surfaces:
        glColor3f(*colors[c])
        for i in surface:
            glVertex3f(*f(vertices[i], pos))	
        c += 1				
    glEnd()

class Viewer:
    def __init__(self):
        self.cameraMatrix = np.array([
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
        self.trans = np.array([-0.1, 0.4, 0.1, .0])
        self.w = 800
        self.h = 800
        self.maze = maze.getMaze(MAP_SIZE)
    def light(self):
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST)

        # feel free to adjust light colors
        lightAmbient = [0.5, 0.5, 0.5, 1.0]
        lightDiffuse = [0.5, 0.5, 0.5, 1.0]
        lightSpecular = [0.5, 0.5, 0.5, 1.0]
        lightPosition = [1, 1, -1, 0]    # vector: point at infinity
        glLightfv(GL_LIGHT0, GL_AMBIENT, lightAmbient)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, lightDiffuse)
        glLightfv(GL_LIGHT0, GL_SPECULAR, lightSpecular)
        glLightfv(GL_LIGHT0, GL_POSITION, lightPosition)
        glEnable(GL_LIGHT0)

    def draw_axis(self):
        lw = 2
        glLineWidth(lw)
        glColor3f(1, 0, 0)
        
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(0.2, 0, 0)
        glEnd()

        glColor3f(0, 1, 0)
        glRotatef(90, 0, 0, 1)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(0.2, 0, 0)
        glEnd()

        glColor3f(0, 0, 1)
        glRotatef(-90, 0, 1, 0)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(0.2, 0, 0)
        glEnd()


    def display(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(0, 0, 0, 1)
        d = 1
        if self.fov > 0:
            d = 1/np.tan(np.radians(self.fov / 2))

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        glScalef(self.zoom, self.zoom, 1)
        if self.fov == 0:
            glOrtho(-self.w/self.h, self.w/self.h, -1, 1, 0.0001, 10000)
        else:
            gluPerspective(self.fov, self.w/self.h, 0.0001, 10000)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        self.cameraMatrix = rotationx(self.degx) @ rotationy(self.degy)
        pos = np.array([0, 0, 0, 0]) @ self.cameraMatrix + self.trans 
        at = np.array([0, 0, -d, 0]) @ self.cameraMatrix + self.trans
        up = (np.array([0, 1, 0, 0])) @ self.cameraMatrix
        M = getCameraView(*(pos[:3]),
            *(at[:3]),
            *(up[:3]),
            self.trans)
        glMultMatrixf(M)

        for i in range(MAP_SIZE):
            for j in range(MAP_SIZE):
                if self.maze[i][j] == 1:
                    drawCube(size=(0.1, 0.5, 0.1), pos=(0.1*i, 0.25, 0.1*j))
                else:
                    drawCube(size=(0.1, 0.2, 0.1), pos=(0.1*i, 0.1, 0.1*j))

        glutSwapBuffers()

    def keyboard(self, key, x, y):
        d = 1
        if self.fov > 0:
            d = 1/np.tan(np.radians(self.fov / 2))
        pos = np.array([0, 0, 0, 0]) @ self.cameraMatrix + self.trans 
        at = np.array([0, 0, -d, 0]) @ self.cameraMatrix + self.trans
        up = (np.array([0, 1, 0, 0])) @ self.cameraMatrix
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
            print(self.degx, self.degy)
            self.rx = x
            self.ry = y
        if self.mode == 2:
            pos = np.array([0, 0, 1, 0]) @ self.cameraMatrix + self.trans
            at = np.array([0, 0, 0, 0]) + self.trans
            up = np.array([0, 1, 0, 0]) @ self.cameraMatrix
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

        self.light()

        glutMainLoop()


if __name__ == "__main__":
    viewer = Viewer()
    viewer.run()
