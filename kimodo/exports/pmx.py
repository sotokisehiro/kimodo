# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Generate a small PMX 2.0 mannequin for validating Kimodo VMD exports."""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Union

import numpy as np

from kimodo.exports.vmd import MMD_BONE_TARGETS
from kimodo.skeleton.registry import build_skeleton

PMX_SIGNATURE = b"PMX "
PMX_VERSION = 2.0
PMX_TEXT_ENCODING = 0  # UTF-16LE, without a BOM (PMX header encoding value 0).
REFERENCE_MODEL_NAME = "Kimodo"


@dataclass(frozen=True)
class _Bone:
    name: str
    english_name: str
    position: np.ndarray
    parent: int
    tail_offset: np.ndarray
    movable: bool = False
    ik_target: int | None = None
    ik_links: tuple[int, ...] = ()


@dataclass(frozen=True)
class _Material:
    name: str
    english_name: str
    diffuse: tuple[float, float, float, float]
    ambient: tuple[float, float, float]


class _MeshBuilder:
    def __init__(self) -> None:
        self.vertices: list[tuple[np.ndarray, np.ndarray, tuple[float, float], int]] = []
        self.faces_by_material: list[list[int]] = [[], [], [], []]

    def _vertex(self, position: np.ndarray, normal: np.ndarray, uv: tuple[float, float], bone: int) -> int:
        self.vertices.append((position.astype(np.float32), normal.astype(np.float32), uv, bone))
        return len(self.vertices) - 1

    def cylinder(
        self,
        start: np.ndarray,
        end: np.ndarray,
        radius: float,
        bone: int,
        material: int,
        sides: int = 8,
    ) -> None:
        direction = end - start
        length = float(np.linalg.norm(direction))
        if length < 1e-5:
            return
        axis = direction / length
        reference = np.array([0.0, 1.0, 0.0])
        if abs(float(np.dot(axis, reference))) > 0.9:
            reference = np.array([1.0, 0.0, 0.0])
        u = np.cross(axis, reference)
        u /= np.linalg.norm(u)
        v = np.cross(axis, u)
        rings: list[list[int]] = [[], []]
        for ring, center in enumerate((start, end)):
            for side in range(sides):
                angle = 2.0 * math.pi * side / sides
                normal = math.cos(angle) * u + math.sin(angle) * v
                position = center + radius * normal
                rings[ring].append(self._vertex(position, normal, (side / sides, float(ring)), bone))
        indices = self.faces_by_material[material]
        for side in range(sides):
            nxt = (side + 1) % sides
            a, b = rings[0][side], rings[0][nxt]
            c, d = rings[1][side], rings[1][nxt]
            indices.extend((a, b, c, b, d, c))

    def sphere(
        self,
        center: np.ndarray,
        radius: float,
        bone: int,
        material: int,
        rings: int = 6,
        sides: int = 10,
    ) -> None:
        grid: list[list[int]] = []
        for ring in range(rings + 1):
            latitude = math.pi * ring / rings
            row = []
            for side in range(sides):
                longitude = 2.0 * math.pi * side / sides
                normal = np.array(
                    [
                        math.sin(latitude) * math.cos(longitude),
                        math.cos(latitude),
                        math.sin(latitude) * math.sin(longitude),
                    ]
                )
                row.append(
                    self._vertex(
                        center + radius * normal,
                        normal,
                        (side / sides, ring / rings),
                        bone,
                    )
                )
            grid.append(row)
        indices = self.faces_by_material[material]
        for ring in range(rings):
            for side in range(sides):
                nxt = (side + 1) % sides
                a, b = grid[ring][side], grid[ring][nxt]
                c, d = grid[ring + 1][side], grid[ring + 1][nxt]
                if ring != 0:
                    indices.extend((a, b, c))
                if ring != rings - 1:
                    indices.extend((b, d, c))


def _text(value: str) -> bytes:
    encoded = value.encode("utf-16-le")
    return struct.pack("<i", len(encoded)) + encoded


def _vec3(value: Iterable[float]) -> bytes:
    return struct.pack("<3f", *(float(x) for x in value))


def _reference_positions() -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    skeleton = build_skeleton(77)
    neutral = skeleton.neutral_joints.detach().cpu().numpy().astype(np.float64)
    height = float(neutral[:, 1].max() - neutral[:, 1].min())
    scale = 20.0 / height
    converted = neutral * np.array([scale, scale, -scale])
    converted[:, 1] -= converted[:, 1].min()
    source_positions = {name: converted[index] for name, index in skeleton.bone_index.items()}
    target_positions = {target.name: source_positions[target.source] for target in MMD_BONE_TARGETS}
    return source_positions, target_positions


def _make_bones(
    source_positions: dict[str, np.ndarray], target_positions: dict[str, np.ndarray]
) -> tuple[list[_Bone], dict[str, int]]:
    bones: list[_Bone] = []
    indices: dict[str, int] = {}

    def add(
        name: str,
        english: str,
        position: np.ndarray,
        parent_name: str | None,
        tail: np.ndarray,
        *,
        movable: bool = False,
        ik_target: int | None = None,
        ik_links: tuple[int, ...] = (),
    ) -> int:
        parent = -1 if parent_name is None else indices[parent_name]
        index = len(bones)
        bones.append(_Bone(name, english, position, parent, tail, movable, ik_target, ik_links))
        indices[name] = index
        return index

    origin = np.zeros(3)
    center_position = target_positions["センター"]
    add("全ての親", "Motherbone", origin, None, center_position - origin, movable=True)
    add("センター", "Center", center_position, "全ての親", np.array([0.0, 1.0, 0.0]), movable=True)
    add("下半身", "Lower body", target_positions["下半身"], "センター", np.array([0.0, -1.0, 0.0]))
    add(
        "上半身",
        "Upper body",
        target_positions["上半身"],
        "センター",
        target_positions["上半身2"] - target_positions["上半身"],
    )
    add(
        "上半身2",
        "Upper body 2",
        target_positions["上半身2"],
        "上半身",
        target_positions["首"] - target_positions["上半身2"],
    )
    add("首", "Neck", target_positions["首"], "上半身2", target_positions["頭"] - target_positions["首"])
    add("頭", "Head", target_positions["頭"], "首", np.array([0.0, 1.0, 0.0]))

    source_to_target = {target.source: target.name for target in MMD_BONE_TARGETS}
    source_to_target["Hips"] = "下半身"
    already = set(indices)
    for target in MMD_BONE_TARGETS:
        if target.name in already or target.name in ("センター", "下半身", "上半身", "上半身2", "首", "頭"):
            continue
        if target.parent_source == "Hips":
            parent_name = "下半身"
        elif target.parent_source is None:
            parent_name = "センター"
        else:
            parent_name = source_to_target[target.parent_source]
        position = target_positions[target.name]
        tail = np.array([0.0, 0.45, 0.0])
        add(target.name, target.source, position, parent_name, tail)
        already.add(target.name)

    # Point tails at the first direct child where possible. This is only visual metadata.
    children: dict[int, list[int]] = {i: [] for i in range(len(bones))}
    for index, bone in enumerate(bones):
        if bone.parent >= 0:
            children[bone.parent].append(index)
    updated = []
    for index, bone in enumerate(bones):
        tail = bone.tail_offset
        if children[index]:
            tail = bones[children[index][0]].position - bone.position
        updated.append(
            _Bone(
                bone.name,
                bone.english_name,
                bone.position,
                bone.parent,
                tail,
                bone.movable,
                bone.ik_target,
                bone.ik_links,
            )
        )
    bones = updated

    for side_jp, side_en in (("左", "Left"), ("右", "Right")):
        ankle = indices[f"{side_jp}足首"]
        knee = indices[f"{side_jp}ひざ"]
        leg = indices[f"{side_jp}足"]
        position = target_positions[f"{side_jp}足首"].copy()
        position[2] = source_positions[f"{side_en}ToeBase"][2]
        add(
            f"{side_jp}足ＩＫ",
            f"{side_en} leg IK",
            position,
            "全ての親",
            np.array([0.0, 0.0, -1.0]),
            movable=True,
            ik_target=ankle,
            ik_links=(knee, leg),
        )
    return bones, indices


def _make_mesh(
    source_positions: dict[str, np.ndarray],
    target_positions: dict[str, np.ndarray],
    bone_indices: dict[str, int],
) -> _MeshBuilder:
    mesh = _MeshBuilder()

    def segment(a: str, b: str, radius: float, bone: str, material: int) -> None:
        mesh.cylinder(target_positions[a], target_positions[b], radius, bone_indices[bone], material)

    segment("下半身", "上半身", 1.25, "下半身", 0)
    segment("上半身", "上半身2", 1.55, "上半身", 0)
    segment("上半身2", "首", 1.3, "上半身2", 0)
    segment("首", "頭", 0.45, "首", 0)
    mesh.sphere(target_positions["頭"] + np.array([0.0, 0.65, 0.0]), 1.15, bone_indices["頭"], 3)

    for side_jp, side_en, material in (("左", "Left", 1), ("右", "Right", 2)):
        segment(f"{side_jp}肩", f"{side_jp}腕", 0.42, f"{side_jp}肩", material)
        segment(f"{side_jp}腕", f"{side_jp}ひじ", 0.48, f"{side_jp}腕", material)
        segment(f"{side_jp}ひじ", f"{side_jp}手首", 0.38, f"{side_jp}ひじ", material)
        mesh.sphere(target_positions[f"{side_jp}手首"], 0.48, bone_indices[f"{side_jp}手首"], material)

        segment(f"{side_jp}足", f"{side_jp}ひざ", 0.72, f"{side_jp}足", material)
        segment(f"{side_jp}ひざ", f"{side_jp}足首", 0.58, f"{side_jp}ひざ", material)
        toe = source_positions[f"{side_en}ToeBase"]
        mesh.cylinder(
            target_positions[f"{side_jp}足首"],
            toe,
            0.5,
            bone_indices[f"{side_jp}足首"],
            material,
        )

        for finger_jp, finger_en in (
            ("親指", "Thumb"),
            ("人指", "Index"),
            ("中指", "Middle"),
            ("薬指", "Ring"),
            ("小指", "Pinky"),
        ):
            suffixes = ("０", "１", "２") if finger_jp == "親指" else ("１", "２", "３")
            for link, suffix in enumerate(suffixes, start=1):
                name = f"{side_jp}{finger_jp}{suffix}"
                start = target_positions[name]
                if link < 3:
                    end = target_positions[f"{side_jp}{finger_jp}{suffixes[link]}"]
                else:
                    previous = target_positions[f"{side_jp}{finger_jp}{suffixes[link - 2]}"]
                    end = start + 0.7 * (start - previous)
                mesh.cylinder(start, end, 0.10, bone_indices[name], material, sides=6)
    return mesh


def build_reference_pmx_bytes() -> bytes:
    """Build a self-contained low-poly PMX 2.0 model compatible with Kimodo VMD output."""
    source_positions, target_positions = _reference_positions()
    bones, bone_indices = _make_bones(source_positions, target_positions)
    mesh = _make_mesh(source_positions, target_positions, bone_indices)
    materials = (
        _Material("胴体", "Body", (0.66, 0.69, 0.72, 1.0), (0.25, 0.26, 0.28)),
        _Material("左側", "Left side", (0.20, 0.48, 0.95, 1.0), (0.08, 0.15, 0.30)),
        _Material("右側", "Right side", (0.95, 0.28, 0.24, 1.0), (0.30, 0.09, 0.07)),
        _Material("頭", "Head", (0.88, 0.86, 0.70, 1.0), (0.30, 0.29, 0.22)),
    )

    out = bytearray(PMX_SIGNATURE)
    out.extend(struct.pack("<f", PMX_VERSION))
    out.extend(struct.pack("<B8B", 8, PMX_TEXT_ENCODING, 0, 4, 4, 4, 4, 4, 4))
    out.extend(_text(REFERENCE_MODEL_NAME))
    out.extend(_text(REFERENCE_MODEL_NAME))
    out.extend(
        _text("Kimodo VMD validation mannequin. Left=blue, right=red. Foot IK is available but VMD disables it.")
    )
    out.extend(_text("Reference mannequin for validating Kimodo VMD motion."))

    out.extend(struct.pack("<i", len(mesh.vertices)))
    for position, normal, uv, bone in mesh.vertices:
        out.extend(_vec3(position))
        out.extend(_vec3(normal))
        out.extend(struct.pack("<2f", *uv))
        out.extend(struct.pack("<Bi", 0, bone))  # BDEF1
        out.extend(struct.pack("<f", 1.0))

    all_face_indices = [index for faces in mesh.faces_by_material for index in faces]
    out.extend(struct.pack("<i", len(all_face_indices)))
    for index in all_face_indices:
        out.extend(struct.pack("<i", index))
    out.extend(struct.pack("<i", 0))  # textures

    out.extend(struct.pack("<i", len(materials)))
    for material, faces in zip(materials, mesh.faces_by_material):
        out.extend(_text(material.name))
        out.extend(_text(material.english_name))
        out.extend(struct.pack("<4f", *material.diffuse))
        out.extend(struct.pack("<3f", 0.20, 0.20, 0.20))
        out.extend(struct.pack("<f", 8.0))
        out.extend(struct.pack("<3f", *material.ambient))
        out.extend(struct.pack("<B", 0x1F))
        out.extend(struct.pack("<4f", 0.08, 0.08, 0.08, 1.0))
        out.extend(struct.pack("<f", 0.35))
        out.extend(struct.pack("<iiBB", -1, -1, 0, 1))
        out.extend(struct.pack("<B", 1))  # built-in toon02.bmp
        out.extend(_text("Kimodo reference material"))
        out.extend(struct.pack("<i", len(faces)))

    out.extend(struct.pack("<i", len(bones)))
    for bone in bones:
        out.extend(_text(bone.name))
        out.extend(_text(bone.english_name))
        out.extend(_vec3(bone.position))
        out.extend(struct.pack("<ii", bone.parent, 0))
        flags = 0x001A | (0x0004 if bone.movable else 0) | (0x0020 if bone.ik_target is not None else 0)
        out.extend(struct.pack("<H", flags))
        out.extend(_vec3(bone.tail_offset))
        if bone.ik_target is not None:
            out.extend(struct.pack("<iifi", bone.ik_target, 40, 1.0, len(bone.ik_links)))
            for link in bone.ik_links:
                out.extend(struct.pack("<iB", link, 0))

    out.extend(struct.pack("<i", 0))  # morphs
    frames = (
        ("Root", "Root", 1, (bone_indices["全ての親"], bone_indices["センター"])),
        ("表情", "Expression", 1, ()),
        ("体", "Body", 0, tuple(range(2, len(bones)))),
    )
    out.extend(struct.pack("<i", len(frames)))
    for name, english, special, elements in frames:
        out.extend(_text(name))
        out.extend(_text(english))
        out.extend(struct.pack("<Bi", special, len(elements)))
        for bone_index in elements:
            out.extend(struct.pack("<Bi", 0, bone_index))
    out.extend(struct.pack("<ii", 0, 0))  # rigid bodies, joints
    return bytes(out)


def save_reference_pmx(path: Union[str, Path]) -> None:
    """Write the Kimodo VMD validation mannequin to ``path``."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(build_reference_pmx_bytes())
