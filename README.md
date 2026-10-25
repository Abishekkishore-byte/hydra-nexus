# Hydra Nexus: pocket-size water identification, purification and verification capsule

**Identify. Purify. Verify.** Hydra Nexus is a handheld capsule that runs a closed loop: IDENTIFY → DECIDE → PURIFY → VERIFY → COMPARE.

1. It measures a raw water sample (M1).
2. It adapts its filtration based on that reading.
3. It measures the treated water again in the same sensing cell (M2).
4. It dispenses the water only if the measured change meets its targets.

This repository holds the Stage 2 design files for the **Vishwakarma Awards 2026–27** submission.

> **Status, October 2026:** this is a design package. No hardware has been fabricated or tested yet, and no result in this repository is a measurement.

## Contents

| Path | What it is |
|------|------------|
| `cad/build_capsule.py` | Parametric FreeCAD (PartDesign) build script. All dimensions come from the `Params` spreadsheet |
| `cad/HydraNexus_Capsule_v1.FCStd` | Native FreeCAD model: shell, top cap, twist-lock cartridge, shared sensing cell, UV-C chamber, pump, valves, dry spine, 18650 cell |
| `cad/HydraNexus_Capsule_v1.step` | STEP export of the same model |
| `cad/screenshots/` | FreeCAD screenshots showing the model and its feature tree |
| `electronics/HydraNexus_Capsule.kicad_sch` | KiCad schematic: USB-C charging (MCP73831), 18650, AP2112K 3.3 V LDO, MT3608 5 V boost, battery-voltage sense, ESP32-C3 module (WROOM-02 symbol), ADS1115, pH/EC/temperature connectors, turbidity transimpedance amplifier, INA219, low-side MOSFET drivers |
| `electronics/gen_schematic.py` | Generator that builds the schematic from the design netlist using official KiCad symbols |
| `electronics/ERC_report.rpt` | Electrical rules check (ERC) report from `kicad-cli` |
| `electronics/HydraNexus_Capsule_schematic.pdf` | Schematic plot |
| `docs/BOM_preliminary.csv` | Preliminary bill of materials. Prices are DFRobot list prices accessed 24 Oct 2026; every other line needs a quotation |
| `docs/Hydra_Nexus_Vishwakarma_Stage2_Submission.pptx` | The Stage 2 submission deck |
| `visuals/` | Conceptual CAD-style renders and the scripts that generated them |

## How to rebuild

```bash
FreeCADCmd build_capsule.py                                     # in cad/
python gen_schematic.py "<KiCad>/share/kicad/symbols" HydraNexus_Capsule.kicad_sch
kicad-cli sch erc HydraNexus_Capsule.kicad_sch -o ERC_report.rpt
```

## Honesty notes

- **AI-assisted.** The CAD model, schematic and renders were produced with AI assistance from the team's Stage 1 concept. The team must review, own and adjust them, and disclose AI assistance where the award rules require it.
- **Concept values.** Dimensions, component values and pin assignments are proposals. Footprints and a PCB layout are not done yet.
- **No measured results.** Nothing in this repository is a measured result. Sensor accuracies are manufacturer specifications.
- **Measurement scope.** pH, TDS and turbidity readings cannot confirm that water is free of pathogens or chemical contaminants. Hydra Nexus reports only measured changes in its installed parameters and recommends laboratory testing where needed.
