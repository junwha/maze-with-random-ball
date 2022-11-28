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

def getTrackballRotation(sx, sy, dx, dy, w, h):
    if sx == dx and sy == dy:
        return np.eye(4)
    sx = sx - w//2
    dx = dx - w//2
    sy = sy - h//2
    sy = -sy
    dy = dy - h//2
    dy = -dy
    r = min(w, h)/4
    p = sx**2 + sy**2
    if p > r**2 / 2:
        sz = (r**2 / 2) / np.sqrt(p)
    else:
        sz = np.sqrt(r**2 - sx**2 - sy**2)
    p = dx**2 + dy**2
    if p > r**2 / 2:
        dz = (r**2 / 2) / np.sqrt(p)
    else:
        dz = np.sqrt(r**2 - dx**2 - dy**2)
    s = np.array([sx, sy, sz])
    d = np.array([dx, dy, dz])
    k = np.cross(s, d)
    sint = np.linalg.norm(k) / (np.linalg.norm(s) * np.linalg.norm(d))
    cost = np.sqrt(1 - sint ** 2)
    k /= np.linalg.norm(k)
    kx, ky, kz = k
    R = np.array([
        [0, -kz, ky, 0],
        [kz, 0, -kx, 0],
        [-ky, kx, 0, 0],
        [0, 0, 0, 1]
    ])
    R = np.eye(4) + sint * R + (1 - cost) *  R@R
    R[3][3] = 1
    return R

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
    glPushMatrix()
    glTranslatef(*pos)
    glBegin(GL_QUADS)
    c = 0
    for surface in surfaces:
        glColor3f(*colors[c])
        for i in surface:
            glVertex3f(*vertices[i])	
        c += 1				
    glEnd()
    glPopMatrix()

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
        self.fov = 0
        self.zoom = 1
        self.trans = np.array([.0, .0, .0, .0])
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
        
        glPushMatrix()
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-self.w/self.h, self.w/self.h, -1, 1, 0.0001, 10000)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        ax = np.array([-0.75, -0.75, -0.2, 0]) @ self.cameraMatrix
        pos = np.array([0, 0, 1, 0]) @ self.cameraMatrix
        at = np.array([0, 0, 0, 0])
        up = (np.array([0, 1, 0, 0])) @ self.cameraMatrix
        # gluLookAt(*pos[:3], *at[:3], *up[:3])
        glMultMatrixf(self.cameraMatrix.transpose())
        glTranslatef(*ax[:3])
        self.draw_axis()
        glPopMatrix()


        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        # projection matrix
        # use glOrtho and glFrustum (or gluPerspective) here
        glScalef(self.zoom, self.zoom, 1)
        if self.fov == 0:
            glOrtho(-self.w/self.h, self.w/self.h, -1, 1, 0.0001, 10000)
        else:
            gluPerspective(self.fov, self.w/self.h, 0.0001, 10000)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        # self.draw_axis()
        # do some transformations using camera view
        pos = np.array([0, 0, d, 0]) @ self.cameraMatrix + self.trans 
        at = np.array([0, 0, 0, 0]) + self.trans
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
        # glColor3f(1, 1, 1)
        # glutSolidTeapot(0.5)

        glutSwapBuffers()

    def keyboard(self, key, x, y):
        if key == b'=':
            if self.zoom < 1:
                self.zoom += 0.1
            else:
                self.zoom += 1
            self.zoom = min(self.zoom, 5)
            self.zoom = max(self.zoom, 0.1)
        if key == b'-':
            if self.zoom < 1:
                self.zoom -= 0.1
            else:
                self.zoom -= 1
            self.zoom = min(self.zoom, 5)
            self.zoom = max(self.zoom, 0.1)
        if key == b'd':
            self.trans = np.array([.0, .0, .0, .0])
            self.cameraMatrix = np.eye(4)
            self.zoom = 1
        if key == b'0':
            self.fov = 0
        if key == b'\x1b':
            exit()
        # glutPostRedisplay()

    def special(self, key, x, y):
        if key == 101:
            self.fov += 5
            self.fov = min(self.fov, 90)
        if key == 103:
            self.fov -= 5
            self.fov = max(self.fov, 0)
        # glutPostRedisplay()

    def mouse(self, button, state, x, y):
        if button == GLUT_LEFT_BUTTON:
            if state == 0:
                self.mode = 1
                self.rx = x
                self.ry = y
            if state == 1:
                self.mode = 0
        if button == GLUT_RIGHT_BUTTON:
            if state == 0:
                self.mode = 2
                self.rx = x
                self.ry = y
            if state == 1:
                self.mode = 0

        # glutPostRedisplay()

    def motion(self, x, y):
        if self.mode == 1:
            self.cameraMatrix = getTrackballRotation(self.rx, self.ry, x, y, self.w, self.h) @ self.cameraMatrix
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
        # glutPostRedisplay()

    def reshape(self, w, h):
        print(f"window size: {w} x {h}")
        t = min(w, h)
        # glViewport((w-t)//2, (h-t)//2, t, t)
        glViewport(0, 0, w, h)
        self.w = w
        self.h = h
        # glutPostRedisplay()

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
