"""
Color utility functions for theme-aware Cairo drawing.

Provides RGB/HSL conversion and manipulation functions to extract colors
from GTK CSS themes and apply them to Cairo drawing contexts.
"""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


def get_css_color(widget, color_name='color'):
    """
    Extract RGB color from widget's CSS style context.

    Args:
        widget: GTK widget with style context
        color_name: CSS color property name (default: 'color')

    Returns:
        Tuple of (r, g, b) in range 0.0-1.0
    """
    style_context = widget.get_style_context()
    color = style_context.get_color(Gtk.StateFlags.NORMAL)
    return (color.red, color.green, color.blue)


def get_css_named_color(widget, color_name):
    """
    Extract RGB from a named CSS color variable like '@solarized-red'.

    Args:
        widget: GTK widget with style context
        color_name: CSS variable name (without @, e.g., 'solarized-red')

    Returns:
        Tuple of (r, g, b) in range 0.0-1.0, or None if not found
    """
    style_context = widget.get_style_context()
    found, color_rgba = style_context.lookup_color(color_name)
    if found:
        return (color_rgba.red, color_rgba.green, color_rgba.blue)
    return None


def rgb_to_hsl(r, g, b):
    """
    Convert RGB to HSL color space.

    Args:
        r, g, b: RGB values in range 0.0-1.0

    Returns:
        Tuple of (h, s, l) where:
            h: hue in range 0.0-1.0 (0=red, 0.33=green, 0.67=blue)
            s: saturation in range 0.0-1.0 (0=gray, 1=full color)
            l: lightness in range 0.0-1.0 (0=black, 0.5=pure, 1=white)
    """
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    l = (max_c + min_c) / 2.0

    if max_c == min_c:
        h = s = 0.0  # Achromatic (gray)
    else:
        d = max_c - min_c
        s = d / (2.0 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)

        if max_c == r:
            h = (g - b) / d + (6.0 if g < b else 0.0)
        elif max_c == g:
            h = (b - r) / d + 2.0
        else:
            h = (r - g) / d + 4.0
        h /= 6.0

    return (h, s, l)


def hsl_to_rgb(h, s, l):
    """
    Convert HSL to RGB color space.

    Args:
        h: hue in range 0.0-1.0
        s: saturation in range 0.0-1.0
        l: lightness in range 0.0-1.0

    Returns:
        Tuple of (r, g, b) in range 0.0-1.0
    """
    def hue_to_rgb(p, q, t):
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1/6:
            return p + (q - p) * 6 * t
        if t < 1/2:
            return q
        if t < 2/3:
            return p + (q - p) * (2/3 - t) * 6
        return p

    if s == 0:
        r = g = b = l  # Achromatic
    else:
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1/3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1/3)

    return (r, g, b)


def invert_lightness(r, g, b):
    """
    Create high-contrast inverse color by mirroring lightness around 50%.

    For light colors (L >= 50%), creates a dark version.
    For dark colors (L < 50%), returns pure black for maximum contrast.

    Args:
        r, g, b: RGB values in range 0.0-1.0

    Returns:
        Tuple of (r, g, b) in range 0.0-1.0
    """
    h, s, l = rgb_to_hsl(r, g, b)

    if l >= 0.5:
        # Light color - invert to dark
        l_inverse = 1.0 - l
        return hsl_to_rgb(h, s, l_inverse)
    else:
        # Already dark - return pure black for maximum contrast
        return (0.0, 0.0, 0.0)


def saturation_gradient(r, g, b, value, max_value):
    """
    Create gradient by varying saturation from white (S=0) to full color.

    Useful for heatmap-style gradients where intensity increases from
    white to a theme color.

    Args:
        r, g, b: Base RGB color in range 0.0-1.0
        value: Current value (can be negative)
        max_value: Maximum absolute value for scaling

    Returns:
        Tuple of (r, g, b) in range 0.0-1.0
    """
    h, s, l = rgb_to_hsl(r, g, b)

    # Calculate intensity (0.0 = white, 1.0 = full color)
    intensity = min(1.0, abs(value) / max_value) if max_value > 0 else 0.0

    # Scale saturation: 0 at value=0 (white), full S at value=max_value
    s_scaled = s * intensity

    return hsl_to_rgb(h, s_scaled, l)
