# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Export SOMA motions as MikuMikuDance VMD 2 model motions.

VMD stores transforms against named bones rather than embedding a skeleton.  This
module therefore targets the conventional Japanese MMD humanoid bone names and
retargets Kimodo's SOMA standard T-pose motion to that hierarchy.
"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import NamedTuple, Union

import torch

from kimodo.geometry import matrix_to_quaternion, quaternion_to_matrix

VMD_FPS = 30.0
VMD_HEADER = b"Vocaloid Motion Data 0002".ljust(30, b"\0")

# MMD's default linear Bezier controls (20, 20) -> (107, 107), in the
# format's unusual overlapping 64-byte layout.
LINEAR_INTERPOLATION = bytes(
    [
        20, 20, 0, 0, 20, 20, 20, 20, 107, 107, 107, 107, 107, 107, 107, 107,
        20, 20, 20, 20, 20, 20, 20, 107, 107, 107, 107, 107, 107, 107, 107, 0,
        20, 20, 20, 20, 20, 20, 107, 107, 107, 107, 107, 107, 107, 107, 0, 0,
        20, 20, 20, 20, 20, 107, 107, 107, 107, 107, 107, 107, 107, 0, 0, 0,
    ]
)


class _BoneTarget(NamedTuple):
    name: str
    source: str
    parent_source: str | None


# Each target local rotation is derived from the global rotations of ``source``
# and ``parent_source``.  That composes any unmapped SOMA joints between them.
_BODY_TARGETS = (
    _BoneTarget("センター", "Hips", None),
    _BoneTarget("下半身", "Hips", "Hips"),
    _BoneTarget("上半身", "Spine1", "Hips"),
    _BoneTarget("上半身2", "Chest", "Spine1"),
    _BoneTarget("首", "Neck2", "Chest"),
    _BoneTarget("頭", "Head", "Neck2"),
    _BoneTarget("左肩", "LeftShoulder", "Chest"),
    _BoneTarget("左腕", "LeftArm", "LeftShoulder"),
    _BoneTarget("左ひじ", "LeftForeArm", "LeftArm"),
    _BoneTarget("左手首", "LeftHand", "LeftForeArm"),
    _BoneTarget("右肩", "RightShoulder", "Chest"),
    _BoneTarget("右腕", "RightArm", "RightShoulder"),
    _BoneTarget("右ひじ", "RightForeArm", "RightArm"),
    _BoneTarget("右手首", "RightHand", "RightForeArm"),
    _BoneTarget("左足", "LeftLeg", "Hips"),
    _BoneTarget("左ひざ", "LeftShin", "LeftLeg"),
    _BoneTarget("左足首", "LeftFoot", "LeftShin"),
    _BoneTarget("右足", "RightLeg", "Hips"),
    _BoneTarget("右ひざ", "RightShin", "RightLeg"),
    _BoneTarget("右足首", "RightFoot", "RightShin"),
)


def _finger_targets(side_jp: str, side_en: str) -> tuple[_BoneTarget, ...]:
    result = []
    chains = (
        ("親指", "Thumb", ("０", "１", "２")),
        ("人指", "Index", ("１", "２", "３")),
        ("中指", "Middle", ("１", "２", "３")),
        ("薬指", "Ring", ("１", "２", "３")),
        ("小指", "Pinky", ("１", "２", "３")),
    )
    for mmd_stem, soma_stem, suffixes in chains:
        parent = f"{side_en}Hand"
        for index, suffix in enumerate(suffixes, start=1):
            source = f"{side_en}Hand{soma_stem}{index}"
            result.append(_BoneTarget(f"{side_jp}{mmd_stem}{suffix}", source, parent))
            parent = source
    return tuple(result)


MMD_BONE_TARGETS = _BODY_TARGETS + _finger_targets("左", "Left") + _finger_targets("右", "Right")


def _fixed_cp932(text: str, size: int) -> bytes:
    """Encode without splitting a multibyte character and NUL-pad to ``size``."""
    encoded = bytearray()
    for char in text:
        chunk = char.encode("cp932")
        if len(encoded) + len(chunk) > size:
            break
        encoded.extend(chunk)
    return bytes(encoded).ljust(size, b"\0")


def _coerce_motion(local_rot_mats: torch.Tensor, root_positions: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    if local_rot_mats.ndim == 5:
        if local_rot_mats.shape[0] != 1:
            raise ValueError("VMD export supports one motion clip at a time.")
        local_rot_mats = local_rot_mats[0]
    if root_positions.ndim == 3:
        if root_positions.shape[0] != 1:
            raise ValueError("VMD export supports one root trajectory at a time.")
        root_positions = root_positions[0]
    if local_rot_mats.ndim != 4 or local_rot_mats.shape[-2:] != (3, 3):
        raise ValueError(f"local_rot_mats must be (T,J,3,3); got {tuple(local_rot_mats.shape)}")
    if root_positions.ndim != 2 or root_positions.shape[-1] != 3:
        raise ValueError(f"root_positions must be (T,3); got {tuple(root_positions.shape)}")
    if local_rot_mats.shape[0] != root_positions.shape[0] or local_rot_mats.shape[0] == 0:
        raise ValueError("Rotation and root arrays must have the same non-zero frame count.")
    if not torch.isfinite(local_rot_mats).all() or not torch.isfinite(root_positions).all():
        raise ValueError("VMD motion contains NaN or infinite values.")
    return local_rot_mats, root_positions


def _slerp(q0: torch.Tensor, q1: torch.Tensor, amount: torch.Tensor) -> torch.Tensor:
    dot = (q0 * q1).sum(dim=-1, keepdim=True)
    q1 = torch.where(dot < 0, -q1, q1)
    dot = dot.abs().clamp(max=1.0)
    theta = torch.acos(dot)
    sin_theta = torch.sin(theta)
    linear = sin_theta.abs() < 1e-6
    a = torch.sin((1.0 - amount) * theta) / sin_theta.clamp(min=1e-8)
    b = torch.sin(amount * theta) / sin_theta.clamp(min=1e-8)
    q = torch.where(linear, (1.0 - amount) * q0 + amount * q1, a * q0 + b * q1)
    return q / torch.linalg.norm(q, dim=-1, keepdim=True).clamp(min=1e-8)


def _resample_to_vmd_fps(
    local_rot_mats: torch.Tensor, root_positions: torch.Tensor, source_fps: float
) -> tuple[torch.Tensor, torch.Tensor]:
    if source_fps <= 0:
        raise ValueError(f"fps must be positive; got {source_fps}")
    if abs(float(source_fps) - VMD_FPS) < 1e-6:
        return local_rot_mats, root_positions

    count = local_rot_mats.shape[0]
    output_count = max(1, int(round((count - 1) * VMD_FPS / float(source_fps))) + 1)
    source_t = torch.arange(output_count, device=local_rot_mats.device, dtype=local_rot_mats.dtype)
    source_t = (source_t / VMD_FPS * float(source_fps)).clamp(max=count - 1)
    i0 = source_t.floor().long()
    i1 = (i0 + 1).clamp(max=count - 1)
    alpha = (source_t - i0.to(source_t.dtype)).unsqueeze(-1)
    roots = torch.lerp(root_positions[i0], root_positions[i1], alpha)

    quats = matrix_to_quaternion(local_rot_mats)
    rotations = quaternion_to_matrix(_slerp(quats[i0], quats[i1], alpha.unsqueeze(-1)))
    return rotations, roots


def _global_rotations(local_rot_mats: torch.Tensor, parents: torch.Tensor) -> torch.Tensor:
    result = torch.empty_like(local_rot_mats)
    for joint, parent in enumerate(parents.tolist()):
        if parent < 0:
            result[:, joint] = local_rot_mats[:, joint]
        else:
            result[:, joint] = result[:, parent] @ local_rot_mats[:, joint]
    return result


def _default_mmd_scale(skeleton) -> float:
    neutral = skeleton.neutral_joints.detach()
    height = float((neutral[:, 1].max() - neutral[:, 1].min()).abs().cpu())
    if height < 1e-6:
        raise ValueError("Cannot infer VMD scale from a zero-height skeleton.")
    return 20.0 / height


def motion_to_vmd_bytes(
    local_rot_mats: torch.Tensor,
    root_positions: torch.Tensor,
    *,
    skeleton,
    fps: float,
    model_name: str = "Kimodo",
    scale: float | None = None,
) -> bytes:
    """Return a VMD 2 body motion targeting standard Japanese MMD bones.

    Kimodo is right-handed, Y-up, +Z-forward.  MMD is treated as left-handed,
    Y-up, so Z is reflected.  Root translation is made relative to the first
    frame because VMD bone positions are offsets from the target model's bind
    pose.  Foot IK is explicitly disabled; leg motion is exported as FK.
    """
    local_rot_mats, root_positions = _coerce_motion(local_rot_mats, root_positions)
    if "somaskel" not in str(skeleton.name):
        raise ValueError(f"VMD export currently supports SOMA skeletons only; got {skeleton.name!r}.")

    if int(local_rot_mats.shape[1]) == 30:
        local_rot_mats = skeleton.to_SOMASkeleton77(local_rot_mats)
        skeleton = skeleton.somaskel77.to(local_rot_mats.device)
    elif int(local_rot_mats.shape[1]) != 77:
        raise ValueError(f"VMD export requires 30 or 77 SOMA joints; got J={local_rot_mats.shape[1]}.")

    local_rot_mats, root_positions = _resample_to_vmd_fps(local_rot_mats, root_positions, float(fps))
    global_rots = _global_rotations(local_rot_mats, skeleton.joint_parents)

    # Reflection changes handedness while retaining proper rotation matrices.
    basis = torch.diag(torch.tensor([1.0, 1.0, -1.0], device=global_rots.device, dtype=global_rots.dtype))
    global_rots = basis @ global_rots @ basis
    root_delta = (root_positions - root_positions[0]) @ basis
    effective_scale = _default_mmd_scale(skeleton) if scale is None else float(scale)
    if effective_scale <= 0:
        raise ValueError(f"VMD scale must be positive; got {effective_scale}.")
    root_delta = root_delta * effective_scale

    index = skeleton.bone_index
    frames: list[bytes] = []
    identity = torch.eye(3, device=global_rots.device, dtype=global_rots.dtype)
    for target in MMD_BONE_TARGETS:
        if target.source not in index or (target.parent_source is not None and target.parent_source not in index):
            continue
        current = global_rots[:, index[target.source]]
        if target.parent_source is None:
            parent = identity.expand_as(current)
        else:
            parent = global_rots[:, index[target.parent_source]]
        local = parent.transpose(-1, -2) @ current
        quats_wxyz = matrix_to_quaternion(local)
        quats_wxyz = quats_wxyz / torch.linalg.norm(quats_wxyz, dim=-1, keepdim=True).clamp(min=1e-8)
        for frame_no in range(1, len(quats_wxyz)):
            if torch.dot(quats_wxyz[frame_no - 1], quats_wxyz[frame_no]) < 0:
                quats_wxyz[frame_no] = -quats_wxyz[frame_no]
        for frame_no in range(local.shape[0]):
            position = root_delta[frame_no] if target.name == "センター" else torch.zeros_like(root_delta[0])
            qw, qx, qy, qz = (float(x) for x in quats_wxyz[frame_no].detach().cpu())
            frames.append(
                struct.pack(
                    "<15sI3f4f64s",
                    _fixed_cp932(target.name, 15),
                    frame_no,
                    *(float(x) for x in position.detach().cpu()),
                    qx,
                    qy,
                    qz,
                    qw,
                    LINEAR_INTERPOLATION,
                )
            )

    output = bytearray(VMD_HEADER)
    output.extend(_fixed_cp932(model_name, 20))
    output.extend(struct.pack("<I", len(frames)))
    for frame in frames:
        output.extend(frame)
    output.extend(struct.pack("<IIIII", 0, 0, 0, 0, 1))  # morph, camera, light, shadow, IK-display
    output.extend(struct.pack("<IBI", 0, 1, 2))
    output.extend(_fixed_cp932("左足ＩＫ", 20))
    output.extend(struct.pack("<B", 0))
    output.extend(_fixed_cp932("右足ＩＫ", 20))
    output.extend(struct.pack("<B", 0))
    return bytes(output)


def save_motion_vmd(
    path: Union[str, Path],
    local_rot_mats: torch.Tensor,
    root_positions: torch.Tensor,
    *,
    skeleton,
    fps: float,
    model_name: str = "Kimodo",
    scale: float | None = None,
) -> None:
    """Write a single SOMA motion clip to a VMD file."""
    Path(path).write_bytes(
        motion_to_vmd_bytes(
            local_rot_mats,
            root_positions,
            skeleton=skeleton,
            fps=fps,
            model_name=model_name,
            scale=scale,
        )
    )
