import HarfangHighLevel as hl

hl.Init(512, 512)

while not hl.UpdateDraw():
    if hl.ImGuiBegin("Window"):
        hl.ImGuiText("Hello World!")
    hl.ImGuiEnd()

hl.Uninit()
