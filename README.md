# Inducing Overthink: Hierarchical Genetic Algorithm-based DoS Attack on Black-Box Large Language Reasoning Models

[![arXiv](https://img.shields.io/badge/arXiv-2605.13338-b31b1b.svg)](https://arxiv.org/abs/2605.13338)
[![Conference](https://img.shields.io/badge/ICML-2026-blue)](https://icml.cc/)

This repository contains the official implementation of the paper **"Inducing Overthink: Hierarchical Genetic Algorithm-based DoS Attack on Black-Box Large Language Reasoning Models"**, accepted at **ICML 2026**.

## Overview

This project implements a Hierarchical Genetic Algorithm (GA) designed to launch Denial-of-Service (DoS) attacks on black-box large language reasoning models. By strategically inducing "overthinking" in the target models, the attack significantly increases the number of generated reasoning tokens, thereby wasting computational resources and causing DoS.

The core algorithm evolves input math problems (e.g., by splitting, crossing over, and mutating premises) to find optimal adversarial prompts that cause the maximum reasoning tokens from the target LLM.

## Installation

This project is built using Python 3.10+ and uses `uv` or `pip` for dependency management.

```bash
# Clone the repository
git clone https://github.com/EndlessCao/Overthink-HGA.git
cd Overthink-HGA

# Install dependencies using pip (or uv)
pip install -r pyproject.toml
# or simply
pip install openai python-dotenv numpy swanlab
```

## Configuration

The framework utilizes different models for the attacker (which proposes problem variations) and the target (which is being attacked). You need to configure API access for both.

Copy the `.env.example` file to create your `.env` file:
```bash
cp .env.example .env
```

Update your `.env` with the appropriate API endpoints and keys:
```env
TARGET_BASE_URL=https://api.openai.com/v1
TARGET_API_KEY=your_target_api_key_here

ATTACKER_BASE_URL=https://api.openai.com/v1
ATTACKER_API_KEY=your_attacker_api_key_here
```

## Usage

To start a test run using the Genetic Algorithm on a sample dataset (like `svamp_test.json`), simply run the `main.py` script:

```bash
python main.py
```

The script will:
1. Load initial math problems from the dataset.
2. Initialize the `GeneAttacker` with a specific population size and generation limit.
3. Evolve the problems iteratively, tracking fitness (token count and overthink penalties) using [SwanLab](https://swanlab.cn/).
4. Output the adversarial prompt that causes the worst-case overthinking on the target model.

## Repository Structure

- `main.py`: Entry point for running the Genetic Algorithm attack.
- `algorithm.py`: Core implementation of the `GeneAttacker` and genetic operators (selection, crossover, mutation).
- `model.py`: API wrappers for `TargetModel` and `AttackerModel`.
- `prompts.py`: Prompt templates used by the attacker model to split/mutate problems.
- `types.py`: Definitions for structured problems (`MathProblem`, `Problem`).
- `utils.py`: Utilities for reading and sampling datasets.
- `algorithm_concept_design.md`: Theoretical design and explanation of the algorithm (in English).

## Citation

If you find our work useful in your research, please consider citing our paper:

```bibtex
@article{overthink_dos_2026,
  title={Inducing Overthink: Hierarchical Genetic Algorithm-based DoS Attack on Black-Box Large Language Reasoning Models},
  author={Shuqiang Wang and Wei Cao and Jiaqi Weng and Jialing Tao and Licheng Pan and Hui Xue and Zhixuan Chu},
  journal={arXiv preprint arXiv:2605.13338},
  year={2026}
}
```
