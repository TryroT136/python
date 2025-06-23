# Ball physics simulation with pygame
# Controls:
#   Space: Randomize ball velocities
#   C: Stop all balls
#   V: Spawn balls
#   R: Reset balls
#   B: Remove balls
#   G: Drag to set spawn velocity
#   A: Gravitate balls
#   D: Push balls
#   Scroll: Change spawn size and effect size
#   Click and drag: Move balls

import pygame
import math as m
import random as r
import sys

window_size = [1200, 600]
PI = 3.14159
gravity = 0.2
air_density = 0.001
num_balls = 100
render_trails = True

class Ball:
    def __init__(self, x, y, vx, vy, mass, radius, fric, color):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.mass = mass
        self.radius = radius
        self.fric = fric
        self.color = color

    def draw(self, screen, oldpos):
        pygame.draw.circle(ball_disp, self.color, (self.x, self.y), self.radius)
        if render_trails:
            pygame.draw.circle(ball_disp, self.color, (oldpos[0], oldpos[1]), self.radius)
            pygame.draw.line(ball_disp, self.color, (self.x, self.y), (oldpos[0], oldpos[1]), self.radius*2)

    def apply_force(self, force, angle):
        force_x = force * m.cos(angle)
        force_y = force * m.sin(angle)
        self.vx += force_x / self.mass
        self.vy += force_y / self.mass

    def collide(self, other_x, other_y, other_radius):
        dx = self.x - other_x
        dy = self.y - other_y
        if abs(dx) > self.radius + other_radius or abs(dy) > self.radius + other_radius:
            return False
        dist = m.sqrt(dx*dx + dy*dy)
        return dist < self.radius + other_radius

    def bound(self, screen_width, screen_height, gravity):
        if self.x < self.radius or self.x > screen_width - self.radius:
            self.vx *= -1

            self.apply_friction()

        # if self.y < self.radius:
        #     self.vy *= -self.fric
        if self.y > screen_height - self.radius:
            self.vy *= -1

            self.y = screen_height - self.radius
            
            self.apply_friction()
        
        self.x = clamp(self.x, self.radius, screen_width - self.radius)
        # self.y = clamp(self.y, self.radius, screen_height - self.radius)

    def apply_friction(self):
        vel = m.sqrt(self.vx**2 + self.vy**2)
        veldir = m.atan2(self.vy, self.vx)

        vel *= self.fric

        self.vx = m.cos(veldir) * vel
        self.vy = m.sin(veldir) * vel

    def bounce(self, other, gravity):
        dx = self.x - other.x
        dy = self.y - other.y
        dist = m.sqrt(dx**2 + dy**2)
        if dist == 0:
            dist = 0.01  # Prevent division by zero

        nx = dx / dist
        ny = dy / dist

        p = 2 * (self.vx * nx + self.vy * ny - other.vx * nx - other.vy * ny) / (self.mass + other.mass)
        self.vx -= p * other.mass * nx
        self.vy -= p * other.mass * ny
        other.vx += p * self.mass * nx
        other.vy += p * self.mass * ny

        self.apply_friction()
        other.apply_friction()

        overlap = 0.5 * (self.radius + other.radius - dist + 1)
        self.x += nx * overlap
        self.y += ny * overlap
        other.x -= nx * overlap
        other.y -= ny * overlap
    
    def apply_drag(self, air_density, v):
        Cd = 0.47 # drag coefficient for a sphere
        F_drag = 0.5 * air_density * v**2 * (self.mass) * Cd # mass is used as the area because the area is the same as the mass in this case
        theta = m.atan2(self.vy, self.vx)
        self.apply_force(-F_drag, theta)

    def move(self, ball_list, gravity, air_density, screen_size):
        try:
            v = m.sqrt(self.vx**2 + self.vy**2)
        except:
            v = m.floor(m.sqrt(sys.float_info.max))
        v = clamp(v, 0, m.floor(m.sqrt(sys.float_info.max)))
        self.apply_drag(air_density, v)
        self.vy += gravity
        self.x += self.vx
        self.y += self.vy
        self.bound(screen_size[0], screen_size[1], gravity)

        for ball in ball_list:
            if self is not ball and self.collide(ball.x, ball.y, ball.radius):
                self.bounce(ball, gravity)

def hsv_to_rgb(h, s, v): # hue: 0-360, saturation: 0-100, value: 0-100
    h /= 360
    s /= 100
    v /= 100
    if s == 0:
        return (v, v, v)
    i = int(h * 6.)
    f = (h * 6.) - i
    p = v * (1. - s)
    q = v * (1. - s * f)
    t = v * (1. - s * (1. - f))
    i = i%6
    if i == 0:
        return (v, t, p)
    if i == 1:
        return (q, v, p)
    if i == 2:
        return (p, v, t)
    if i == 3:
        return (p, q, v)
    if i == 4:
        return (t, p, v)
    if i == 5:
        return (v, p, q)

def clamp(n, mn, mx):
    if type(n) == tuple:
        return tuple(max(mn, min(x, mx)) for x in n)
    return max(mn, min(n, mx))

def tuple_mult(t, n):
    return tuple(int(x * n) for x in t)

pygame.init()
pygame.font.init()
font = pygame.font.SysFont('Arial', 30)
screen = pygame.display.set_mode(window_size)#, pygame.RESIZABLE)
ball_disp = pygame.Surface(screen.get_size())
ui_indicators = pygame.Surface(screen.get_size(), pygame.SRCALPHA)#, pygame.RESIZABLE)
pygame.display.set_caption('Ball Physics')
clock = pygame.time.Clock()
running = True
mouse_down = False
move_balls = False
move_balls_up = False
move_balls_down = False
move_balls_left = False
move_balls_right = False
gravitate_balls = False
push_balls = False
spawn_balls = False
remove_balls = False
spawn_size = 10
spawn_cooldown = 0
spawn_size_draw_timer = 0
spawn_vel = (0, 0)
spawn_vel_choosing = False
spawn_vel_start_pos = (0, 0)
weightless = 0
selected_ball = -1

def add_ball(pos=False, x=0, y=0, vel=False, vx=0, vy=0, rad=False, rad_in=0):
    if rad:
        radius = rad_in
    else:
        radius = r.randint(5, 30)
    
    if pos:
        bx = x
        by = y
    else:
        bx = r.randint(radius, window_size[0] - radius)
        by = r.randint(radius, window_size[1] - radius)
    
    if vel:
        bvx = vx
        bvy = vy
    else:
        bvx = (r.random()*2-1)*10
        bvy = (r.random()*2-1)*10
    
    balls.append(Ball(
        x=bx,
        y=by,
        vx=bvx,
        vy=bvy,
        mass=PI*radius*radius,
        radius=radius,
        fric=0.9,
        color=clamp(tuple_mult(hsv_to_rgb(r.random()*360, 100, 100), 255), 1, 255)
    ))

balls = []

for i in range(num_balls):
    radius_temp = r.randint(5, 30)
    add_ball(
        pos=True,
        x = r.randint(radius_temp, window_size[0]-radius_temp),
        y = r.randint(radius_temp, window_size[1]-radius_temp),
        rad = True,
        rad_in = radius_temp,
        vel = True,
        vx = 0,
        vy = 0
    )

while running:
    mx = clamp(pygame.mouse.get_pos()[0], 0, window_size[0])
    my = clamp(pygame.mouse.get_pos()[1], 0, window_size[1])

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # elif event.type == pygame.VIDEORESIZE:
        #     window_size = screen.get_size()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_SPACE:
                move_balls = True
                weightless += 1
            elif event.key == pygame.K_c:
                for ball in balls:
                    ball.vx = 0
                    ball.vy = 0
            elif event.key == pygame.K_v:
                spawn_balls = True
            elif event.key == pygame.K_r:
                balls = []
                # for _ in range(num_balls):
                #     add_ball()
            elif event.key == pygame.K_b:
                remove_balls = True
            elif event.key == pygame.K_g:
                spawn_vel_choosing = True
                spawn_vel_start_pos = (mx, my)
            elif event.key == pygame.K_a:
                gravitate_balls = True
                weightless += 1
            elif event.key == pygame.K_d:
                push_balls = True
                weightless += 1
            elif event.key == pygame.K_UP:
                move_balls_up = True
                weightless += 1
            elif event.key == pygame.K_DOWN:
                move_balls_down = True
                weightless += 1
            elif event.key == pygame.K_LEFT:
                move_balls_left = True
                weightless += 1
            elif event.key == pygame.K_RIGHT:
                move_balls_right = True
                weightless += 1
        
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                move_balls = False
                weightless -= 1
            elif event.key == pygame.K_v:
                spawn_balls = False
            elif event.key == pygame.K_b:
                remove_balls = False
            elif event.key == pygame.K_g:
                spawn_vel = ((mx - spawn_vel_start_pos[0]) / 10, (my - spawn_vel_start_pos[1]) / 10)
                spawn_vel_choosing = False
            elif event.key == pygame.K_a:
                gravitate_balls = False
                weightless -= 1
            elif event.key == pygame.K_d:
                push_balls = False
                weightless -= 1
            elif event.key == pygame.K_UP:
                move_balls_up = False
                weightless -= 1
            elif event.key == pygame.K_DOWN:
                move_balls_down = False
                weightless -= 1
            elif event.key == pygame.K_LEFT:
                move_balls_left = False
                weightless -= 1
            elif event.key == pygame.K_RIGHT:
                move_balls_right = False
                weightless -= 1
        
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_down = True
            for i, ball in enumerate(balls):
                if ball.collide(mx, my, 0):
                    selected_ball = i
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            mouse_down = False
            selected_ball = -1
        
        # scroll to change spawned ball size
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 4:
            spawn_size += 2
            spawn_size_draw_timer = 120
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 5:
            spawn_size -= 2
            if spawn_size < 1:
                spawn_size = 1
            spawn_size_draw_timer = 120


    screen.fill((0, 0, 0))
    ball_disp.fill((0, 0, 0))
    # pygame.draw.rect(ui_indicators, (0, 0, 0, 10), (0, 0, window_size[0], window_size[1]))
    ui_indicators.fill((0, 0, 0, 0))

    for i, ball in enumerate(balls):
        if mouse_down and i == selected_ball:
            ball.vx += (((mx - ball.x) - ball.vx) / (ball.mass * 0.01)) * (spawn_size/10)
            ball.vy += (((my - ball.y) - ball.vy) / (ball.mass * 0.01)) * (spawn_size/10)
        oldpos = (ball.x, ball.y)
        ball.move(balls, gravity * (0 if weightless > 0 else 1), air_density, window_size)
        ball.draw(screen, oldpos)
    
    if spawn_vel_choosing:
        pygame.draw.line(ui_indicators, (255, 255, 255, 200), spawn_vel_start_pos, (mx, my), 2)

    if move_balls:
        for ball in balls:
                    ball.vx += (r.random()*2-1) * 20
                    ball.vy += (r.random()*2-1) * 20
    
    if gravitate_balls:
        for ball in balls:
            dx = ball.x - mx
            dy = ball.y - my
            # dist = m.sqrt(dx**2 + dy**2)
            force = (spawn_size*0.1 / ball.mass)
            ball.vx -= dx * force
            ball.vy -= dy * force
    elif push_balls:
        for ball in balls:
            dx = ball.x - mx
            dy = ball.y - my
            # dist = m.sqrt(dx**2 + dy**2)
            force = (spawn_size*0.1 / ball.mass) * -1
            ball.vx -= dx * force
            ball.vy -= dy * force
    
    if move_balls_up:
        for ball in balls:
            ball.vy -= 1
    if move_balls_down:
        for ball in balls:
            ball.vy += 1
    if move_balls_left:
        for ball in balls:
            ball.vx -= 1
    if move_balls_right:
        for ball in balls:
            ball.vx += 1
    
    if spawn_balls and spawn_cooldown < 1:
        add_ball(True, mx, my, True, spawn_vel[0], spawn_vel[1], True, spawn_size)
        spawn_cooldown = 1
    elif spawn_cooldown > 0:
        spawn_cooldown -= 1
    
    if spawn_size_draw_timer > 0:
        pygame.draw.circle(ui_indicators, (255, 255, 255, 100), (mx, my), spawn_size)
        spawn_size_draw_timer -= 1
    
    if remove_balls:
        pygame.draw.circle(ui_indicators, (255, 20, 20, 100), (mx, my), spawn_size)
        nballs = []
        for i, ball in enumerate(balls):
            if not ball.collide(mx, my, spawn_size):
                nballs.append(ball)
        balls = nballs
        if selected_ball > len(balls)-1:
            if len(balls) == 0:
                selected_ball = -1
            else:
                selected_ball = len(balls)-1

    if mouse_down and selected_ball != -1:
        for i in range(20):
            dx = (balls[selected_ball].x - mx) / 20
            dy = (balls[selected_ball].y - my) / 20
            try:
                pygame.draw.circle(ui_indicators, (255, 255, 255, 200), (mx + dx * i, my + dy * i), m.sqrt((dx * (20 - i))**2 + (dy * (20 - i))**2) / 30 + 1)
            except:
                pygame.draw.rect(ui_indicators, (255, 255, 255, 200), (0, 0, window_size[0], window_size[1]))

    fps = font.render(str(int(clock.get_fps())), True, (255, 255, 255))
    count = font.render(str(len(balls)), True, (255, 255, 255))
    debug = font.render(str(weightless), True, (255, 255, 255))

    screen.blit(ball_disp, (0, 0))
    screen.blit(ui_indicators, (0, 0))
    screen.blit(fps, (10, 10))
    screen.blit(count, (10, 40))
    screen.blit(debug, (10, 70))

    pygame.display.flip()
    clock.tick(60)
