# EfficientAT Model Provenance

Upstream: https://github.com/fschmid56/EfficientAT , MIT license (original LICENSE included in `third_party/efficientat`). Vendored source commit `a425fdce92572e602a1d5634799bd9f1f2efa806`. Release `v0.0.1`.

| ID | Release asset | Bytes | Parameters | AudioSet mAP |
|---|---|---:|---:|---:|
| mn10_as (default) | mn10_as_mAP_471.pt | 19708753 | 4.88 million | 0.471 |
| mn04_as (alternative) | mn04_as_mAP_432.pt | 4066513 | 0.983 million | 0.432 |

The original 527-class AudioSet label CSV and source model implementation are included. Original mel preprocessing uses 32kHz, 128 mel bins, 1024 FFT, 800 window and 320 hop with evaluation mode normalization, not generic log-mel settings. Upstream CPU float32 predictions may differ slightly from reported fp16 results.

Official GitHub release metadata contains no SHA256. Initial development setup uses exact version/filename/byte-size and a SHA256 manifest (trust-on-first-use). **Production requires externally supplied `EXPECTED_MODEL_SHA256` to avoid trusting an unverified first download**. Runtime verifies cached SHA256 and loads with `torch.load(weights_only=True)` and `strict=True`. Upstream published accuracy is not a validated SuperApp result. Review dependencies, pretrained model terms and AudioSet licensing before commercial release.
