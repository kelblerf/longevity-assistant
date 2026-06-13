# Biomarker Intake Review

- input: `C:\Users\Petr\Downloads\Rozbor krve.xlsx`
- output: `C:\Users\Petr\Documents\AI_ChatGPT_Projekt_Kartičky\Longevity\longevity-assistant\notes\biomarker-intake-draft-rozbor-krve.csv`
- written rows: `155`
- skipped rows: `6`
- confirmed runtime import on `2026-06-11`: `6` reports / `155` observations / `50` trends
- user-confirmed corrections applied on `2026-06-11`:
  - `RLP 2022` exact date set to `2022-01-12`
  - `RLP2026` exact date set to `2026-01-05`
  - `RLP 2020 / GGT` corrected from `19.0` to `0.19`
  - `SYNLAB_IFMV2021 / Trombocyty` standard platelet value overridden from `79` to `175`

## Counts by report

- `RLP-2018`: `21`
- `RLP 2020`: `21`
- `SYNLAB_IFMV2021`: `49`
- `RLP 2022`: `23`
- `RLP2026`: `24`
- `SYNLAB_k 7.10.2021`: `17`

## Counts by category

- `kidney`: `13`
- `liver`: `27`
- `inflammation`: `4`
- `minerals`: `6`
- `electrolytes`: `9`
- `hormones`: `7`
- `lipids`: `24`
- `methylation`: `2`
- `vitamins`: `5`
- `thyroid`: `5`
- `blood_count`: `46`
- `glucose_metabolism`: `7`

## Source-Verified Findings

- `Vitamin D 25-OH` on source row `33` had source unit `mmol/l`, but source values `101.9` and `131.8` fit the stated reference range `75-500` only as `nmol/L`. The normalized CSV unit `nmol/L` is therefore an intentional correction, not an import bug.
- `GGT` on source row `10` was originally written in the workbook as `19.0` with reference range `0.0-1.0 μkat/l` for `RLP 2020`. After user confirmation, the normalized dataset now uses `0.19`.
- `Bilirubin celkovy` on source row `5` for `RLP-2018` contains `2021-03-11` in the value cell. This is clearly malformed in the source workbook and was correctly skipped from the normalized output.
- `SYNLAB_IFMV2021` hematology rows `46-53` contain values without repeated date cells in the source workbook. The import used `2021-01-05` as a fallback from the surrounding block, so these rows should stay usable but remain lower-confidence.
- `RLP 2022` and `RLP2026` originally entered the normalized draft with approximated dates from the year header. After user confirmation, they now use exact dates `2022-01-12` and `2026-01-05`.

## Manual Review Queue

- rows `46-53` / `SYNLAB_IFMV2021` / hematology block: values look structurally consistent, but the exact date should be upgraded if a source report with the true collection date is available
- row `42` / `SYNLAB_IFMV2021` / `PLTh`: keep as a separate specialized marker; do not merge it into the standard platelet marker
- row `53` / `SYNLAB_IFMV2021` / `Trombocyty`: normalized runtime now uses user-confirmed standard platelet value `175`, while `PLTh 79` remains preserved as a separate specialized marker

## Skipped / Structural Rows

- row `5` / `RLP-2018` / `Bilirubin celkovy`: `date_in_value_column` (`2021-03-11 00:00:00`)
- row `21` / `structural` / `Separace séra`: `non_biomarker_row_skipped`
- row `22` / `structural` / `Odběr ze žíly`: `non_biomarker_row_skipped`
- row `44` / `structural` / `Krevní obraz základní (KO)`: `non_biomarker_row_skipped`
- row `45` / `structural` / `Krevní obraz + 5 populační dif.`: `non_biomarker_row_skipped`
- row `56` / `source_row` / `Anti TSH receptor (TRAK)`: `malformed_marker_metadata_row_skipped` (`abbr=0.0, unit=0.0`)

## Recommended Next Pass

- leave the vitamin D unit normalization as-is
- keep PLTh as a separate marker and do not collapse it into standard platelets
