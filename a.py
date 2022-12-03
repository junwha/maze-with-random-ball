8c8
< FPS = 144
---
> FPS = 15
36a37
> VELOCITY = 0.1
47,65d47
< 
< UNIT_LENGTH = 1
< WALL_HEIGHT = 5*UNIT_LENGTH
< ROAD_HEIGHT = 1
< VELOCITY = UNIT_LENGTH*0.5
< 
< TICK = 0.05 # 1/FPS
< 
< RESULT_TICK_A = True
< RESULT_TICK_B = False
< 
< EYE_MATRIX = np.eye(3)
< 
< def gen_np_f32_array(array):
<     return np.array(array, dtype="float32")
< 
< ZERO_VECTOR = gen_np_f32_array([0, 0, 0])
< 
< 
70a53,68
> def getCameraView(px, py, pz, ax, ay, az, ux, uy, uz, trans):
>     p = np.array([px, py, pz])
>     at = np.array([ax, ay, az])
>     up = np.array([ux, uy, uz])
>     z = p - at
>     z = z / np.linalg.norm(z)
>     x = np.cross(up, z)
>     x = x / np.linalg.norm(x)
>     y = np.cross(z, x)
>     R = np.array([[x[0], y[0], z[0], 0],
>                   [x[1], y[1], z[1], 0],
>                   [x[2], y[2], z[2], 0],
>                   [-np.dot(p, x), -np.dot(p, y), -np.dot(p, z), 1]
>     ])
>     return R
> 
72,74c70,72
<     p = gen_np_f32_array([px, py, pz])
<     at = gen_np_f32_array([ax, ay, az])
<     up = gen_np_f32_array([ux, uy, uz])
---
>     p = np.array([px, py, pz])
>     at = np.array([ax, ay, az])
>     up = np.array([ux, uy, uz])
86c84
<     return gen_np_f32_array([[c, 0, -s, 0],
---
>     return np.array([[c, 0, -s, 0],
89c87
<                     [0, 0, 0, 1]])
---
>                     [0, 0, 0, 1]], dtype=np.float32)
95c93
<     return gen_np_f32_array([[1, 0, 0, 0],
---
>     return np.array([[1, 0, 0, 0],
98c96
<                     [0, 0, 0, 1]])
---
>                     [0, 0, 0, 1]], dtype=np.float32)
146,247d143
< class RigidBody():
<     def __init__(self, pos, v, result_status=RESULT_TICK_A):
<         self.pos = pos
<         self.v = v
<         self.result_status = result_status
<     
<     # Result Status represents whether current result of Object is belongs to A or B.
<     def get_result_status(self):
<         return self.result_status
<     
<     def update(self):
<         self.pos += self.v*TICK 
< 
<     # def apply_collision_result(self, v):
<     #     self.v = v
<     #     self.result_status = RESULT_TICK_B if RESULT_TICK_A else RESULT_TICK_A
<     
<     def draw(self):
<         pass 
<     
< class Ball(RigidBody):
<     def __init__(self, radius=UNIT_LENGTH*0.5, pos=gen_np_f32_array([0, 0, 0]), v=gen_np_f32_array([0, 0, 0.5])): 
<         self.radius = radius
<         super().__init__(pos, v)
<         
<     def draw(self):
<         glColor3f(0, 1, 1)
<         glPushMatrix()
<         glTranslatef(*self.pos)
<         glutSolidSphere(self.radius, 100, 100)
<         glPopMatrix()
<         glColor3f(1, 1, 1)
< 
< class ConstraintBox():
<     def __init__(self, cLines=gen_np_f32_array([[-UNIT_LENGTH, UNIT_LENGTH], [-UNIT_LENGTH, UNIT_LENGTH], [-UNIT_LENGTH, UNIT_LENGTH]])): # Initialize constraint lines
<         assert cLines[0][0] < cLines[0][1] and cLines[1][0] < cLines[1][1] and cLines[2][0] < cLines[2][1]
<         self.cLines = cLines
<         
<     def testBall(self, b: Ball): # return (normal vector, error) on collision, otherwise 0 vector
<         
<         for i in range(3):
<             if (b.pos[i]-b.radius) <= self.cLines[i][0]:
<                 return (EYE_MATRIX[i], (b.radius-(b.pos[i]-self.cLines[i][0])))
<             elif (b.pos[i]+b.radius) >= self.cLines[i][1]:
<                 return (-EYE_MATRIX[i], (b.radius-(self.cLines[i][1]-b.pos[i])))
<         
<         return (ZERO_VECTOR, ZERO_VECTOR) 
< class CollisionDetector():
<     def __init__(self):
<         self.balls = []
<         self.boundaries = []
<         self.constraintBox = ConstraintBox(cLines=gen_np_f32_array([[-3*UNIT_LENGTH, UNIT_LENGTH], [-3*UNIT_LENGTH, 3*UNIT_LENGTH], [-3*UNIT_LENGTH, 3*UNIT_LENGTH]]))
<         # TODO: matrix needed
<     
<     def testAll(self):
<         for i in range(len(self.balls)):
<             self.testCollisionOnOneBall(self.balls[i])
<             for j in range(len(self.balls)):
<                 if i < j:
<                     self.testCollisionOnTwoBalls(self.balls[i], self.balls[j])
<                     
<     def addBall(self, b):
<         # TODO: 
<         self.balls.append(b)
< 
<     def testCollisionOnOneBall(self, b):
<         normalFromWall, err = self.constraintBox.testBall(b)
<         
<         if np.linalg.norm(normalFromWall) == 0:
<             return
<         
<         self.triggerOnOneBall(normalFromWall, err, b)
<         
<     def testCollisionOnTwoBalls(self, b1: Ball, b2: Ball):
<         min_dist = b1.radius + b2.radius
<         cur_dist = np.linalg.norm(b1.pos-b2.pos)
<         
<         if min_dist >= cur_dist:
<             err = min_dist-cur_dist
<             self.triggerOnTwoBalls(err, b1, b2)
<         
<         
<     def triggerOnOneBall(self, n, err, b):
<         
<         assert np.linalg.norm(n) == 1
< 
<         b.pos = b.pos + n*err # Error correction
<         b.v = b.v - (2 * (b.v@n))*n 
<         
<     def triggerOnTwoBalls(self, err, b1: Ball, b2: Ball):
<         normal = b2.pos-b1.pos 
<         unitNormal = normal/np.linalg.norm(normal) # unit normal vector from b1 to b2
<         
<         normalB1 = (b1.v @ unitNormal) * unitNormal
<         normalB2 = (b2.v @ unitNormal) * unitNormal
<         
<         b1.pos = b1.pos - unitNormal*(err/2) # Error correction
<         b2.pos = b2.pos + unitNormal*(err/2)
<         
<         b1.v = b1.v - normalB1 + normalB2
<         b2.v = b2.v - normalB2 + normalB1
<         
251c147
<         self.cameraMatrix = gen_np_f32_array([
---
>         self.cameraMatrix = np.array([
264c160
<         self.trans = gen_np_f32_array([-10*UNIT_LENGTH, UNIT_LENGTH*2, UNIT_LENGTH, .0])
---
>         self.trans = np.array([-0.5, 0.4, 0.1, .0])
268,276d163
<         self.sample_ball = [
<             Ball(pos=gen_np_f32_array([-1*UNIT_LENGTH, 1.5*UNIT_LENGTH, -1*UNIT_LENGTH]), v=gen_np_f32_array([0, 1, 1])),
<             Ball(pos=gen_np_f32_array([-1*UNIT_LENGTH, 1*UNIT_LENGTH, 1*UNIT_LENGTH]), v=gen_np_f32_array([0, 0, 2])),
<             Ball(pos=gen_np_f32_array([-1*UNIT_LENGTH, 0, 0]), v=gen_np_f32_array([0, -3, 0]))
<         ]
<         self.collisionDetector = CollisionDetector()
<         for ball in self.sample_ball:
<             self.collisionDetector.addBall(ball)
<         
290c177
<         glLightfv(GL_LIGHT0, GL_LINEAR_ATTENUATION, 0.1)
---
>         glLightfv(GL_LIGHT0, GL_LINEAR_ATTENUATION, 1)
305,307c192,195
<    
<         gluPerspective(self.fov, self.w/self.h, 0.0001, 10000)
<         
---
>         if self.fov == 0:
>             glOrtho(-self.w/self.h, self.w/self.h, -1, 1, 0.0001, 10000)
>         else:
>             gluPerspective(self.fov, self.w/self.h, 0.0001, 10000)
312,314c200,202
<         pos = gen_np_f32_array([0, 0, 0, 0]) @ self.cameraMatrix + self.trans 
<         at = gen_np_f32_array([0, 0, -d, 0]) @ self.cameraMatrix + self.trans
<         up = (gen_np_f32_array([0, 1, 0, 0])) @ self.cameraMatrix
---
>         pos = np.array([0, 0, 0, 0]) @ self.cameraMatrix + self.trans 
>         at = np.array([0, 0, -d, 0]) @ self.cameraMatrix + self.trans
>         up = (np.array([0, 1, 0, 0])) @ self.cameraMatrix
325c213
<                     drawCube(size=(UNIT_LENGTH, UNIT_LENGTH*WALL_HEIGHT, UNIT_LENGTH), pos=(UNIT_LENGTH*i, UNIT_LENGTH*WALL_HEIGHT/2, UNIT_LENGTH*j))
---
>                     drawCube(size=(0.1, 0.5, 0.1), pos=(0.1*i, 0.25, 0.1*j))
327,338c215
<                     drawCube(size=(UNIT_LENGTH, UNIT_LENGTH*ROAD_HEIGHT, UNIT_LENGTH), pos=(UNIT_LENGTH*i, UNIT_LENGTH*ROAD_HEIGHT/2, UNIT_LENGTH*j))
<         
<         # self.collisionDetector.testAll()
<         
<         # self.sample_ball[0].update()
<         # self.sample_ball[1].update()
<         # self.sample_ball[2].update()
<         
<         # self.sample_ball[0].draw()
<         # self.sample_ball[1].draw()
<         # self.sample_ball[2].draw()
<         
---
>                     drawCube(size=(0.1, 0.2, 0.1), pos=(0.1*i, 0.1, 0.1*j))
345,347c222,224
<         pos = gen_np_f32_array([0, 0, 0, 0]) @ self.cameraMatrix + self.trans 
<         at = gen_np_f32_array([0, 0, -d, 0]) @ self.cameraMatrix + self.trans
<         up = (gen_np_f32_array([0, 1, 0, 0])) @ self.cameraMatrix
---
>         pos = np.array([0, 0, 0, 0]) @ self.cameraMatrix + self.trans 
>         at = np.array([0, 0, -d, 0]) @ self.cameraMatrix + self.trans
>         up = (np.array([0, 1, 0, 0])) @ self.cameraMatrix
397a275
>             print(self.degx, self.degy)
401,403c279,281
<             pos = gen_np_f32_array([0, 0, 1, 0]) @ self.cameraMatrix + self.trans
<             at = gen_np_f32_array([0, 0, 0, 0]) + self.trans
<             up = gen_np_f32_array([0, 1, 0, 0]) @ self.cameraMatrix
---
>             pos = np.array([0, 0, 1, 0]) @ self.cameraMatrix + self.trans
>             at = np.array([0, 0, 0, 0]) + self.trans
>             up = np.array([0, 1, 0, 0]) @ self.cameraMatrix
