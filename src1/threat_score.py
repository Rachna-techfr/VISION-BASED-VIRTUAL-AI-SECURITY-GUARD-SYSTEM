# Kept for import compatibility — color logic now in app.py directly
def level_to_color(loitering=False, confirmed=False):
    if confirmed: return (200, 80,   0)
    if loitering: return (0,   0, 255)
    return             (0, 200,  80)