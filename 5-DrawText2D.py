import HarfangHighLevel as hl

hl.Init(512, 512)

while not hl.UpdateDraw():
    hl.DrawText2D("Hello World!", 10, 50)
    hl.DrawText2D("Bonjour", 256, 256, 2, hl.Color.Green, True)

hl.Uninit()
