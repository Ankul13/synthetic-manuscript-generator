from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


def generate_paper_background(
    width=1600,
    height=1000,
    output_path="paper_background_test.png",
    seed=None
):
    """
    Generate an aged handmade-paper background.

    Components:
    - warm paper base
    - fine paper grain
    - low-frequency texture
    - random stains
    - darker edges
    """

    rng = np.random.default_rng(seed)

    # ------------------------------------------------
    # 1. BASE PAPER
    # ------------------------------------------------

    base_color = np.array(
        [222, 198, 158],
        dtype=np.float32
    )

    image = np.ones(
        (height, width, 3),
        dtype=np.float32
    ) * base_color

    # ------------------------------------------------
    # 2. FINE PAPER GRAIN
    # ------------------------------------------------

    fine_noise = rng.normal(
        0,
        7,
        (height, width, 1)
    )

    image += fine_noise

    # ------------------------------------------------
    # 3. LOW-FREQUENCY PAPER TEXTURE
    # ------------------------------------------------

    small_height = max(1, height // 20)
    small_width = max(1, width // 20)

    coarse_noise = rng.normal(
        0,
        20,
        (small_height, small_width)
    )

    coarse_noise = Image.fromarray(
        np.uint8(
            np.clip(
                coarse_noise + 128,
                0,
                255
            )
        )
    )

    coarse_noise = coarse_noise.resize(
        (width, height),
        Image.Resampling.BICUBIC
    )

    coarse_noise = coarse_noise.filter(
        ImageFilter.GaussianBlur(25)
    )

    coarse_array = (
        np.asarray(coarse_noise)
        .astype(np.float32)
        - 128
    )

    image += coarse_array[:, :, None]

    # ------------------------------------------------
    # 4. RANDOM AGING / STAINS
    # ------------------------------------------------

    stain_layer = Image.new(
        "L",
        (width, height),
        0
    )

    # IMPORTANT:
    # Convert to float32 so we can subtract
    # floating-point stain values safely.
    stain_pixels = np.asarray(
        stain_layer,
        dtype=np.float32
    ).copy()

    number_of_stains = rng.integers(
        20,
        45
    )

    yy, xx = np.ogrid[
        :height,
        :width
    ]

    for _ in range(number_of_stains):

        cx = rng.integers(
            0,
            width
        )

        cy = rng.integers(
            0,
            height
        )

        radius_x = rng.integers(
            max(10, width // 80),
            max(20, width // 12)
        )

        radius_y = rng.integers(
            max(10, height // 80),
            max(20, height // 10)
        )

        distance = (
            ((xx - cx) / radius_x) ** 2
            +
            ((yy - cy) / radius_y) ** 2
        )

        stain = np.exp(
            -distance * 2
        )

        strength = rng.uniform(
            10,
            35
        )

        stain_pixels -= (
            stain * strength
        )

    stain_pixels = np.clip(
        stain_pixels,
        0,
        255
    )

    stain_pixels = Image.fromarray(
        stain_pixels.astype(np.uint8)
    )

    stain_pixels = stain_pixels.filter(
        ImageFilter.GaussianBlur(8)
    )

    stain_array = (
        np.asarray(stain_pixels)
        .astype(np.float32)
    )

    stain_darkness = (
        255 - stain_array
    )

    image -= (
        stain_darkness[:, :, None] * 0.35
    )

    # ------------------------------------------------
    # 5. DARKER EDGES
    # ------------------------------------------------

    yy, xx = np.mgrid[
        0:height,
        0:width
    ]

    distance_from_edge = np.minimum.reduce(
        [
            xx,
            width - 1 - xx,
            yy,
            height - 1 - yy
        ]
    )

    edge_width = min(
        width,
        height
    ) * 0.15

    edge_factor = np.clip(
        1 - distance_from_edge / edge_width,
        0,
        1
    )

    edge_factor = edge_factor ** 2

    image -= (
        edge_factor[:, :, None] * 35
    )

    # ------------------------------------------------
    # 6. CLIP VALUES
    # ------------------------------------------------

    image = np.clip(
        image,
        0,
        255
    ).astype(np.uint8)

    # ------------------------------------------------
    # 7. SAVE IMAGE
    # ------------------------------------------------

    result = Image.fromarray(
        image,
        mode="RGB"
    )

    result.save(output_path)

    print(
        f"Background saved: {output_path}"
    )


if __name__ == "__main__":

    project_root = (
        Path(__file__).resolve().parent.parent
    )

    output_file = (
        project_root
        / "paper_background_test.png"
    )

    generate_paper_background(
        width=1600,
        height=1000,
        output_path=output_file,
        seed=42
    )