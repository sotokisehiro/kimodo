# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import struct

import torch

from kimodo.exports.motion_formats import infer_target_format_from_path
from kimodo.exports.vmd import (
    LINEAR_INTERPOLATION,
    MMD_BONE_TARGETS,
    VMD_HEADER,
    _fixed_cp932,
    motion_to_vmd_bytes,
)


class _FakeSoma77:
    name = "somaskel77-test"

    def __init__(self):
        names = []
        for target in MMD_BONE_TARGETS:
            for name in (target.source, target.parent_source):
                if name is not None and name not in names:
                    names.append(name)
        while len(names) < 77:
            names.append(f"Unused{len(names)}")
        self.bone_order_names = names
        self.bone_index = {name: index for index, name in enumerate(names)}
        self.joint_parents = torch.full((77,), -1, dtype=torch.long)
        self.neutral_joints = torch.zeros((77, 3), dtype=torch.float32)
        self.neutral_joints[1, 1] = 2.0


def _read_bone_frames(data: bytes):
    assert data[:30] == VMD_HEADER
    count = struct.unpack_from("<I", data, 50)[0]
    frames = []
    offset = 54
    record = struct.Struct("<15sI3f4f64s")
    for _ in range(count):
        frames.append(record.unpack_from(data, offset))
        offset += record.size
    return frames, offset


def test_vmd_binary_layout_and_root_coordinate_conversion():
    skeleton = _FakeSoma77()
    rotations = torch.eye(3).repeat(2, 77, 1, 1)
    roots = torch.tensor([[1.0, 2.0, 3.0], [2.0, 4.0, 6.0]])

    data = motion_to_vmd_bytes(rotations, roots, skeleton=skeleton, fps=30.0, scale=10.0)
    frames, offset = _read_bone_frames(data)

    assert len(LINEAR_INTERPOLATION) == 64
    assert len(frames) == len(MMD_BONE_TARGETS) * 2
    center = [frame for frame in frames if frame[0].rstrip(b"\0").decode("cp932") == "センター"]
    assert center[0][1] == 0
    assert all(abs(a - b) < 1e-5 for a, b in zip(center[0][2:5], (0.0, 0.0, 0.0)))
    assert center[1][1] == 1
    assert all(abs(a - b) < 1e-5 for a, b in zip(center[1][2:5], (10.0, 20.0, -30.0)))
    assert all(abs(a - b) < 1e-5 for a, b in zip(center[1][5:9], (0.0, 0.0, 0.0, 1.0)))
    assert center[1][9] == LINEAR_INTERPOLATION

    assert struct.unpack_from("<IIIII", data, offset) == (0, 0, 0, 0, 1)
    offset += 20
    frame_no, visible, ik_count = struct.unpack_from("<IBI", data, offset)
    assert (frame_no, visible, ik_count) == (0, 1, 2)
    offset += 9
    left_name = data[offset : offset + 20].rstrip(b"\0").decode("cp932")
    left_enabled = data[offset + 20]
    offset += 21
    right_name = data[offset : offset + 20].rstrip(b"\0").decode("cp932")
    right_enabled = data[offset + 20]
    assert (left_name, left_enabled, right_name, right_enabled) == ("左足ＩＫ", 0, "右足ＩＫ", 0)


def test_vmd_reflects_rotation_into_mmd_handedness():
    skeleton = _FakeSoma77()
    rotations = torch.eye(3).repeat(1, 77, 1, 1)
    rotations[0, skeleton.bone_index["Hips"]] = torch.tensor(
        [[0.0, 0.0, 1.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]]
    )
    frames, _ = _read_bone_frames(
        motion_to_vmd_bytes(rotations, torch.zeros((1, 3)), skeleton=skeleton, fps=30.0, scale=1.0)
    )
    center = next(frame for frame in frames if frame[0].rstrip(b"\0").decode("cp932") == "センター")
    qx, qy, qz, qw = center[5:9]
    assert abs(qx) < 1e-5 and abs(qz) < 1e-5
    assert abs(qy + 2**-0.5) < 1e-5
    assert abs(qw - 2**-0.5) < 1e-5


def test_vmd_resamples_source_timeline_to_30fps():
    skeleton = _FakeSoma77()
    rotations = torch.eye(3).repeat(3, 77, 1, 1)
    roots = torch.zeros((3, 3))
    frames, _ = _read_bone_frames(
        motion_to_vmd_bytes(rotations, roots, skeleton=skeleton, fps=60.0, scale=1.0)
    )
    center_frames = [frame[1] for frame in frames if frame[0].rstrip(b"\0").decode("cp932") == "センター"]
    assert center_frames == [0, 1]


def test_cp932_fixed_field_does_not_split_multibyte_character():
    encoded = _fixed_cp932("あ" * 20, 15)
    assert len(encoded) == 15
    assert encoded.rstrip(b"\0").decode("cp932") == "あ" * 7


def test_vmd_extension_is_inferred_as_target_only():
    assert infer_target_format_from_path("motion.vmd", "kimodo") == "mmd-vmd"


def test_vmd_rejects_non_soma_skeleton():
    skeleton = _FakeSoma77()
    skeleton.name = "smplx22"
    try:
        motion_to_vmd_bytes(
            torch.eye(3).repeat(1, 77, 1, 1),
            torch.zeros((1, 3)),
            skeleton=skeleton,
            fps=30.0,
        )
    except ValueError as error:
        assert "SOMA" in str(error)
    else:
        raise AssertionError("Expected non-SOMA VMD export to fail")


def test_vmd_rejects_non_positive_scale():
    skeleton = _FakeSoma77()
    try:
        motion_to_vmd_bytes(
            torch.eye(3).repeat(1, 77, 1, 1),
            torch.zeros((1, 3)),
            skeleton=skeleton,
            fps=30.0,
            scale=0.0,
        )
    except ValueError as error:
        assert "positive" in str(error)
    else:
        raise AssertionError("Expected zero VMD scale to fail")


if __name__ == "__main__":
    test_vmd_binary_layout_and_root_coordinate_conversion()
    test_vmd_reflects_rotation_into_mmd_handedness()
    test_vmd_resamples_source_timeline_to_30fps()
    test_cp932_fixed_field_does_not_split_multibyte_character()
    test_vmd_extension_is_inferred_as_target_only()
    test_vmd_rejects_non_positive_scale()
