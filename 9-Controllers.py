import HarfangHighLevel as hl

hl.Init(512, 512)

while not hl.UpdateDraw():
    if hl.ImGuiBegin("Controllers"):
        for i in range(16):
            joystick = hl.Joystick(f"joystick_slot_{i}")
            joystick.Update()
            if joystick.IsConnected():
                if hl.ImGuiCollapsingHeader(f"joystick_slot_{i}"):
                    hl.ImGuiIndent()
                    for j in range(joystick.ButtonsCount()):
                        hl.ImGuiText(f"button {j}: {joystick.Down(j)}")
                    for j in range(joystick.AxesCount()):
                        hl.ImGuiText(f"axe {j}: {joystick.Axes(j)}")
                    hl.ImGuiUnindent()
            else:
                hl.ImGuiText(f"Generic Controller: {i} not connected")
    hl.ImGuiEnd()

hl.Uninit()
