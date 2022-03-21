import HarfangHighLevel as hl

width, height = 512, 512

hl.Init(width, height)
hl.AddFpsCamera(0, 1, -2, 0.3, 0, 0)

while not hl.UpdateDraw():
    hl.DrawText("Hello World!", 0, 0, 0)
    hl.DrawLine(0, -2, 0, 0, 2, 0)
    hl.DrawCross(0, 0, 0)

    hl.DrawPlane(0, 0, 0, size_x=10, size_z=10)

    # draw the render target
    hl.DrawQuad2D(width * 0.1, height * 0.5, 30, 50, "logo.png")
    hl.DrawQuad2D(width * 0.2, height * 0.5, 30, 50, color=hl.Color(0.5, 1.0, 0.0))

    hl.DrawQuad3DV(hl.Vec3(-0.5, 1, 0), hl.Vec3(-0.5, 2, 0), hl.Vec3(0.5, 2, 0), hl.Vec3(0.5, 1, 0))

hl.Uninit()
