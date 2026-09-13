"""Rebuild the two corrected longitudinal sections used by the VO sheet.

The source STEP/BRep model is never changed.  These are drawing-only
conventions: tooth rims use conventional envelopes, longitudinally cut
fasteners/rings/shafts remain unhatched, and Z8 (position 32) is omitted from
B–B in accordance with the review note that is printed next to the view.
"""
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
REDUCER_PROJ = HERE.parents[2] / "Сборочный_чертёж_редуктора" / "Исходные_данные" / "Проекции"
sys.path.insert(0, str(REDUCER_PROJ))
sys.path.insert(0, "/tmp")

from okp_projection_fine import (  # noqa: E402
    BRepAlgoAPI_Common,
    BRepAlgoAPI_Section,
    DATA,
    NODES,
    clipping_box,
    compound,
    edges,
    gp_Dir,
    gp_Pln,
    gp_Pnt,
    load,
    project,
)
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut  # noqa: E402


PHYSICAL_IDS = set(json.loads((DATA / "physical_ids.json").read_text()))
OUT = HERE / "Проекции"


def under(node_id, root_id):
    while node_id is not None:
        if node_id == root_id:
            return True
        node_id = NODES[node_id]["parent"]
    return False


def leaves(roots):
    return [
        node["id"]
        for node in NODES
        if node["id"] in PHYSICAL_IDS
        and any(under(node["id"], root) for root in roots)
    ]


def full_name(node_id):
    names = []
    while node_id is not None:
        names.append(NODES[node_id]["name"])
        node_id = NODES[node_id]["parent"]
    return " ".join(names).lower()


def unsectioned(node_id):
    name = full_name(node_id)
    return any(
        word in name
        for word in (
            "вал-шестерня",
            "вад-шестерня",
            "вал vi",
            "винт",
            "гайка",
            "шайба",
            "кольцо",
            "шарик",
            "пружина",
            "штифт",
            "шпонка",
            # The microswitch is a purchased electromechanical product.  In
            # the local D-D section its case and terminals are shown by their
            # visible outlines, without cutting the internal construction.
            "микропереключатель",
        )
    )


def build_section(ids, plane_x, omitted=(), trim_cover_screw=False):
    clip = clipping_box(0, plane_x, False)
    plane = gp_Pln(gp_Pnt(plane_x, 0, 0), gp_Dir(1, 0, 0))
    shown_shapes = []
    sections = []

    for node_id in ids:
        if node_id in omitted:
            continue
        bbox = NODES[node_id]["bbox"]
        if not bbox or bbox[0] > plane_x + 1e-5:
            continue

        source = load(node_id)
        if node_id == 389:
            # The supplied model leaves the retaining ring and M8 nut inside
            # the hub volume.  Carve their exact drawing envelopes from the
            # hub so the section hatch stops at the mating boundaries.
            for tool_id in (248, 280):
                operation = BRepAlgoAPI_Cut(source, load(tool_id))
                operation.Build()
                source = operation.Shape()
        elif node_id == 392:
            operation = BRepAlgoAPI_Cut(source, load(248))
            operation.Build()
            source = operation.Shape()
        if trim_cover_screw and node_id == 286:
            # The STEP lets the M2 cover screw run into the rotating part.
            # Shorten only its drawing representation to the free face.
            operation = BRepAlgoAPI_Common(
                source, clipping_box(1, 41.5, False)
            )
            operation.Build()
            source = operation.Shape()

        intersects = bbox[0] < plane_x - 1e-5 and bbox[3] > plane_x + 1e-5
        if intersects:
            operation = BRepAlgoAPI_Common(source, clip)
            operation.Build()
            shown = operation.Shape()
            if not unsectioned(node_id):
                section = BRepAlgoAPI_Section(source, plane, False)
                section.Build()
                sections.append({"id": node_id, "edges": edges(section.Shape(), .002)})
        else:
            shown = source

        if not shown.IsNull():
            shown_shapes.append(shown)

    value = project(compound(shown_shapes), (1, 0, 0), (0, 1, 0))
    value["sections"] = sections
    value["metadata"] = {
        "plane_x": plane_x,
        "omitted_ids": list(omitted),
        "drawing_only_screw_trim": bool(trim_cover_screw),
    }
    return value


def main():
    long_roots = [
        node["id"]
        for node in NODES
        if node["parent"] == 0
        and node["bbox"]
        and node["bbox"][4] <= 65
        and node["bbox"][3] < 45
        and node["bbox"][0] > -50
        and node["id"] != 4
    ]
    long_data = build_section(
        leaves(long_roots),
        -15.33,
        # Z8 is omitted by the review note.  The exact HLR of the two springs
        # is replaced on the sheet by their conventional cut traces according
        # to GOST 2.401.  The incorrectly oriented M2 solid is likewise drawn
        # conventionally on the sheet, with its head outside the mating part.
        omitted=(304, 286, 395, 398),
        trim_cover_screw=False,
    )
    (OUT / "long_revised_clean.json").write_text(
        json.dumps(long_data, separators=(",", ":"))
    )

    clutch_data = build_section(leaves((299,)), -6.667)
    (OUT / "clutch_revised_clean.json").write_text(
        json.dumps(clutch_data, separators=(",", ":"))
    )

    # D–D through the second actual KW10-Z1P microswitch, on the Axis-M
    # side.  X=131.419995 passes through the axes of both M1.6 fasteners.
    microswitch_data = build_section(
        leaves((148, 159, 164, 194)), 131.4199947446
    )
    (OUT / "microswitch2_clean.json").write_text(
        json.dumps(microswitch_data, separators=(",", ":"))
    )


if __name__ == "__main__":
    main()
