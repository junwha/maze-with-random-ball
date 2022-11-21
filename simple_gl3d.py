from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import numpy as np
import maze 

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
MAP_SIZE = 21

BOTTOM_LEFT_FRONT = 0
BOTTOM_LEFT_BACK = 1
BOTTOM_RIGHT_BACK = 2
BOTTOM_RIGHT_FRONT = 3
TOP_LEFT_FRONT = 4
TOP_LEFT_BACK = 5
TOP_RIGHT_BACK = 6
TOP_RIGHT_FRONT = 7

def get_camera_matrix(c, at, up):
    z = c-at 
    z = z/np.linalg.norm(z) # Get unit vector
    x = np.cross(up, z)
    x = x/np.linalg.norm(x) # Get unit vector
    y = np.cross(z, x)
    R = np.column_stack([x, y, z]) # Construct rotation matrix with [x y z]
    upper = np.column_stack([R.T, -R.T@c]) # Horizontal concat
    T = np.vstack([upper, [0, 0, 0, 1]]) # Vertical concat
    return T

# Derive the difference relative to camera using difference on view plane
def get_translation_diff(c, at, up, diff_x, diff_y):
    z = c-at 
    z = z/np.linalg.norm(z) # Get unit vector for z
    x = np.cross(up, z)
    x = x/np.linalg.norm(x) # Get unit vector for x
    y = np.cross(z, x) # Get unit vector for y
    return x*diff_x+y*diff_y # Get difference for x and y component

# Convert point to vector on trackball
def point2vector(p, r): # Convert point to vector
    x, y = p
    d = (x**2+y**2)**0.5 # Distance from origin
    if d > r: # scale down distance to r if d > r
        x *= (r/d) 
        y *= (r/d) 
    z = (r**2-x**2-y**2)**0.5
    return np.array([x, y, z])    

# Draw cube in the position with the size 
# TODO: receive color as parameter
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
        self.up = np.array([0, 1, 0, 0]) # 0-homogeneous coordinate because up vector is a vector
        self.at = np.array([0, 0, 0, 1]) # at position 
        self.cop = np.array([0, 0, 1, 1]) # center of projection (position)
        
        self.window_size = (800, 800) # to track current window ratio
        
        self.fovy = 0
        
        # State variables to track mouse position
        self.mouse_pos = None # Last mouse position (for drag)
        self.mouse_mode = MOUSE_MODE_ROTATION 

        self.rotation = np.eye(4)
        self.translation = np.eye(4)
        self.scale_factor = 1
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

    def display(self):
        glViewport(0, 0, *self.window_size) # Update viewport to new width and height
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(0, 0, 0, 1)
        
        ##################
        ### Projection ###
        ##################
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        
        Z_NEAR = 0.1 # fixed znear to properly include teapot object
        h = np.tan(np.radians(self.fovy/2))*Z_NEAR # Relative height about znear and fovy
        w = self.window_size[0]/self.window_size[1]*h # Relative width about aspect and height
        self.cop = np.array([0, 0, 2*np.tan(np.radians(90-self.fovy/2)), 1]) # COP for perspective projection
        
        if self.fovy == 0: # Orthogonal projection
            self.cop = np.array([0, 0, 1, 1]) # COP for orthogonal projection
            h = 2
            w = h*self.window_size[0]/self.window_size[1] # From initial height, derive relative width
            glOrtho(-w/2, w/2, -h/2, h/2, Z_NEAR, Z_FAR) # zFar to enough large number to include teapot object
        else: # Perspective projection
            glFrustum(-w/2, w/2, -h/2, h/2, Z_NEAR, 1000.0) # zFar to enough large number to include teapot object


        ##################
        ### Model View ###
        ##################
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        glMultMatrixf(get_camera_matrix((self.cop @ self.rotation @ self.translation)[:-1], (self.at @ self.rotation @ self.translation)[:-1], (self.up @ self.rotation)[:-1]).T)
        glScalef(self.scale_factor, self.scale_factor, self.scale_factor) # Zoom in and out

        # Construct maze
        for i in range(MAP_SIZE):
            for j in range(MAP_SIZE):
                if self.maze[i][j] == 1:
                    drawCube(size=(0.1, 0.5, 0.1), pos=(0.1*i, 0.25, 0.1*j))
                else:
                    drawCube(size=(0.1, 0.2, 0.1), pos=(0.1*i, 0.1, 0.1*j))

        #################
        ### Indicator ###
        #################
        glViewport(0, 0, 100, 100) # Generate 10x10 viewport in bottom-left for indicator
        glMatrixMode(GL_PROJECTION) # Projection independently
        glLoadIdentity()

        glOrtho(-1, 1, -1, 1, 0.1, 1000.0) # Orthogonal projection on 2x2 plane
        
        glMatrixMode(GL_MODELVIEW) # Model view independently
        glLoadIdentity()

        # Independent camera position for indicator (apply only rotation)
        indicator_cop = np.array([0, 0, 1, 1]) @ self.rotation 
        indicator_at = np.array([0, 0, 0, 1]) @ self.rotation
        indicator_up = np.array([0, 1, 0, 0]) @ self.rotation

        glMultMatrixf(get_camera_matrix(indicator_cop[:-1], indicator_at[:-1], indicator_up[:-1]).T)

        for i in range(3): # Draw x, y, z axis with RGB
            color = [0, 0, 0]
            line = [0, 0, 0]
            color[i] = 1 
            line[i] = 1
            glColor3f(*color) # Set color
            glBegin(GL_LINES)
            glVertex3f(0, 0, 0) # origin
            glVertex3f(*line) # point on axis
            glEnd()
        
        glColor3f(1, 1, 1) # Reset color to white (for teapot)
        glutSwapBuffers()
        
    def close(self):
        glutDestroyWindow(glutGetWindow())
        exit(0)

    def keyboard(self, key, x, y):
        print(f"keyboard event: key={key}, x={x}, y={y}")
        if glutGetModifiers() & GLUT_ACTIVE_SHIFT:
            print("shift pressed")
        if glutGetModifiers() & GLUT_ACTIVE_ALT:
            print("alt pressed")
        if glutGetModifiers() & GLUT_ACTIVE_CTRL:
            print("ctrl pressed")
        
        if key == KEY_ZOOM_IN:
            if self.scale_factor >= 1 and self.scale_factor < SCALE_MAX: # Zoom in by 1
                self.scale_factor += 1
            elif self.scale_factor < 1: # Zoom in by 0.1
                self.scale_factor += 0.1
            print(self.scale_factor)
        elif key == KEY_ZOOM_OUT:
            if self.scale_factor > 1: # Zoom out by 1
                self.scale_factor -= 1
            elif self.scale_factor <= 1 and self.scale_factor > SCALE_MIN: # Zoom out by 0.1
                self.scale_factor -= 0.1
            print(self.scale_factor)
        elif key == KEY_RESET: # Reset all transformation related fields
            self.translation = np.eye(4)
            self.rotation = np.eye(4)
            self.scale_factor = 1
        elif key == KEY_RESET_PROJECTION: # Reset projection to orthogonal (FoV=0)
            self.fovy = 0
        elif key == KEY_EXIT: # Exit
            self.close()

        glutPostRedisplay()

    def special(self, key, x, y):
        print(f"special key event: key={key}, x={x}, y={y}")

        
        if key == KEY_FOV_DEC and self.fovy > FOV_MIN: # Decrease FoV by 5
            self.fovy -= 5
        elif key == KEY_FOV_INC and self.fovy < FOV_MAX: # Increase FoV by 5
            self.fovy += 5
            
        glutPostRedisplay()

    
    def pixel2viewport(self, x, y):
        w, h = self.window_size
        return ((x-w/2)/(w/2), -(y-h/2)/(h/2))

    def mouse(self, button, state, x, y):
        print(f"mouse press event: button={button}, state={state}, x={x}, y={y}")
        
        if button == 2: # Set translation mode for right click 
            self.mouse_mode = MOUSE_MODE_TRANSLATION
        elif button == 0: # Set rotation mode for left click
            self.mouse_mode = MOUSE_MODE_ROTATION
        self.mouse_pos = None # Flush mouse position on click 
        glutPostRedisplay()
    
    
    def get_track_ball_rotation_matrix(self, sp, ep):
        r = 1 # Because sv and ev is scaled between -1 to 1, trackball always has unit radius
        sv = point2vector(sp, r) # Convert point to vector on trackball
        ev = point2vector(ep, r) # Convert point to vector on trackball
        n = np.cross(sv, ev) # Get axis of rotation
        theta = np.linalg.norm(n)/(np.linalg.norm(sv)*np.linalg.norm(ev)) # sin(theta) ~ theta if sv and ev is very close
        
        # Construct rotation matrix from Identity matrix
        glPushMatrix()
        glLoadIdentity()
        glRotatef(ROTATION_FACTOR*theta, *n) # Rotate about n
        rotation_matrix = glGetDoublev(GL_MODELVIEW_MATRIX)
        glPopMatrix()
        return rotation_matrix

    def motion(self, x, y):  
        print(f"mouse move event: x={x}, y={y}")
        
        # Task 4
        current_pos = self.pixel2viewport(x, y) # Normalize current position between -1 to 1
        if self.mouse_pos != None:
            if self.mouse_mode == MOUSE_MODE_ROTATION: # Rotation
                self.rotation = self.get_track_ball_rotation_matrix(current_pos, self.mouse_pos)@self.rotation
            else: # Translation
                prev_x, prev_y = self.mouse_pos # Last mouse position
                diff_x, diff_y = (current_pos[0]-prev_x), current_pos[1]-prev_y # Difference between current and prev mouse positions
                # Get differences of x, y, and z components about camera position (diff_x is horizontal difference and diff_y is vertical difference about image plane)
                (dx, dy, dz) = get_translation_diff((self.cop @ self.rotation @ self.translation)[:-1], (self.at @ self.rotation @ self.translation)[:-1], (self.up @ self.rotation)[:-1], diff_x, diff_y)
                # Apply new translation to current translation matrix
                glPushMatrix()
                glLoadMatrixf(self.translation)
                glTranslatef(dx, dy, dz)
                self.translation = glGetDoublev(GL_MODELVIEW_MATRIX)
                glPopMatrix()
        self.mouse_pos = current_pos

        glutPostRedisplay()

    
    def reshape(self, w, h):
        self.window_size = (w, h) # Update window size variable, it will affect to projection and normalization
        print(f"window size: {w} x {h}")
        # glViewport(0, 0, w, h) 
        glutPostRedisplay()

    def run(self):
        glutInit()
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
        glutInitWindowSize(*self.window_size) 
        glutInitWindowPosition(0, 0)
        glutCreateWindow(b"CS471 Computer Graphics #2")

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
