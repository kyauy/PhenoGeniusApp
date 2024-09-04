---
title: PhenoGenius
emoji: 🧞‍♂️
sdk: streamlit
sdk_version: 1.38.0
app_file: phenogenius_app.py
python_version: 3.11
pinned: true
---

# PhenoGenius web app

Symptom interaction modeling for precision medicine

## Overview

Symptom interaction model provide a method to standardize clinical descriptions and fully exploit phenotypic data in precision medicine.

This repository contains scripts and files to use PhenoGenius Web app, the phenotype matching system for genetic disease based on this model. **Please try PhenoGenius in the cloud at [https://huggingface.co/spaces/kyauy/PhenoGenius](https://huggingface.co/spaces/kyauy/PhenoGenius).**

If you use PhenoGenius, please cite:
> Yauy et al., Learning phenotypic patterns in genetic disease by symptom interaction modeling. medrXiv (2023). [https://doi.org/10.1101/2022.07.29.22278181](https://doi.org/10.1101/2022.07.29.22278181)

## Install

- Requirements

```bash
python == 3.11 #(pyenv install 3.11)
poetry #(https://python-poetry.org/docs/#installation)
git-lfs
```

- Install dependencies

```bash
poetry install
```

If you need to generate a `requirements.txt` file, use the following command:
```
poetry export --without-hashes --format=requirements.txt > requirements.txt
```

NB: if git-lfs is not installed, you won't be able to download PhenoGenius Web app resources.

## Use streamlit webapp in your desktop

### Run

```bash
poetry shell
streamlit run phenogenius_app.py
```


Enjoy !

## Command line interface

The command line interface is available in the PhenoGenius client repository [https://github.com/kyauy/PhenoGenius/](https://github.com/kyauy/PhenoGenius/).

## License

*PhenoGenius* is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for the full license text.

## Misc

*PhenoGenius* is a collaboration of :

[![SeqOne](data/img/logo-seqone.png)](https://seqone.com/)

[![Université Grenoble Alpes](data/img/logo-uga.png)](https://iab.univ-grenoble-alpes.fr/)


