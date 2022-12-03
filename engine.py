
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GL.shaders import *
import numpy as np
from settings import *
from utils import *

class IDGenerator:
    def __init__(self):
        self.id = -1
        
    def genNewID(self):
        self.id += 1
        return self.id
    
class RigidBody():
    _idGenerator = IDGenerator() # Static variable
    
    def __init__(self, pos, v, result_status=RESULT_TICK_A):
        self.id = RigidBody._idGenerator.genNewID()
        self.pos = pos
        self.v = v
        self.result_status = result_status
        self.collisionTargets = set() # Collided objects to this rigid body
        self.collisionRange = [[False, False]]*3 # Collided constraint lines
        
    # Result Status represents whether current result of Object is belongs to A or B.
    def get_result_status(self):
        return self.result_status
    
    def resetCollision(self):
        for i in range(3):
            for j in range(2):
                self.collisionRange[i][j] = False
        self.collisionTargets = set()
    
    def update(self):
        self.resetCollision() # Reset collisionObjects for new state
        self.pos += self.v*TICK 

    # [RigidBody-RigidBody] Test collision was processed before, if not, return True
    def tryCollideWithTarget(self, target: 'RigidBody'): 
        if target.id in self.collisionTargets:
            return False
        self.collisionTargets.add(target.id)
        target.tryCollideWithTarget(self)
        return True

    # [RigidBody-Line] Test collision was processed before, if not, return True
    def tryCollideWithLine(self, ax, i):
        if self.collisionRange[ax][i]:
            return False
        self.collisionRange[ax][i] = True
        return True
    
    def draw(self):
        pass 
    
class Ball(RigidBody):
    def __init__(self, radius=UNIT_LENGTH*0.5, pos=gen_np_f32_array([0, 0, 0]), v=gen_np_f32_array([0, 0, 0.5])): 
        self.radius = radius
        
        super().__init__(pos, v)
        
    def draw(self):
        glColor3f(0, 1, 1)
        glPushMatrix()
        glTranslatef(*self.pos)
        glutSolidSphere(self.radius, 100, 100)
        glPopMatrix()
        glColor3f(1, 1, 1)

class ConstraintBox():
    def __init__(self, cLines=gen_np_f32_array([[-UNIT_LENGTH, UNIT_LENGTH], [-UNIT_LENGTH, UNIT_LENGTH], [-UNIT_LENGTH, UNIT_LENGTH]])): # Initialize constraint lines
        assert cLines[0][0] < cLines[0][1] and cLines[1][0] < cLines[1][1] and cLines[2][0] < cLines[2][1]
        self.cLines = cLines
        
    def testBall(self, b: Ball): # return (normal vector, error, line) on collision, otherwise 0 vector
        for i in range(3):
            if (b.pos[i]-b.radius) <= self.cLines[i][0]:
                return (EYE_MATRIX[i], (b.radius-(b.pos[i]-self.cLines[i][0])), (i, 0))
            elif (b.pos[i]+b.radius) >= self.cLines[i][1]:
                return (-EYE_MATRIX[i], (b.radius-(self.cLines[i][1]-b.pos[i])), (i, 1))
        
        return (ZERO_VECTOR, ZERO_VECTOR, None) 
    
class CollisionDetector():
    def __init__(self):
        self.balls = {}
        self.constraintBox = ConstraintBox(cLines=gen_np_f32_array([[-3*UNIT_LENGTH, UNIT_LENGTH], [-3*UNIT_LENGTH, 3*UNIT_LENGTH], [-3*UNIT_LENGTH, 3*UNIT_LENGTH]]))
    
    def testAll(self):
        for key1 in self.balls.keys():
            self.testCollisionOnOneBall(self.balls[key1])
            for key2 in self.balls.keys():
                if key1 < key2:
                    self.testCollisionOnTwoBalls(self.balls[key1], self.balls[key2])
                    
    def addBall(self, b):
        self.balls[b.id] = b

    def testCollisionOnOneBall(self, b: Ball):
        normalFromWall, err, line = self.constraintBox.testBall(b)
        
        if np.linalg.norm(normalFromWall) == 0:
            return

        if not b.tryCollideWithLine(*line): # Already triggered
            return
        
        self.triggerOnOneBall(normalFromWall, err, b)
        
    def testCollisionOnTwoBalls(self, b1: Ball, b2: Ball):
        min_dist = b1.radius + b2.radius
        cur_dist = np.linalg.norm(b1.pos-b2.pos)
        
        if min_dist >= cur_dist:
            if not b1.tryCollideWithTarget(b2): # Already triggered
                return 
            err = min_dist-cur_dist
            self.triggerOnTwoBalls(err, b1, b2)
        
        
    def triggerOnOneBall(self, n, err, b):
        
        assert np.linalg.norm(n) == 1

        b.pos = b.pos + n*err # Error correction
        b.v = b.v - (2 * (b.v@n))*n 
        
    def triggerOnTwoBalls(self, err, b1: Ball, b2: Ball):
        normal = b2.pos-b1.pos 
        unitNormal = normal/np.linalg.norm(normal) # unit normal vector from b1 to b2
        
        normalB1 = (b1.v @ unitNormal) * unitNormal
        normalB2 = (b2.v @ unitNormal) * unitNormal
        
        b1.pos = b1.pos - unitNormal*(err/2) # Error correction
        b2.pos = b2.pos + unitNormal*(err/2)
        
        b1.v = b1.v - normalB1 + normalB2
        b2.v = b2.v - normalB2 + normalB1