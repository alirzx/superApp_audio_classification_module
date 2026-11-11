# EfficientAT upstream

Source: https://github.com/fschmid56/EfficientAT at commit `a425fdce92572e602a1d5634799bd9f1f2efa806`, MIT license (see LICENSE). Changes: `models/preprocess.py` uses modern PyTorch complex STFT equivalent; `helpers/utils.py` locates AudioSet labels relative to its source directory; `models/mn/model.py` suppresses debug model print. All other source elements are unchanged. Runtime constructs a model with `pretrained_name=None` and loads the locally verified checkpoint; upstream automatic downloader is never invoked.
