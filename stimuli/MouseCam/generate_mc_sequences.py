import os
from pathlib import Path
import numpy as np
from PIL import Image
import random


# -----------------------------
# Helper Functions
# -----------------------------
def load_montage(image_path, frame_width, frame_height, color_sequence="BGR"):
    """
    Load a montage image and split it into individual frames.
    The coordinate system is defined such that (0,0) is at the bottom-left.

    Args:
        image_path: Path to the montage image file.
        frame_width: Width of each frame in pixels.
        frame_height: Height of each frame in pixels.
        color_sequence: 'BGR' or 'RGB' indicating the color channel order.

    Returns:
        frames: NumPy array of shape (num_frames, height, width, 3)
    """
    img = Image.open(image_path).convert("RGB")
    if color_sequence == "BGR":
        r, g, b = img.split()
        img = Image.merge("RGB", (b, g, r))
    elif color_sequence != "RGB":
        raise ValueError("color_sequence must be 'BGR' or 'RGB'")
    img_np = np.array(img)

    total_height, total_width, _ = img_np.shape
    cols = total_width // frame_width
    rows = total_height // frame_height

    # Vectorized extraction: reshape into (rows, H, cols, W, C), flip row order for
    # bottom-left origin, transpose to (rows, cols, H, W, C), flatten to (N, H, W, C).
    grid = img_np[:rows * frame_height, :cols * frame_width, :]
    grid = grid.reshape(rows, frame_height, cols, frame_width, 3)
    grid = grid[::-1]  # row 0 = bottom of image
    frames = grid.transpose(0, 2, 1, 3, 4).reshape(-1, frame_height, frame_width, 3)
    return np.ascontiguousarray(frames, dtype=np.uint8)


def _load_mc_data(p, color_sequence):
    """Load test frames, train frames, and sequence indices from disk."""
    indices = np.loadtxt(p["IndexName"])
    test_frames = load_montage(
        p["movName_Test"], p["frame_width"], p["frame_height"], color_sequence=color_sequence
    )
    train_frames = load_montage(
        p["movName_Train"], p["frame_width"], p["frame_height"], color_sequence=color_sequence
    )
    return test_frames, train_frames, indices


def downsample_spatial(frames, factor):
    """Block-average spatial downsampling by the given integer factor."""
    T, H, W, C = frames.shape
    H_ds = H // factor
    W_ds = W // factor
    frames_crop = frames[:, :H_ds * factor, :W_ds * factor, :]
    frames_ds = frames_crop.reshape(T, H_ds, factor, W_ds, factor, C)
    return np.round(frames_ds.mean(axis=(2, 4))).astype(np.uint8)


def build_frame_indices(test_frames, train_frames, indices, sequence_column):
    """
    Build a 1D array of frame indices into the concatenated [test_frames, train_frames] reference.

    Reconstruction: reference[frame_indices] reproduces the full movie.
    The reference is structured as np.concatenate([test_frames, train_frames], axis=0),
    so test frame k maps to index k and train frame k maps to index n_test_frames + k.
    """
    nFr_Test = test_frames.shape[0]
    nFr_Sequ = int(5.0 * 30.0)
    nFr_Train = train_frames.shape[0]
    nSeqs_Train = nFr_Train // nFr_Sequ
    half = nSeqs_Train // 2

    test_idx = np.arange(nFr_Test, dtype=np.int32)

    def train_block_idx(row_start, row_end):
        idx = np.empty((row_end - row_start) * nFr_Sequ, dtype=np.int32)
        for k, iF in enumerate(range(row_start, row_end)):
            snippet = int(indices[iF][sequence_column])
            offset = nFr_Test + snippet * nFr_Sequ
            idx[k * nFr_Sequ:(k + 1) * nFr_Sequ] = np.arange(offset, offset + nFr_Sequ)
        return idx

    return np.concatenate([
        test_idx,
        train_block_idx(0, half),
        test_idx,
        train_block_idx(half, 2 * half),
        test_idx,
    ])


def build_movie(test_frames, train_frames, indices, sequence_column=None, verbose=False):
    """
    Build the full stimulus sequence following the logic of the original QDSpy script.

    Args:
        test_frames: NumPy array of shape (nFr_Test, height, width, 3).
        train_frames: NumPy array of shape (nFr_Train, height, width, 3).
        indices: 2-D NumPy array loaded from RandomSequences.txt.
        sequence_column: Column index to use (None picks randomly).
        verbose: Print debug info.

    Returns:
        movie: NumPy array of shape (total_frames, height, width, 3)
        sequence_column: The column that was used.
    """
    num_columns = indices.shape[1]
    if sequence_column is None:
        sequence_column = random.randint(0, num_columns - 1)

    nFr_Test = test_frames.shape[0]
    nFr_Train = train_frames.shape[0]
    nFr_Sequ = int(5.0 * 30.0)  # durSnippet_s * FrameRateMovie = 150
    nSeqs_Train = nFr_Train // nFr_Sequ
    half = nSeqs_Train // 2

    if verbose:
        print(
            f"Test frames: {nFr_Test}, Train frames: {nFr_Train}\n"
            f"Train sequences: {nSeqs_Train}, Frames per sequence: {nFr_Sequ}"
        )

    height, width = test_frames.shape[1], test_frames.shape[2]
    total_frames = 3 * nFr_Test + 2 * half * nFr_Sequ
    movie = np.zeros((total_frames, height, width, 3), dtype=np.uint8)
    t = 0

    def insert_test_block():
        nonlocal t
        movie[t : t + nFr_Test] = test_frames
        t += nFr_Test

    # -----------------------------
    # Test Set #1
    # -----------------------------
    insert_test_block()

    # -----------------------------
    # First half of training set
    # -----------------------------
    for iF in range(half):
        fs = int(indices[iF][sequence_column]) * nFr_Sequ
        movie[t : t + nFr_Sequ] = train_frames[fs : fs + nFr_Sequ]
        t += nFr_Sequ

    # -----------------------------
    # Test Set #2
    # -----------------------------
    insert_test_block()

    # -----------------------------
    # Second half of training set
    # -----------------------------
    for iF in range(half):
        a = iF + half
        fs = int(indices[a][sequence_column]) * nFr_Sequ
        movie[t : t + nFr_Sequ] = train_frames[fs : fs + nFr_Sequ]
        t += nFr_Sequ

    # -----------------------------
    # Test Set #3
    # -----------------------------
    insert_test_block()

    return movie, sequence_column


_DEFAULT_QDSPY_PATH = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), "QDSpy", "all_movie_files"
)
_DEFAULT_OUTDIR = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), "output_sequences"
)


def create_mc_array_v1(
    sequence_column,
    side="right",
    qdspy_path=_DEFAULT_QDSPY_PATH,
):
    create_mc_array(
        sequence_column=sequence_column,
        train_file=f"train_images_{side}.jpg",
        test_file=f"test_images_rand_{side}.jpg",
        frame_height=56,
        frame_width=56,
        color_sequence="BGR",
        qdspy_path=qdspy_path,
        outfile=f"MC1_{side}.npz",
    )


def create_mc_array_v2(
    sequence_column,
    side="right",
    qdspy_path=_DEFAULT_QDSPY_PATH,
):
    train_file = "MC2_train_rgb2_72x64_right.jpg" if side == "right" else "MC2_train_rgb_72x64_left.jpg"
    create_mc_array(
        sequence_column=sequence_column,
        train_file=train_file,
        test_file=f"MC2_test_rgb_72x64_{side}.jpg",
        frame_height=72,
        frame_width=64,
        color_sequence="RGB",
        qdspy_path=qdspy_path,
        outfile=f"MC2_{sequence_column}_{side}.npz",
    )


def create_mc_array_v2_new(
    sequence_column,
    side="right",
    qdspy_path=_DEFAULT_QDSPY_PATH,
):
    create_mc_array(
        sequence_column=sequence_column,
        train_file=f"MC2_train_rgb2_64x72_{side}-new.jpg",
        test_file=f"MC2_test_rgb_64x72_{side}-new.jpg",
        frame_height=64,
        frame_width=72,
        color_sequence="RGB",
        qdspy_path=qdspy_path,
        outfile=f"MC2_{sequence_column}_{side}.npz",
    )


def create_mc_array_v3(
    sequence_column,
    side="right",
    qdspy_path=_DEFAULT_QDSPY_PATH,
):
    create_mc_array(
        sequence_column=sequence_column,
        train_file=f"MC3_train_rgb_64x72_{side}.jpg",
        test_file=f"MC3_test_rgb_64x72_{side}.jpg",
        frame_height=64,
        frame_width=72,
        color_sequence="RGB",
        qdspy_path=qdspy_path,
        outfile=f"MC3_{sequence_column}_{side}.npz",
    )


def create_mc_array(
    sequence_column: int,
    color_sequence: str,
    train_file: str | Path,
    test_file: str | Path,
    frame_width: int,
    frame_height: int,
    outfile: str,
    qdspy_path: str = _DEFAULT_QDSPY_PATH,
    outdir: str = _DEFAULT_OUTDIR,
    verbose: bool = False,
    add_movie: bool = False,
    test_frames: np.ndarray | None = None,
    train_frames: np.ndarray | None = None,
    indices: np.ndarray | None = None,
):
    """
    Generate one stimulus sequence and save it as a compressed .npz.

    The file stores a frame_indices array (int32) that indexes into the corresponding
    reference file (see create_mc_reference). Reconstruct the full movie with:
        reference = np.load("MCx_ref_side.npz")["stimulus"]
        movie = reference[np.load(outfile)["frame_indices"]]

    If add_movie=True, the reconstructed movie is also stored as 'stimulus' in the
    file itself, making it self-contained without needing to load the reference.

    Pass test_frames, train_frames, and indices to reuse already-loaded data
    and avoid redundant file I/O across repeated calls with different sequence_column.
    """
    if verbose:
        print("QDSpy path:", os.path.abspath(qdspy_path))

    assert os.path.exists(qdspy_path), f"QDSpy path does not exist: {qdspy_path}"

    if test_frames is None or train_frames is None or indices is None:
        p = {
            "movName_Test": os.path.join(qdspy_path, test_file),
            "movName_Train": os.path.join(qdspy_path, train_file),
            "IndexName": os.path.join(qdspy_path, "RandomSequences.txt"),
            "frame_width": frame_width,
            "frame_height": frame_height,
        }
        test_frames, train_frames, indices = _load_mc_data(p, color_sequence)

    frame_indices = build_frame_indices(test_frames, train_frames, indices, sequence_column)
    is_test_set = frame_indices < test_frames.shape[0]

    out_path = os.path.join(outdir, outfile)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    framerate = 30.0
    n_frames = frame_indices.shape[0]
    time_mc = np.arange(n_frames) / framerate

    trigger_dt = 5.0
    trigger_mc = np.zeros(n_frames, dtype=bool)
    trigger_mc[::int(np.round(framerate * trigger_dt))] = True

    if add_movie:
        reference = np.concatenate([test_frames, train_frames], axis=0)
        np.savez_compressed(
            out_path,
            frame_indices=frame_indices,
            is_test_set=is_test_set,
            stimulus=reference[frame_indices],
            time=time_mc.astype(np.float32),
            trigger=trigger_mc,
            framerate=np.float32(framerate),
        )
    else:
        np.savez_compressed(
            out_path,
            frame_indices=frame_indices,
            is_test_set=is_test_set,
            time=time_mc.astype(np.float32),
            trigger=trigger_mc,
            framerate=np.float32(framerate),
        )


# Version configs for the main loop
_VERSION_CONFIGS: dict[str, dict] = {
    "v1": {
        "frame_height": 56, "frame_width": 56, "color_sequence": "BGR",
        "train_file": lambda side: f"train_images_{side}.jpg",
        "test_file":  lambda side: f"test_images_rand_{side}.jpg",
        "outfile":    lambda col, side: f"MC1_seq{col}_{side}.npz",
        "ref_outfile": lambda side: f"MC1_ref_{side}.npz",
    },
    "v2": {
        "frame_height": 72, "frame_width": 64, "color_sequence": "RGB",
        "train_file": lambda side: "MC2_train_rgb2_72x64_right.jpg" if side == "right" else "MC2_train_rgb_72x64_left.jpg",
        "test_file":  lambda side: f"MC2_test_rgb_72x64_{side}.jpg",
        "outfile":    lambda col, side: f"MC2_seq{col}_{side}.npz",
        "ref_outfile": lambda side: f"MC2_ref_{side}.npz",
    },
    "v2_new": {
        "frame_height": 64, "frame_width": 72, "color_sequence": "RGB",
        "train_file": lambda side: f"MC2_train_rgb2_64x72_{side}-new.jpg",
        "test_file":  lambda side: f"MC2_test_rgb_64x72_{side}-new.jpg",
        "outfile":    lambda col, side: f"MC2new_seq{col}_{side}.npz",
        "ref_outfile": lambda side: f"MC2new_ref_{side}.npz",
    },
    "v3": {
        "frame_height": 64, "frame_width": 72, "color_sequence": "RGB",
        "train_file": lambda side: f"MC3_train_rgb_64x72_{side}.jpg",
        "test_file":  lambda side: f"MC3_test_rgb_64x72_{side}.jpg",
        "outfile":    lambda col, side: f"MC3_seq{col}_{side}.npz",
        "ref_outfile": lambda side: f"MC3_ref_{side}.npz",
    },
}


def create_mc_reference(
    version_key,
    side : str,
    setup_id : int,
    qdspy_path=_DEFAULT_QDSPY_PATH,
    outdir=_DEFAULT_OUTDIR,
    downsample=1,
    pixel_size_original=12.5,
    overwrite=False,
):
    """
    Create a reference stimulus file for the given version and side.

    The reference contains all unique frames — test frames followed by train frames —
    at both original and spatially downsampled resolution. Individual sequence files
    store a frame_indices array that indexes into this reference to reconstruct
    the full movie via reference[frame_indices].
    """
    cfg = _VERSION_CONFIGS[version_key]
    outfile = cfg["ref_outfile"](side)
    out_path = os.path.join(outdir, outfile)

    if os.path.exists(out_path) and not overwrite:
        print(f"Reference file already exists, skipping: {outfile}")
        return

    p = {
        "movName_Test":  os.path.join(qdspy_path, cfg["test_file"](side)),
        "movName_Train": os.path.join(qdspy_path, cfg["train_file"](side)),
        "IndexName":     os.path.join(qdspy_path, "RandomSequences.txt"),
        "frame_width":   cfg["frame_width"],
        "frame_height":  cfg["frame_height"],
    }
    test_frames, train_frames, _ = _load_mc_data(p, cfg["color_sequence"])

    reference = np.concatenate([test_frames, train_frames], axis=0)
    assert np.all(reference.astype(np.uint8) == reference)
    reference = reference.astype(np.uint8)
    if downsample > 1:
        reference = downsample_spatial(reference, downsample)

    os.makedirs(outdir, exist_ok=True)

    if setup_id in [1, 2]:
        reference = np.flip(np.rot90(reference, k=1, axes=(1, 2)), axis=1)
    elif setup_id == 3:
        reference = np.rot90(reference, k=1, axes=(1, 2))

    # Set red channel to zero, because there is not red LED in the setup
    reference[..., 0] = 0

    np.savez_compressed(
        out_path,
        stimulus=reference,
        n_test_frames=np.int32(test_frames.shape[0]),
        framerate=np.float32(30.0),
        pixel_size=np.float32(pixel_size_original * downsample),
        pixel_size_original=np.float32(pixel_size_original),
    )
    print(f"Saved reference: {outfile}  "
          f"({test_frames.shape=}, {train_frames.shape=})")


def main(versions=("v1", "v2", "v2_new", "v3"), overwrite=False, downsample=1):
    # Create one reference file per (version, side) — 8 total
    for v in versions:
        if v == "v1":
            setup_id = 3
        else:
            setup_id = 1

        for side in ["right", "left"]:
            create_mc_reference(
                version_key=v,
                side=side,
                setup_id=setup_id,
                downsample=downsample,
                overwrite=overwrite,
            )

    # Create individual sequence files (frame_indices only, no pixel data)
    for v in versions:
        cfg = _VERSION_CONFIGS[v]

        if v == "v1":
            setup_id = 3
        else:
            setup_id = 1

        for side in ["right", "left"]:
            train_file: str = cfg["train_file"](side)
            test_file: str = cfg["test_file"](side)
            # Load montages and index file once per (version, side)
            p = {
                "movName_Train": os.path.join(_DEFAULT_QDSPY_PATH, train_file),
                "movName_Test":  os.path.join(_DEFAULT_QDSPY_PATH, test_file),
                "IndexName":     os.path.join(_DEFAULT_QDSPY_PATH, "RandomSequences.txt"),
                "frame_width":   cfg["frame_width"],
                "frame_height":  cfg["frame_height"],
            }
            test_frames, train_frames, indices = _load_mc_data(p, cfg["color_sequence"])

            for i in range(20):
                outfile = cfg["outfile"](i, side)
                outpath = os.path.join(_DEFAULT_OUTDIR, outfile)

                if os.path.exists(outpath) and not overwrite:
                    print(f"File already exists, skipping: {outfile}")
                    continue

                print(f"Creating MC {v} sequence for side={side}, sequence_column={i}")
                create_mc_array(
                    sequence_column=i,
                    color_sequence=cfg["color_sequence"],
                    train_file=train_file,
                    test_file=test_file,
                    frame_width=cfg["frame_width"],
                    frame_height=cfg["frame_height"],
                    qdspy_path=_DEFAULT_QDSPY_PATH,
                    outdir=_DEFAULT_OUTDIR,
                    outfile=outfile,
                    test_frames=test_frames,
                    train_frames=train_frames,
                    indices=indices,
                )

if __name__ == "__main__":
    main(versions=("v1", "v2", "v2_new", "v3"), overwrite=False)
    
