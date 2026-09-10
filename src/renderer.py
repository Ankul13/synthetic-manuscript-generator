from pathlib import Path
import random

from PIL import Image, ImageDraw, ImageFont

from .effects import apply_text_effects
from .handwriting import apply_handwriting_variation
from .layout import (
    draw_margin_markers,
    draw_section_marker,
    highlight_text_region,
)


def render_text(
    text,
    font_path,
    background_path,
    output_path,
    image_width=1600,
    image_height=1000,
    font_size=45,
    margin=130,
    line_spacing=25,
    seed=42,
):
    """
    Render manuscript text on an aged background.

    The function:
    1. Loads the manuscript background.
    2. Adds historical-style layout elements.
    3. Wraps text inside page boundaries.
    4. Renders complete lines to preserve Indic shaping.
    5. Adds handwriting variation.
    6. Adds ink fading, bleeding and smudging.
    7. Saves the final rendered manuscript.
    """

    rng = random.Random(seed)

    # --------------------------------------------------
    # STEP 1: Load background
    # --------------------------------------------------

    background_path = Path(background_path)
    font_path = Path(font_path)
    output_path = Path(output_path)

    if not background_path.exists():
        raise FileNotFoundError(
            f"Background file not found:\n{background_path}"
        )

    if not font_path.exists():
        raise FileNotFoundError(
            f"Font file not found:\n{font_path}"
        )

    image = Image.open(background_path).convert("RGB")

    image = image.resize(
        (image_width, image_height),
        Image.Resampling.LANCZOS,
    )

    # --------------------------------------------------
    # STEP 2: Load script font
    # --------------------------------------------------

    font = ImageFont.truetype(
        str(font_path),
        font_size,
    )

    # --------------------------------------------------
    # STEP 3: Add manuscript layout elements
    # --------------------------------------------------

    image = draw_margin_markers(
        image,
        margin=margin,
    )

    section_y = rng.randint(
        int(image_height * 0.70),
        int(image_height * 0.80),
    )

    image = draw_section_marker(
        image,
        y=section_y,
        margin=margin,
    )

    # Add subtle highlighted manuscript region.
    # It is applied BEFORE text so the text remains readable.
    highlight_y = rng.randint(
        int(image_height * 0.20),
        int(image_height * 0.35),
    )

    image = highlight_text_region(
        image,
        x=margin,
        y=highlight_y,
        width=rng.randint(400, 650),
        height=48,
        opacity=20,
    )

    # --------------------------------------------------
    # STEP 4: Define writing boundaries
    # --------------------------------------------------

    x_start = margin
    y = margin

    max_width = image_width - (2 * margin)
    max_height = image_height - margin

    # --------------------------------------------------
    # STEP 5: Wrap text into manuscript lines
    # --------------------------------------------------

    words = text.split()

    lines = []
    current_line = ""

    for word in words:

        test_line = (
            current_line + " " + word
        ).strip()

        bbox = font.getbbox(test_line)

        line_width = (
            bbox[2] - bbox[0]
        )

        if line_width <= max_width:

            current_line = test_line

        else:

            if current_line:
                lines.append(current_line)

            current_line = word

    if current_line:
        lines.append(current_line)

    # --------------------------------------------------
    # STEP 6: Render every manuscript line
    # --------------------------------------------------

    for line in lines:

        # Stop before leaving bottom boundary
        if y > max_height:
            break

        # Small position variations simulate
        # irregular historical handwriting.
        x_jitter = rng.randint(-5, 5)
        y_jitter = rng.randint(-3, 3)

        # Slight line rotation
        rotation = rng.uniform(
            -1.2,
            1.2,
        )

        # --------------------------------------------------
        # Ink color variation
        # --------------------------------------------------

        ink_value = rng.randint(
            40,
            70,
        )

        ink_color = (
            min(255, ink_value + 10),
            max(0, ink_value - 5),
            max(0, ink_value - 20),
        )

        # --------------------------------------------------
        # Calculate line dimensions
        # --------------------------------------------------

        bbox = font.getbbox(line)

        text_width = (
            bbox[2] - bbox[0]
        )

        text_height = (
            bbox[3] - bbox[1]
        )

        padding = 35

        layer_width = (
            text_width + padding * 2
        )

        layer_height = (
            text_height + padding * 2
        )

        # --------------------------------------------------
        # Create transparent text layer
        # --------------------------------------------------

        text_layer = Image.new(
            "RGBA",
            (
                layer_width,
                layer_height,
            ),
            (0, 0, 0, 0),
        )

        layer_draw = ImageDraw.Draw(
            text_layer
        )

        alpha = rng.randint(
            190,
            245,
        )

        # Render the WHOLE line.
        #
        # This is important for Devanagari,
        # Modi and Sharada because rendering
        # individual characters can break
        # Unicode shaping and conjuncts.
        layer_draw.text(
            (
                padding - bbox[0],
                padding - bbox[1],
            ),
            line,
            font=font,
            fill=(
                ink_color[0],
                ink_color[1],
                ink_color[2],
                alpha,
            ),
        )

        # --------------------------------------------------
        # STEP 7: Handwriting variation
        # --------------------------------------------------

        text_layer = apply_handwriting_variation(
            text_layer,
            rng,
        )

        # --------------------------------------------------
        # STEP 8: Historical ink effects
        # --------------------------------------------------

        text_layer = apply_text_effects(
            text_layer,
            rng,
        )

        # --------------------------------------------------
        # STEP 9: Slight line rotation
        # --------------------------------------------------

        text_layer = text_layer.rotate(
            rotation,
            resample=Image.Resampling.BICUBIC,
            expand=True,
        )

        # --------------------------------------------------
        # STEP 10: Calculate final line position
        # --------------------------------------------------

        paste_x = (
            x_start + x_jitter
        )

        paste_y = (
            y + y_jitter
        )

        # Keep text inside left/top boundary
        if paste_x < margin:
            paste_x = margin

        if paste_y < margin:
            paste_y = margin

        # Keep text inside right boundary
        if (
            paste_x + text_layer.width
            > image_width - margin
        ):
            paste_x = (
                image_width
                - margin
                - text_layer.width
            )

        # Stop if next line would leave page
        if (
            paste_y + text_layer.height
            > image_height - margin
        ):
            break

        # --------------------------------------------------
        # STEP 11: Paste text onto manuscript
        # --------------------------------------------------

        image.paste(
            text_layer,
            (
                int(paste_x),
                int(paste_y),
            ),
            text_layer,
        )

        # --------------------------------------------------
        # STEP 12: Irregular line spacing
        # --------------------------------------------------

        spacing_variation = rng.randint(
            -3,
            5,
        )

        y += (
            font_size
            + line_spacing
            + spacing_variation
        )

    # --------------------------------------------------
    # STEP 13: Save rendered manuscript
    # --------------------------------------------------

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    image.save(output_path)

    print(
        f"✓ Rendered manuscript: "
        f"{output_path.name}"
    )