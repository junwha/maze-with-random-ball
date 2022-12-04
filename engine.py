
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
    
    def __init__(self, pos, v, radius, reactionable=True):
        self.id = RigidBody._idGenerator.genNewID()
        self._pos = pos
        self.v = v
        self.radius = radius
        self.collisionTargets = set() # Collided objects to this rigid body
        self.collisionRange = [[False, False], [False, False], [False, False]] # Collided constraint lines
        self.reactionable = reactionable
        
    @property
    def pos(self):
        return self._pos
    
    @pos.setter
    def pos(self, pos):
        self._pos = pos
    
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

class EndTarget(RigidBody):
    def __init__(self, radius=UNIT_LENGTH, pos=gen_np_f32_array([0, 0, 0, 1]), v=gen_np_f32_array([0, 0, 0, 0])):
        super().__init__(pos, v, radius, reactionable=False)
        
    def draw(self):
        glColor3f(0, 0, 0.7)
        glPushMatrix()
        glTranslatef(*self.pos[:3])
        glutSolidTeapot(2*self.radius)
        glPopMatrix()
        glColor3f(1, 1, 1)
        
class Player(RigidBody):
    def __init__(self, radius=UNIT_LENGTH, pos=gen_np_f32_array([0, 0, 0, 1]), v=gen_np_f32_array([0, 0, 0, 0])):
        super().__init__(pos, v, radius, reactionable=False)
    def draw(self):
        pass
class Ball(RigidBody):
    def __init__(self, radius=UNIT_LENGTH*0.01, pos=gen_np_f32_array([0, 0, 0, 1]), v=gen_np_f32_array([0, 0, 0.5, 0]), c=gen_np_f32_array([1, 1, 1])): 
        self.c = c # Color
        super().__init__(pos, v, radius)
        
    def draw(self):
        glColor3f(*self.c)
        glPushMatrix()
        glTranslatef(*self.pos[:3])
        glutSolidSphere(self.radius, 100, 100)
        glPopMatrix()
        glColor3f(1, 1, 1)
class CollisionDetector():
    def __init__(self, cLines):
        assert cLines[0][0] < cLines[0][1] and cLines[1][0] < cLines[1][1] and cLines[2][0] < cLines[2][1]
        self.cLines = cLines # Constraint lines for the box
        self.rigidBodies = {} # Rigid bodies contained in the box
    
    # Test all rigid body in the box
    def testAll(self):
        for key1 in self.rigidBodies.keys():
            self.testCollisionOnRigidBody(self.rigidBodies[key1])
            for key2 in self.rigidBodies.keys():
                if key1 < key2:
                    self.testCollisionOnTwoRigidBody(self.rigidBodies[key1], self.rigidBodies[key2])
                    
    def addRigidBody(self, b: RigidBody):
        self.rigidBodies[b.id] = b
        
    def testCollisionOnRigidBody(self, b: RigidBody):
        for i in range(3):
            if b.pos[i]-b.radius <= self.cLines[i][0]:
                if b.tryCollideWithLine(i, 0):
                    normal = EYE_MATRIX[i]
                    err = self.cLines[i][0] - (b.pos[i]-b.radius) 
                    
                    self.triggerOnRigidBody(normal, err, b)
       
            elif b.pos[i]+b.radius >= self.cLines[i][1]:
                if b.tryCollideWithLine(i, 1):
                    normal = -EYE_MATRIX[i]
                    err = (b.pos[i]+b.radius)-self.cLines[i][1] 

                    self.triggerOnRigidBody(normal, err, b)

    def testCollisionOnTwoRigidBody(self, b1: RigidBody, b2: RigidBody):
        min_dist = b1.radius + b2.radius
        cur_dist = np.linalg.norm(b1.pos-b2.pos)
        
        if min_dist >= cur_dist:
            if not b1.tryCollideWithTarget(b2): # Already triggered
                return 
            err = min_dist-cur_dist
            self.triggerOnTwoRigidBody(err, b1, b2)
        
    def triggerOnRigidBody(self, n, err, b):
        assert np.linalg.norm(n) == 1
        
        if b is Player:
            err += 0.05
            
        b.pos = b.pos + n*err # Error correction
        
        if b.reactionable:
            b.v = b.v - (2 * (b.v@n))*n 

    def triggerOnTwoRigidBody(self, err, b1: RigidBody, b2: RigidBody):
        normal = b2.pos-b1.pos 
        unitNormal = normal/np.linalg.norm(normal) # unit normal vector from b1 to b2
        
        normalB1 = (b1.v @ unitNormal) * unitNormal
        normalB2 = (b2.v @ unitNormal) * unitNormal
        
        b1.pos = b1.pos - unitNormal*(err/2) # Error correction
        b2.pos = b2.pos + unitNormal*(err/2)
        
        if b1.reactionable:
            b1.v = b1.v - normalB1 + normalB2
        if b2.reactionable:
            b2.v = b2.v - normalB2 + normalB1
