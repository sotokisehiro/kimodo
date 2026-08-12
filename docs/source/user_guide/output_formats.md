# Output Formats

## Converting Between Formats

To convert between the formats described below, see [Motion format conversion](motion_convert.md) (`kimodo_convert`).

## Kimodo NPZ Format

Generated motions are stored as NPZ files (one file per sample, e.g. `motion_00.npz`) containing:

- `posed_joints`: Global joint positions `[T, J, 3]`
- `global_rot_mats`: Global joint rotation matrices `[T, J, 3, 3]`
- `local_rot_mats`: Local (parent-relative) joint rotation matrices `[T, J, 3, 3]`
- `foot_contacts`: Foot contact labels [left heel, left toe, right heel, right toes] `[T, 4]`
- `smooth_root_pos`: Smoothed root representations outputted from the model `[T, 3]`
- `root_positions`: The (non-smoothed) trajectory of the actual root joint (e.g., pelvis) `[T, 3]`
- `global_root_heading`: The heading direction output from the model `[T, 2]`

Where:

- `T`: number of frames
- `J`: number of joints in the exported skeleton representation (`77` for SOMA NPZ exports, `34` for G1, `22` for SMPL-X)

If multiple samples are generated, files are saved with suffixes like `_00`, `_01`, etc.

For SOMA models, the exported NPZ uses the full **`somaskel77`** skeleton even though the model itself operates internally on the reduced **`somaskel30`** skeleton. This means the saved `posed_joints`, `global_rot_mats`, and `local_rot_mats` arrays are written in the 77-joint SOMA layout. Older 30-joint SOMA NPZ files may still exist and remain loadable for backward compatibility.

Also for SOMA models, the output motion is saved such that the rest pose (i.e. zero pose) is the standard T-pose that Kimodo uses internally. This differs from the default behavior of BVH export (see below), which uses a rest pose consistent with the BONES-SEED dataset format. The standard T-pose as a BVH file is also available [in the assets of the repo](https://github.com/nv-tlabs/kimodo/tree/main/kimodo/assets/skeletons/somaskel77).

## BVH Format for Kimodo-SOMA

When using a SOMA model and passing the `--bvh` flag to CLI generation, Kimodo also writes a BVH file alongside the NPZ output.

- BVH export is supported for **SOMA models only**
- the exported hierarchy uses the full **`somaskel77`** skeleton
- if the motion is still in internal `somaskel30` form, Kimodo converts it to `somaskel77` before writing the BVH
- the file stores root translation plus per-joint local rotations for the clip at the generated frame rate
- by default, the rest pose (i.e., zero pose) of the saved BVH file is consistent with the BONES-SEED dataset format. If you prefer a standard T-pose as the rest pose, pass in `--bvh_standard_tpose` when generating.

The exporter writes a standard plain-text BVH file and scales joint offsets and root motion from meters to centimeters (same format as the SEED dataset release). If multiple samples are generated, files are saved with suffixes like `_00`, `_01`, etc.

## MikuMikuDance VMD Format for Kimodo-SOMA

When using a SOMA model and passing `--vmd`, Kimodo writes a VMD 2 model-motion file alongside the NPZ output.

- VMD export supports SOMA 30- and 77-joint motions; SOMA30 is expanded before export.
- Motion is retargeted to conventional Japanese MMD humanoid bone names.
- VMD frame numbers use MMD's 30 fps timeline. Other source rates are resampled.
- Root motion is written to `センター`, relative to the first frame.
- Kimodo's right-handed Y-up coordinates are converted to MMD's left-handed Y-up coordinates.
- Leg motion is exported as FK and the `左足ＩＫ` and `右足ＩＫ` controls are disabled in the VMD.
- Facial morphs, camera, lighting, and self-shadow animation are not exported.

The default distance scale normalizes the SOMA character height to 20 MMD units. Use `--vmd-scale` when a target PMX model needs a different scale, and `--vmd-model-name` to set the model name embedded in the VMD header.

VMD motions depend on the target PMX model's bind pose and bone layout. Models with non-standard axes or missing standard Japanese bone names may require additional retargeting.

### Reference PMX model

For MMD validation, the repository includes `kimodo/assets/mmd/kimodo_reference.pmx`. It is a low-poly, T-pose mannequin whose proportions, coordinate conversion, model name (`Kimodo`), and Japanese bone names match the VMD exporter. PMX text fields use BOM-less UTF-16LE for compatibility with MikuMikuDance. Its left side is blue and its right side is red so mirrored motion is easy to identify.

To test an exported motion in MMD:

1. Load `kimodo_reference.pmx` as the model.
2. Load the generated `.vmd` as motion data.
3. Start playback at frame 0. The VMD disables both foot IK bones so the generated FK leg rotations are used.

The packaged model can be regenerated after skeleton or mapping changes with:

```bash
kimodo_make_mmd_reference
```

## CSV Format for Kimodo-G1

When using `Kimodo-G1` models and providing `--output` to CLI generation, the exporter writes MuJoCo `qpos`
data to a CSV file. Each row corresponds to a pose in the motion and contains 36 values:

- Root translation `[x, y, z]`
- Root rotation quaternion `[w, x, y, z]`
- 29 joint 1-DoF values (in G1 joint order)

The CSV uses the MuJoCo coordinate system (z-up, +x forward). If multiple samples are generated, files are saved with suffixes like `_00`, `_01`, etc.


## AMASS NPZ Format for Kimodo-SMPLX

When using the `Kimodo-SMPLX-RP` model and `--output` is specified to CLI generation, the exporter writes an
AMASS-style SMPL-X `.npz` file. Keys include:

- `trans`: Root translation `[T, 3]`
- `root_orient`: Root orientation axis-angle `[T, 3]`
- `pose_body`: Body pose axis-angle `[T, 63]` (21 joints x 3)
- `pose_hand`: Hand pose axis-angle `[T, 90]` (15 joints x 2 hands x 3)
- `pose_jaw`: Jaw pose axis-angle `[T, 3]`
- `pose_eye`: Eye pose axis-angle `[T, 6]`
- `betas`: Shape coefficients
- `num_betas`: Number of shape coefficients
- `gender`: `neutral`
- `surface_model_type`: `smplx`
- `mocap_frame_rate`: Frame rate (fps)
- `mocap_time_length`: Motion duration in seconds

The exporter converts from the Kimodo coordinate system (y-up, +z forward)
to AMASS coordinates (z-up, +y forward). If multiple samples are generated, files are saved with suffixes like `_00`, `_01`, etc.
