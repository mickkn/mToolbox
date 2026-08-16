"""
image2stl.py  –  Convert a grayscale (or colour) image to an STL heightmap.

Usage:
    python image2stl.py input.png output.stl
    python image2stl.py input.png output.stl --height 10 --base 1 --smooth 1

Arguments:
    input          Path to the source image (PNG, JPG, …)
    output         Path for the generated STL file
    --height       Maximum extrusion height in mm  (default: 10)
    --base         Solid base thickness in mm       (default: 1)
    --scale        XY scale – mm per pixel          (default: 0.1)
    --smooth       Gaussian blur radius (0 = off)   (default: 1)
    --invert       Invert heights (dark = tall)

Install dependencies:
    pip install Pillow numpy numpy-stl scipy
"""

from argparse import ArgumentParser
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from stl import mesh as stl_mesh


def image_to_heightmap(
    image_path: str,
    max_height: float = 10.0,
    base_height: float = 1.0,
    smooth_radius: float = 1.0,
    invert: bool = False,
) -> np.ndarray:
    img = Image.open(image_path).convert("L")          # grayscale
    arr = np.array(img, dtype=np.float32) / 255.0      # 0..1

    if invert:
        arr = 1.0 - arr

    if smooth_radius > 0:
        arr = gaussian_filter(arr, sigma=smooth_radius)

    heights = base_height + arr * max_height
    return heights


def heightmap_to_stl(heights: np.ndarray, scale_xy: float = 0.1) -> stl_mesh.Mesh:
    rows, cols = heights.shape
    # Each grid cell = 2 triangles on top + 4 side quads + bottom
    # Simpler approach: top surface only + flat base stitched together
    n_cells = (rows - 1) * (cols - 1)
    n_triangles = n_cells * 2 + n_cells * 8 + 2 * (rows - 1) * 2 + 2 * (cols - 1) * 2

    # Pre-build vertex grid
    x = np.arange(cols) * scale_xy
    y = np.arange(rows) * scale_xy
    xx, yy = np.meshgrid(x, y)
    zz = heights

    triangles = []

    # ---- top surface ------------------------------------------------
    for r in range(rows - 1):
        for c in range(cols - 1):
            v00 = (xx[r, c],   yy[r, c],   zz[r, c])
            v10 = (xx[r+1, c], yy[r+1, c], zz[r+1, c])
            v01 = (xx[r, c+1], yy[r, c+1], zz[r, c+1])
            v11 = (xx[r+1, c+1], yy[r+1, c+1], zz[r+1, c+1])
            triangles.append((v00, v10, v11))
            triangles.append((v00, v11, v01))

    # ---- bottom face ------------------------------------------------
    z0 = 0.0
    for r in range(rows - 1):
        for c in range(cols - 1):
            b00 = (xx[r, c],   yy[r, c],   z0)
            b10 = (xx[r+1, c], yy[r+1, c], z0)
            b01 = (xx[r, c+1], yy[r, c+1], z0)
            b11 = (xx[r+1, c+1], yy[r+1, c+1], z0)
            triangles.append((b00, b11, b10))   # reversed normal
            triangles.append((b00, b01, b11))

    # ---- side walls -------------------------------------------------
    def wall_quad(a_top, b_top, a_bot, b_bot):
        triangles.append((a_top, b_top, b_bot))
        triangles.append((a_top, b_bot, a_bot))

    # front (r=0)
    for c in range(cols - 1):
        wall_quad(
            (xx[0, c],   yy[0, c],   zz[0, c]),
            (xx[0, c+1], yy[0, c+1], zz[0, c+1]),
            (xx[0, c],   yy[0, c],   z0),
            (xx[0, c+1], yy[0, c+1], z0),
        )
    # back (r=rows-1)
    for c in range(cols - 1):
        wall_quad(
            (xx[-1, c+1], yy[-1, c+1], zz[-1, c+1]),
            (xx[-1, c],   yy[-1, c],   zz[-1, c]),
            (xx[-1, c+1], yy[-1, c+1], z0),
            (xx[-1, c],   yy[-1, c],   z0),
        )
    # left (c=0)
    for r in range(rows - 1):
        wall_quad(
            (xx[r+1, 0], yy[r+1, 0], zz[r+1, 0]),
            (xx[r, 0],   yy[r, 0],   zz[r, 0]),
            (xx[r+1, 0], yy[r+1, 0], z0),
            (xx[r, 0],   yy[r, 0],   z0),
        )
    # right (c=cols-1)
    for r in range(rows - 1):
        wall_quad(
            (xx[r, -1],   yy[r, -1],   zz[r, -1]),
            (xx[r+1, -1], yy[r+1, -1], zz[r+1, -1]),
            (xx[r, -1],   yy[r, -1],   z0),
            (xx[r+1, -1], yy[r+1, -1], z0),
        )

    # ---- build STL mesh ---------------------------------------------
    n = len(triangles)
    solid = stl_mesh.Mesh(np.zeros(n, dtype=stl_mesh.Mesh.dtype))
    for i, (v0, v1, v2) in enumerate(triangles):
        solid.vectors[i] = [v0, v1, v2]
    return solid


def main():
    parser = ArgumentParser(description="Convert an image to an STL heightmap.")
    parser.add_argument("input",  help="Source image (PNG, JPG, …)")
    parser.add_argument("output", nargs="?", default="output.stl", help="Destination STL file")
    parser.add_argument("--height",  type=float, default=10.0, help="Max extrusion height in mm (default: 10)")
    parser.add_argument("--base",    type=float, default=1.0,  help="Base thickness in mm (default: 1)")
    parser.add_argument("--scale",   type=float, default=0.1,  help="XY scale mm/pixel (default: 0.1)")
    parser.add_argument("--smooth",  type=float, default=1.0,  help="Gaussian blur radius, 0=off (default: 1)")
    parser.add_argument("--invert",  action="store_true",      help="Invert heights (dark pixels = tall)")
    args = parser.parse_args()

    print(f"Loading image: {args.input}")
    heights = image_to_heightmap(
        args.input,
        max_height=args.height,
        base_height=args.base,
        smooth_radius=args.smooth,
        invert=args.invert,
    )
    print(f"Image size: {heights.shape[1]}w × {heights.shape[0]}h pixels  →  "
          f"{heights.shape[1] * args.scale:.1f} × {heights.shape[0] * args.scale:.1f} mm")

    print("Building mesh…")
    solid = heightmap_to_stl(heights, scale_xy=args.scale)

    output = Path(args.output)
    solid.save(str(output))
    print(f"Saved STL to: {output.resolve()}")


if __name__ == "__main__":
    main()

