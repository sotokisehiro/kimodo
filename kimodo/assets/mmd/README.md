# Kimodo MMD reference model

`kimodo_reference.pmx` is a low-poly PMX 2.0 mannequin for validating VMD motions exported by Kimodo.

- Model name: `Kimodo`
- Text encoding: BOM-less UTF-16LE (PMX encoding value 0)
- Height: 20 MMD units
- Left side: blue
- Right side: red
- Rig: standard Japanese MMD body and finger bones, plus left/right foot IK

Load the PMX model in MikuMikuDance, then load a VMD generated with
`kimodo_gen --vmd` or `kimodo_convert ... --to mmd-vmd`. Kimodo VMD files
disable both foot IK bones and drive the legs with FK rotations.

Regenerate the PMX after changing the SOMA-to-MMD mapping:

```bash
kimodo_make_mmd_reference
```
