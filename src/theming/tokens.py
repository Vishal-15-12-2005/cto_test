from kivy.utils import get_color_from_hex

class ColorPalette:
    # Common colors
    PRIMARY = get_color_from_hex("#6200EE")
    PRIMARY_VARIANT = get_color_from_hex("#3700B3")
    SECONDARY = get_color_from_hex("#03DAC6")
    SECONDARY_VARIANT = get_color_from_hex("#018786")
    ERROR = get_color_from_hex("#B00020")

    # Light Theme
    LIGHT_BACKGROUND = get_color_from_hex("#FFFFFF")
    LIGHT_SURFACE = get_color_from_hex("#FFFFFF")
    LIGHT_ON_PRIMARY = get_color_from_hex("#FFFFFF")
    LIGHT_ON_SECONDARY = get_color_from_hex("#000000")
    LIGHT_ON_BACKGROUND = get_color_from_hex("#000000")
    LIGHT_ON_SURFACE = get_color_from_hex("#000000")
    LIGHT_ON_ERROR = get_color_from_hex("#FFFFFF")

    # Dark Theme
    DARK_BACKGROUND = get_color_from_hex("#121212")
    DARK_SURFACE = get_color_from_hex("#1E1E1E")
    DARK_ON_PRIMARY = get_color_from_hex("#000000")
    DARK_ON_SECONDARY = get_color_from_hex("#000000")
    DARK_ON_BACKGROUND = get_color_from_hex("#FFFFFF")
    DARK_ON_SURFACE = get_color_from_hex("#FFFFFF")
    DARK_ON_ERROR = get_color_from_hex("#000000")

class Typography:
    # Font sizes
    H1 = 96
    H2 = 60
    H3 = 48
    H4 = 34
    H5 = 24
    H6 = 20
    SUBTITLE1 = 16
    SUBTITLE2 = 14
    BODY1 = 16
    BODY2 = 14
    BUTTON = 14
    CAPTION = 12
    OVERLINE = 10

class Spacing:
    XS = 4
    S = 8
    M = 16
    L = 24
    XL = 32
    XXL = 64
