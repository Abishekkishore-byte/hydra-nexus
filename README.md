# Hydra Nexus

**Identify. Purify. Verify.**

Hydra Nexus is a pocket-size capsule that tests water, filters it, and then tests the same water again before it lets you drink it.

Each run goes like this:

1. A small pump pulls in a water sample.
2. The capsule measures its pH, TDS, cloudiness and temperature.
3. It picks a flow speed and UV dose to suit that water.
4. It filters the water through carbon, a fine membrane and optional UV-C light.
5. The treated water goes back through the same test cell.
6. The water comes out of the spout only if it actually improved.

If it didn't improve, the capsule stops and tells you why: the cartridge may need replacing, or the water may need a proper lab test.

This repository holds our design files for the **Vishwakarma Awards 2026–27, Stage 2**.

> **Where we are (October 2026):** this is the design stage. We haven't built or tested any hardware yet, so nothing here is a measured result.

## What's in here

| Folder | What you'll find |
|--------|------------------|
| `cad/` | Our parametric FreeCAD model of the capsule (`.FCStd`, plus a `.STEP` export). It has 9 parts: body, cap, filter cartridge, test cell, UV-C chamber, pump, valves, electronics side and battery. Every key size comes from one parameter table. Also the script that builds the model, and screenshots. |
| `electronics/` | Our KiCad schematic of 75 parts: USB-C charging, the 18650 battery, 3.3 V and 5 V supplies, the ESP32-C3, the ADS1115 converter, the sensor connectors, the cloudiness-sensor amplifier, the current sensor and the switches for the pump, valves and lights. It passes KiCad's electrical check with no errors or warnings. The folder also has the check report, a PDF and the script that generates the schematic. |
| `docs/` | Our Stage 2 deck and a first parts list (CSV). Prices are DFRobot's listed prices from 24 Oct 2026. Everything else is still waiting on quotes. |
| `visuals/` | The concept renders used in the deck and the scripts that drew them. |

## Rebuilding the files

```bash
FreeCADCmd build_capsule.py                                     # run inside cad/
python gen_schematic.py "<KiCad>/share/kicad/symbols" HydraNexus_Capsule.kicad_sch
kicad-cli sch erc HydraNexus_Capsule.kicad_sch -o ERC_report.rpt
```

## Things we want to be upfront about

- **AI help.** We used AI tools to help produce the CAD model, the schematic and the renders from our Stage 1 idea. Our team will go through them, change them where needed, and own them.
- **Starting points, not final choices.** Sizes, part values and pin choices are where we are starting from. We haven't assigned PCB footprints or done a board layout yet.
- **No results yet.** Nothing here is a test result. Sensor accuracies are the manufacturers' figures.
- **What we can't detect.** pH, TDS and cloudiness can't prove water is free of germs or harmful chemicals. Hydra Nexus only reports what it measures, and suggests a lab test when that matters.
