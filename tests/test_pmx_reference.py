# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import struct
from pathlib import Path

import numpy as np

from kimodo.exports.pmx import (
    PMX_SIGNATURE,
    PMX_TEXT_ENCODING,
    PMX_VERSION,
    REFERENCE_MODEL_NAME,
    _text,
    _make_bones,
    _make_mesh,
    _reference_positions,
    build_reference_pmx_bytes,
)
from kimodo.exports.vmd import MMD_BONE_TARGETS


def test_reference_pmx_is_deterministic_and_packaged():
    generated = build_reference_pmx_bytes()
    packaged = Path("kimodo/assets/mmd/kimodo_reference.pmx").read_bytes()
    assert generated[8] == 8
    assert generated[9] == PMX_TEXT_ENCODING == 0
    assert generated == packaged
    assert generated[:4] == PMX_SIGNATURE
    assert struct.unpack_from("<f", generated, 4)[0] == PMX_VERSION


def test_pmx_text_is_bomless_utf16le():
    packed = _text("日本語Kimodo")
    size = struct.unpack_from("<i", packed)[0]
    payload = packed[4:]
    assert size == len(payload)
    assert payload == "日本語Kimodo".encode("utf-16-le")
    assert not payload.startswith((b"\xff\xfe", b"\xfe\xff"))
    assert payload.decode("utf-16-le") == "日本語Kimodo"


def test_reference_model_covers_every_exported_vmd_bone():
    source_positions, target_positions = _reference_positions()
    bones, indices = _make_bones(source_positions, target_positions)
    names = {bone.name for bone in bones}
    assert REFERENCE_MODEL_NAME == "Kimodo"
    assert {target.name for target in MMD_BONE_TARGETS} <= names
    assert {"全ての親", "左足ＩＫ", "右足ＩＫ"} <= names
    assert bones[indices["左足ＩＫ"]].ik_target == indices["左足首"]
    assert bones[indices["右足ＩＫ"]].ik_target == indices["右足首"]


def test_reference_mesh_has_valid_skinning_and_material_ranges():
    source_positions, target_positions = _reference_positions()
    bones, indices = _make_bones(source_positions, target_positions)
    mesh = _make_mesh(source_positions, target_positions, indices)
    assert mesh.vertices
    assert all(0 <= vertex[3] < len(bones) for vertex in mesh.vertices)
    assert len(mesh.faces_by_material) == 4
    assert all(len(faces) > 0 and len(faces) % 3 == 0 for faces in mesh.faces_by_material)
    assert all(0 <= index < len(mesh.vertices) for faces in mesh.faces_by_material for index in faces)


def test_reference_mesh_faces_follow_vertex_normals():
    source_positions, target_positions = _reference_positions()
    _, indices = _make_bones(source_positions, target_positions)
    mesh = _make_mesh(source_positions, target_positions, indices)
    for faces in mesh.faces_by_material:
        for offset in range(0, len(faces), 3):
            vertices = [mesh.vertices[faces[offset + corner]] for corner in range(3)]
            a, b, c = (vertex[0] for vertex in vertices)
            face_normal = np.cross(b - a, c - a)
            vertex_normal = sum((vertex[1] for vertex in vertices), np.zeros(3))
            assert float(np.dot(face_normal, vertex_normal)) > 0.0


if __name__ == "__main__":
    test_reference_pmx_is_deterministic_and_packaged()
    test_pmx_text_is_bomless_utf16le()
    test_reference_model_covers_every_exported_vmd_bone()
    test_reference_mesh_has_valid_skinning_and_material_ranges()
    test_reference_mesh_faces_follow_vertex_normals()
