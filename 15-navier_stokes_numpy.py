import numpy as np

import HarfangHighLevel as hl

visc = 0.0
diff = 0.0
base_force_u, base_force_v, base_force_dens = 5, 5, 100

N = 64
size = (N + 2) * (N + 2)

u = np.zeros((N + 2, N + 2))
v = np.zeros((N + 2, N + 2))
u_prev = np.zeros((N + 2, N + 2))
v_prev = np.zeros((N + 2, N + 2))
dens = np.zeros((N + 2, N + 2))
dens_prev = np.zeros((N + 2, N + 2))


def add_source(N, x, s, dt):
    x += dt * s


def set_bnd(N, b, x):
    for i in range(1, N + 1):
        x[0, i] = x[1, i] * -1 if (b == 1) else x[1, i]
        x[N + 1, i] = x[N, i] * -1 if (b == 1) else x[N, i]
        x[i, 0] = x[i, 1] * -1 if (b == 2) else x[i, 1]
        x[i, N + 1] = x[i, N] * -1 if (b == 2) else x[i, N]

    x[0, 0] = 0.5 * (x[1, 0] + x[0, 1])
    x[0, N + 1] = 0.5 * (x[1, N + 1] + x[0, N])
    x[N + 1, 0] = 0.5 * (x[N, 0] + x[N + 1, 1])
    x[N + 1, N + 1] = 0.5 * (x[N, N + 1] + x[N + 1, N])


def conv2d(a, f):
    s = f.shape + tuple(np.subtract(a.shape, f.shape) + 1)
    strd = np.lib.stride_tricks.as_strided
    subM = strd(a, shape=s, strides=a.strides * 2)
    return np.einsum("ij,ijkl->kl", f, subM)


def lin_solve(N, b, x, x0, a, c):
    for k in range(20):
        # for i in range(1, N+1):
        # 	for j in range(1, N+1):
        # 		x[i, j] = (x0[i, j] + a * (x[i-1, j] + x[i+1, j] + x[i, j-1] + x[i, j+1]))
        # 		/ c

        # double the frame rate, but it's not exactly the same, never find, close
        # enough
        x[1:-1, 1:-1] = (x0[1:-1, 1:-1] + a * (conv2d(x, np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]])))) / c

        set_bnd(N, b, x)


def diffuse(N, b, x, x0, diff, dt):
    a = dt * diff * N * N
    lin_solve(N, b, x, x0, a, 1 + 4 * a)


def advect(N, b, d, d0, u, v, dt):
    dt0 = dt * N
    for i in range(1, N + 1):
        for j in range(1, N + 1):
            x = i - dt0 * u[i, j]
            y = j - dt0 * v[i, j]
            if x < 0.5:
                x = 0.5
            if x > N + 0.5:
                x = N + 0.5
            i0 = int(x)
            i1 = i0 + 1
            if y < 0.5:
                y = 0.5
            if y > N + 0.5:
                y = N + 0.5
            j0 = int(y)
            j1 = j0 + 1
            s1 = x - i0
            s0 = 1 - s1
            t1 = y - j0
            t0 = 1 - t1
            d[i, j] = s0 * (t0 * d0[i0, j0] + t1 * d0[i0, j1]) + s1 * (t0 * d0[i1, j0] + t1 * d0[i1, j1])

    set_bnd(N, b, d)


def dens_step(N, x, x0, u, v, diff, dt):
    add_source(N, x, x0, dt)
    x0, x = x, x0
    diffuse(N, 0, x, x0, diff, dt)
    x0, x = x, x0
    advect(N, 0, x, x0, u, v, dt)


def project(N, u, v, p, div):
    # for i in range(1, N + 1):
    # 	for j in range(1, N + 1):
    # 		div[i, j] = -0.5 * (u[i+1, j] - u[i-1, j] + v[i, j+1] - v[i, j-1]) / N
    # 		p[i, j] = 0
    div[1:-1, 1:-1] = -0.5 * (conv2d(u, np.array([[0, -1, 0], [0, 0, 0], [0, 1, 0]])) + conv2d(v, np.array([[0, 0, 0], [-1, 0, 1], [0, 0, 0]]))) / N
    p[:] = 0

    set_bnd(N, 0, div)
    set_bnd(N, 0, p)

    lin_solve(N, 0, p, div, 1, 4)

    # for i in range(1, N + 1):
    # 	for j in range(1, N + 1):
    # 		u[i, j] -= 0.5 * N * (p[i+1, j] - p[i-1, j])
    # 		v[i, j] -= 0.5 * N * (p[i, j+1] - p[i, j-1])
    v[1:-1, 1:-1] -= 0.5 * N * (conv2d(p, np.array([[0, 0, 0], [-1, 0, 1], [0, 0, 0]])))
    u[1:-1, 1:-1] -= 0.5 * N * (conv2d(p, np.array([[0, -1, 0], [0, 0, 0], [0, 1, 0]])))

    set_bnd(N, 1, u)
    set_bnd(N, 2, v)


def vel_step(N, u, v, u0, v0, visc, dt):
    add_source(N, u, u0, dt)
    add_source(N, v, v0, dt)
    u0, u = u, u0
    diffuse(N, 1, u, u0, visc, dt)
    v0, v = v, v0
    diffuse(N, 2, v, v0, visc, dt)
    project(N, u, v, u0, v0)
    u0, u = u, u0
    v0, v = v, v0
    advect(N, 1, u, u0, u0, v0, dt)
    advect(N, 2, v, v0, u0, v0, dt)
    project(N, u, v, u0, v0)


def get_from_UI(dens_prev, u_prev, v_prev):
    dens_prev[:] = 0.0
    u_prev[:] = 0.0
    v_prev[:] = 0.0

    if hl.KeyDown(hl.K_F1):
        dens_prev[1, 1] = base_force_dens
    if hl.KeyDown(hl.K_F2):
        for i in range(2, 5):
            v_prev[i, 5] = base_force_v
    if hl.KeyDown(hl.K_F3):
        u_prev[3, 3] = base_force_u
    if hl.KeyDown(hl.K_F4):
        u_prev[int(N / 2.0), int(N / 2.0)] = base_force_u
        v_prev[int(N / 2.0), int(N / 2.0)] = base_force_v

    # for i in range(1, N+1):
    # 	v_prev[IX(1, i)] = base_force_v if int(N/3) < i < int(N/3*2) else 0
    # 	u_prev[IX(1, i)] = 0


def draw_dens(N, dens, u, v):
    scale = 2
    for i in range(1, N + 1):
        for j in range(1, N + 1):
            p = hl.Vec3(i / (N) - 0.5, j / (N) - 0.5, 0)
            hl.DrawLineV(p, p + (hl.Normalize(hl.Vec3(u[i, j], v[i, j], 0)) / N))
            # helper_2d.draw_quad(mat4.TransformationMatrix(p + hl.Vec3(0, 0, 0.1), hl.Vec3(0, 0, 0)), 1 / N, 1 / N, false_texture, col(dens[i, j], 0, 0))


def simulation_step(dt):
    global visc, diff, base_force_u, base_force_v, base_force_dens
    if hl.ImGuiBegin("params"):
        hl.ImGuiText(f"Forces: touches F1, F2, F3, F4")
        visc = hl.ImGuiSliderFloat("visc", visc, 0.0, 10.0)[1]
        diff = hl.ImGuiSliderFloat("diff", diff, 0.0, 1000.0)[1]
        base_force_u = hl.ImGuiSliderFloat("base_force_u", base_force_u, 0.0, 1000.0)[1]
        base_force_v = hl.ImGuiSliderFloat("base_force_v", base_force_v, 0.0, 1000.0)[1]
        base_force_dens = hl.ImGuiSliderFloat("base_force_dens", base_force_dens, 0.0, 1000.0)[1]
    hl.ImGuiEnd()

    get_from_UI(dens_prev, u_prev, v_prev)
    vel_step(N, u, v, u_prev, v_prev, visc, dt)
    dens_step(N, dens, dens_prev, u, v, diff, dt)
    draw_dens(N, dens, u, v)


hl.Init(512, 512)
hl.AddFpsCamera(0, 0, -2)

while not hl.UpdateDraw():
    simulation_step(hl.GetDTSec())

