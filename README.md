<p align="center">
  <img src="./assets/banner.png" alt="Banner" width="100%">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-76B900.svg" alt="License"></a>
  <a href="https://research.nvidia.com/labs/sil/projects/kimodo/"><img src="https://img.shields.io/badge/Project-Page-blue" alt="Project Page"></a>
  <a href="https://research.nvidia.com/labs/sil/projects/kimodo/docs/index.html"><img src="https://img.shields.io/badge/docs-online-green.svg" alt="Documentation"></a>
</p>

## Windowsへのインストール

ここでは、Windows 10/11（64-bit）にPython、PyTorch、Kimodoをソースからインストールし、モーションを生成できる状態にするまでの手順を説明します。KimodoはCPUでも起動できますが、実用的な時間で生成するにはCUDA対応のNVIDIA GPUを推奨します。

### 1. 必要なソフトウェアをインストールする

以下をインストールしてください。

1. [Python公式サイト](https://www.python.org/downloads/windows/)から64-bit版Pythonをインストールします。PyTorchの対応範囲と依存パッケージの互換性を考慮し、Python 3.10または3.11を推奨します。従来のインストーラーを使う場合は、インストール画面で **Add Python to PATH** を有効にします。
2. [Git for Windows](https://git-scm.com/download/win)をインストールします。
3. [CMake](https://cmake.org/download/)のWindows x64 Installerをインストールし、インストーラーでCMakeを`PATH`へ追加します。
4. [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)をインストールします。ワークロード **C++によるデスクトップ開発** を選び、MSVC C++ビルドツールとWindows SDKを含めます。これはKimodoに同梱された`MotionCorrection` C++拡張のビルドに必要です。
5. NVIDIA GPUを使う場合は、[NVIDIAドライバ](https://www.nvidia.com/download/index.aspx)をインストールまたは更新します。

PowerShellを新しく開き、インストールを確認します。

```powershell
py --version
git --version
cmake --version
```

Pythonが複数入っている場合は、次のように使用するバージョンを確認できます。

```powershell
py -3.11 --version
```

### 2. リポジトリを取得する

まだ取得していない場合は、PowerShellで次を実行します。

```powershell
git clone https://github.com/nv-tlabs/kimodo.git
cd kimodo
```

以降のコマンドは、`README.md`や`pyproject.toml`があるKimodoリポジトリのルートで実行してください。

### 3. 仮想環境を作成する

リポジトリ内に`.venv`を作成し、パッケージ管理ツールを更新します。このREADMEのコマンドは、仮想環境をactivateせず、`.venv`内のPythonを直接指定します。

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
```

Python 3.10をインストールした場合は、1行目を`py -3.10 -m venv .venv`に変更してください。

### 4. PyTorchをインストールする

[PyTorch公式インストールページ](https://pytorch.org/get-started/locally/)のセレクターで、次を選びます。

- PyTorch Build: **Stable**
- Your OS: **Windows**
- Package: **Pip**
- Language: **Python**
- Compute Platform: 使用するNVIDIAドライバに適したCUDA、またはCPUのみなら **CPU**

表示されたインストールコマンドの先頭にある`pip3`または`pip`を、`.\.venv\Scripts\python.exe -m pip`へ置き換えて実行します。例えば、公式ページに次のコマンドが表示された場合、

```powershell
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/<CUDAに対応する名前>
```

このリポジトリでは次のように実行します。

```powershell
.\.venv\Scripts\python.exe -m pip install torch torchvision torchaudio `
  --index-url https://download.pytorch.org/whl/<CUDAに対応する名前>
```

`<CUDAに対応する名前>`をそのまま入力せず、必ず公式セレクターが表示した実際のURLを使ってください。通常、PyTorchのpipパッケージには必要なCUDAランタイムが含まれるため、別途CUDA Toolkitをインストールする必要はありませんが、対応するNVIDIAドライバは必要です。

インストール後、PyTorchとCUDAの状態を確認します。

```powershell
.\.venv\Scripts\python.exe -c "import torch; print('PyTorch:', torch.__version__); print('CUDA build:', torch.version.cuda); print('CUDA available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none')"
```

NVIDIA GPUで生成する場合、`CUDA available: True`とGPU名が表示されることを確認してください。

### 5. Kimodoをインストールする

コマンドラインからモーションを生成するための基本構成は、次のコマンドで編集可能インストールします。この処理では`MotionCorrection` C++拡張もCMakeでビルドされます。

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

インタラクティブデモとSOMA関連の追加依存関係もインストールする場合は、代わりに次を実行します。

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[all]"
```

ビルド中にC++コンパイラが見つからない場合は、Visual Studio Build Toolsのインストールを確認し、**Developer PowerShell for VS 2022**から同じコマンドを実行してください。

### 6. Hugging Faceを認証する

Kimodoのテキストエンコーダは、アクセス承認が必要な`meta-llama/Meta-Llama-3-8B-Instruct`を使用します。

1. Hugging Faceアカウントを作成します。
2. [`meta-llama/Meta-Llama-3-8B-Instruct`のモデルページ](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct)で利用条件に同意し、アクセス承認を受けます。
3. [Hugging Faceのトークン設定](https://huggingface.co/settings/tokens/new?tokenType=read)でRead権限のトークンを作成します。
4. CLIをインストールしてログインします。

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade huggingface_hub
.\.venv\Scripts\hf.exe auth login
```

プロンプトが表示されたら、作成したトークンを貼り付けます。トークンはREADME、スクリプト、Git管理下のファイルへ書き込まないでください。

### 7. インストールを確認する

Kimodo、PyTorch、`MotionCorrection`を同じ仮想環境から読み込めることを確認します。

```powershell
.\.venv\Scripts\python.exe -c "import kimodo, motion_correction, torch; print('Kimodo import: OK'); print('MotionCorrection import: OK'); print('CUDA available:', torch.cuda.is_available())"
.\.venv\Scripts\python.exe -m pip check
```

`pip check`で`No broken requirements found.`と表示されれば、インストールされた依存関係に既知の不整合はありません。

### 8. 最初のモーションを生成する

テキストエンコーダをCPUへオフロードし、短いVMDモーションを生成します。`TEXT_ENCODER_DEVICE`に別の値が既に設定されている場合は、その値を上書きしません。

```powershell
if (-not $env:TEXT_ENCODER_DEVICE) {
  $env:TEXT_ENCODER_DEVICE = "cpu"
}
.\.venv\Scripts\python.exe -m kimodo.scripts.generate `
  "A person waves their right hand." `
  --duration 3.0 `
  --vmd `
  --output outputs/first_wave
```

初回実行時はモデルが自動的にダウンロードされるため、完了まで時間がかかることがあります。正常に完了すると、少なくとも`outputs/first_wave.npz`と`outputs/first_wave.vmd`が生成されます。

### 9. (Optional)VMDサイジングCLI版を用意する

CodexなどのAIエージェントから操作する場合は、[VMDサイジングCLI版](https://github.com/errno-mmd/vmd_sizing/releases/download/ver5.01.08-CLI/VmdSizing_5.01.08_64bit_cli.exe)をダウンロードして、本リポジトリ(最初にgit cloneでできたフォルダ)に置いてください。
AIエージェントがこのVMDサイジングCLI版のexeファイルを使用します。

本CLI版は、miuさん作の[VMDサイジング](https://github.com/miu200521358/vmd_sizing)を改造したものです。本家VMDサイジングについては https://bowlroll.net/file/197410 か[Wiki](https://github.com/miu200521358/vmd_sizing/wiki/)を参照ください。

### よくある問題

- **`CUDA available: False`になる**：NVIDIAドライバを更新し、CPU版ではなく、公式セレクターで選んだCUDA版PyTorchを`.venv`へ再インストールしてください。
- **`cmake`が見つからない**：CMakeを`PATH`へ追加し、PowerShellを開き直してください。
- **C++コンパイラが見つからない**：Visual Studio Build Toolsの **C++によるデスクトップ開発** が入っていることを確認し、Developer PowerShellを使用してください。
- **Hugging Faceの401／403エラーになる**：Llamaモデルのアクセス承認、Readトークン、`hf auth login`の状態を確認してください。
- **GPUメモリが不足する**：`TEXT_ENCODER_DEVICE=cpu`を設定してください。テキストエンコーダをCPUへ移すため処理は少し遅くなりますが、GPUメモリ使用量を大幅に削減できます。
- **モデルのダウンロードに失敗する**：インターネット接続、空きディスク容量、Hugging Face認証を確認してから再実行してください。

## Kimodoモーション生成（CLIとCodex）

### `kimodo.scripts.generate`を直接使う

Windowsでは、リポジトリのルートから仮想環境のPythonを直接呼び出します。テキストエンコーダをCPUへオフロードすると、処理はやや遅くなりますがGPUメモリの使用量を抑えられます。

```powershell
if (-not $env:TEXT_ENCODER_DEVICE) {
  $env:TEXT_ENCODER_DEVICE = "cpu"
}
.\.venv\Scripts\python.exe -m kimodo.scripts.generate `
  "A person walks forward." `
  --duration 5.0 `
  --vmd `
  --output outputs/walk_forward
```

第1引数の`prompt`には、生成したい動作を英語で指定します。複数の動作を連続させる場合は、各動作をピリオドで区切ります。`--duration`には全動作で共通の秒数、または各動作に対応する秒数を空白区切りの文字列で指定できます。

```powershell
.\.venv\Scripts\python.exe -m kimodo.scripts.generate `
  "A person walks forward. They stop and wave their right hand." `
  --duration "3.0 3.0" `
  --vmd `
  --output outputs/walk_and_wave
```

この例では、歩行を3秒、右手を振る動作を3秒生成します。秒数の個数は、ピリオドで区切った動作数と一致させてください。

主なコマンドライン引数は次のとおりです。

| 引数 | 既定値 | 説明 |
| --- | --- | --- |
| `prompt` | なし | 動作を表す英語テキスト。`--input_folder`を使わない場合は必須 |
| `--model` | `kimodo-soma-rp` | 使用するKimodoモデル |
| `--duration` | `5.0` | 動作の秒数。複数動作では`"3.0 2.0"`のように指定可能 |
| `--num_samples` | `1` | 生成するサンプル数 |
| `--diffusion_steps` | `100` | Diffusionのステップ数 |
| `--num_transition_frames` | `5` | 連続する動作間の遷移用フレーム数 |
| `--constraints` | なし | 保存済み制約リストのパス |
| `--output` | `output` | NPZ、CSV、BVH、VMDなどに共通する出力名のベース |
| `--save_example_dir` | 無効 | デモ互換の`motion.npz`、`constraints.json`、`meta.json`を含むフォルダも保存 |
| `--bvh` | 無効 | BVHも出力（SOMAモデルのみ） |
| `--bvh_standard_tpose` | 無効 | BVHのレストポーズを標準Tポーズにする |
| `--vmd` | 無効 | MikuMikuDance用VMDも出力（SOMAモデルのみ） |
| `--vmd-model-name` | `Kimodo` | VMD内のモデル名（CP932で最大20バイト） |
| `--vmd-scale` | 自動推定 | メートルからMMD単位への変換倍率 |
| `--no-postprocess` | 無効 | 足滑りを軽減する後処理を無効化（G1では常に無効） |
| `--seed` | なし | 再現可能な生成に使う乱数シード |
| `--input_folder` | なし | `meta.json`と任意の`constraints.json`を含む入力フォルダ |
| `--cfg_type` | モデル既定 | CFG方式：`nocfg`、`regular`、`separated` |
| `--cfg_weight` | モデル既定 | `regular`では重み1個、`separated`ではテキストと制約の重み2個 |

CFGは、例えば次のように指定します。

```powershell
# 通常のCFG
.\.venv\Scripts\python.exe -m kimodo.scripts.generate `
  "A person jumps." --cfg_type regular --cfg_weight 2.0

# テキストと制約に異なる重みを使用
.\.venv\Scripts\python.exe -m kimodo.scripts.generate `
  "A person jumps." --cfg_type separated --cfg_weight 2.0 1.5

# CFGを無効化
.\.venv\Scripts\python.exe -m kimodo.scripts.generate `
  "A person jumps." --cfg_type nocfg
```

`--cfg_type`を省略して`--cfg_weight`だけを指定した場合、重み1個は`regular`、2個は`separated`として扱われます。`--input_folder`を使う場合、プロンプトと時間はフォルダ内の`meta.json`から読み込まれます。`num_samples`、`diffusion_steps`、`seed`も`meta.json`の値が優先され、CFGをCLIで明示した場合はCLIの値が優先されます。

CLIは常にKimodo形式のNPZを保存し、`--vmd`などを付けると対応する形式も追加で保存します。すべての引数は次のコマンドで確認できます。

```powershell
.\.venv\Scripts\python.exe -m kimodo.scripts.generate --help
```

なお、kimodoが生成するモーションはTスタンスの人型3Dモデルを基準としているため、MMDのAスタンスのモデルに適用する前に、VMDサイジングで調整することをお勧めします。
その際、モーション作成モデルPMXとして kimodo\assets\mmd\kimodo_reference.pmx を指定してください。

### Codexから自然言語で使う

このリポジトリの AGENTS.md にCodexへの指示が書かれているので、Codexで「プロジェクトを作成」し、ソースフォルダーとしてこのリポジトリ(最初にgit cloneでできたフォルダー)を指定してください。

Codexには、作りたいモーションを日本語でそのまま指示できます。Codexは内容をKimodo向けの簡潔な英語プロンプトへ変換し、動作の順序、方向、左右、速度、スタイル、時間を対応する引数へ反映してコマンドを実行します。

依頼例：

> 3秒間前に歩いた後、立ち止まって3秒間右手を振るモーションを作って。

このリポジトリでCodexに依頼した場合は、特に指定がなければ次の設定が使われます。

- `.\.venv\Scripts\python.exe`で実行する
- `TEXT_ENCODER_DEVICE`が未設定なら`cpu`を設定する
- `--vmd`を付けてVMDも出力する
- `outputs/`以下に内容を表す短い名前で保存する
- 時間などが省略されていても、結果を大きく左右する曖昧さがなければ既定値を使って生成する

モデル、時間、サンプル数、シード、制約、CFG、VMD以外の形式、出力先なども日本語で指定できます。例えば次のように依頼できます。

> 走ってジャンプする6秒のモーションを3サンプル、seed 42で作って。BVHも出力して。

Codexは、実行前に変換後の英語プロンプトを示し、完了後に生成ファイルのフルパスまたはエラーを報告します。

### 生成したVMDをMMDのモデルへ適用する

最初に、Codexに指示してMMDにモデルを読み込んでください。

> MMDに "C:\MikuMikuDance_x64\UserFile\Model\初音ミクVer2.pmx" のモデルを読み込んで

CodexにMMDへの適用まで依頼した場合、Kimodoが生成したVMDをモデルへ直接適用せず、先にVmdSizingで適用先モデルに合わせます。MMDの操作には[mmd-mcp](https://github.com/BeamManP/mmd-mcp)を使用します。例えば次のような指示を出せます。

> 「垂直ジャンプ(3秒間)、振り返る(2秒間)、でんぐり返り(4秒間)」のモーションを生成し、MMD上の現在のモデルに適用して、MMD上で、カメラ表示への切り替えと再生を行って

VmdSizingには、Kimodoが生成したVMDのフルパスと、MMDでモデルを読み込んだ際に指定したPMXファイルのフルパスを渡します。

```powershell
.\VmdSizing_5.01.08_64bit_cli.exe `
  --motion_path "<Kimodoが生成したVMDのフルパス>" `
  --org_model_path "kimodo\assets\mmd\kimodo_reference.pmx" `
  --rep_model_path "<MMDに読み込んだ適用先モデルのフルパス>" `
  --detail_stance_flg 1 `
  --twist_flg 1
```

処理後は、元のVMD名に適用先モデル名、日付、時刻が追加されたVMDが`outputs`フォルダに生成されます。MMDにはこの新しいサイジング済みVMDを適用します。適用先モデルのフルパスを確認できない場合は、Codexが実行前にそのパスを尋ねます。

===

以下はオリジナルのREADME.mdの内容です。

## Overview

Kimodo is a **ki**nematic **mo**tion **d**iffusi**o**n model trained on a large-scale (700 hours) commercially-friendly optical motion capture dataset. The model generates high-quality 3D human and robot motions, and is controlled through text prompts and an extensive set of constraints such as full-body pose keyframes, end-effector positions/rotations, 2D paths, and 2D waypoints. Full details of the model architecture and training are available in the [technical report](https://research.nvidia.com/labs/sil/projects/kimodo/assets/kimodo_tech_report.pdf).

This repository provides:
- **Inference**: code and CLI to generate motions on both human and robot skeletons
- **Interactive Demo**: easily author motions with a timeline interface of text prompts and kinematic controls
- **Benchmark**: [test cases](https://huggingface.co/datasets/nvidia/Kimodo-Motion-Gen-Benchmark) and evaluation code built on the [BONES-SEED](https://huggingface.co/datasets/bones-studio/seed) dataset to evaluate motion generation models based on text and constraint-following abilities
- **Annotations**: fine-grained temporal text descriptions created for the Kimodo project are included in the [BONES-SEED](https://huggingface.co/datasets/bones-studio/seed) dataset. For more information on these labels, see our separate [Hugging Face repo](https://huggingface.co/datasets/nvidia/SEED-Timeline-Annotations).

<div align="center">
  <img src="assets/teaser.gif" width="1280">
</div>

## News

See the [full changelog](CHANGELOG.md) for a detailed list of all changes.

- **[2026-07-10]** Released the [ARDY project](https://research.nvidia.com/labs/sil/projects/ardy/) -- a _real-time_ motion generation model with all the controllability of Kimodo!
- **[2026-05-03]** _FIX_: fixed a bug causing incorrect calculation of averaged metrics for constraint test cases in the benchmark
- **[2026-04-24]** _NEW_: improved multi-prompt generation and better support for small VRAM GPUs via `TEXT_ENCODER_DEVICE=cpu` env var
- **[2026-04-10]** Released the [Kimodo Motion Generation Benchmark](#kimodo-motion-generation-benchmark) alongside new v1.1 Kimodo-SOMA models
- **[2026-03-19]** **Breaking:** Model inputs/outputs now use the SOMA 77-joint skeleton (`somaskel77`).
- **[2026-03-16]** Initial open-source release of Kimodo with five model variants (SOMA, G1, SMPL-X), CLI, interactive demo, and timeline annotations for BONES-SEED.


## Kimodo Models

Several variations of Kimodo are available trained on various skeletons and datasets. All models support text-to-motion and kinematic controls.

> Note: models will be downloaded automatically when attempting to generate from the CLI or Interactive Demo, so there is no need to download them manually

| Model | Skeleton | Training Data | Release Date | Hugging Face | License |
|:-------|:-------------|:------:|:------:|:-------------:|:-------------:|
| **Kimodo-SOMA-RP-v1.1** | [SOMA](https://github.com/NVlabs/SOMA-X) | [Bones Rigplay 1](https://bones.studio/datasets#rp01) | April 10, 2026 | [Link](https://huggingface.co/nvidia/Kimodo-SOMA-RP-v1.1) | [NVIDIA Open Model](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/) |
| **Kimodo-SOMA-SEED-v1.1** | [SOMA](https://github.com/NVlabs/SOMA-X) | [BONES-SEED](https://huggingface.co/datasets/bones-studio/seed) | April 10, 2026  | [Link](https://huggingface.co/nvidia/Kimodo-SOMA-SEED-v1.1) | [NVIDIA Open Model](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/) |
| **Kimodo-SOMA-RP-v1** | [SOMA](https://github.com/NVlabs/SOMA-X) | [Bones Rigplay 1](https://bones.studio/datasets#rp01) | March 16, 2026 | [Link](https://huggingface.co/nvidia/Kimodo-SOMA-RP-v1) | [NVIDIA Open Model](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/) |
| **Kimodo-G1-RP-v1** | [Unitree G1](https://github.com/unitreerobotics/unitree_mujoco/tree/main/unitree_robots/g1) | [Bones Rigplay 1](https://bones.studio/datasets#rp01) | March 16, 2026  | [Link](https://huggingface.co/nvidia/Kimodo-G1-RP-v1) | [NVIDIA Open Model](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/) |
| **Kimodo-SOMA-SEED-v1** | [SOMA](https://github.com/NVlabs/SOMA-X) | [BONES-SEED](https://huggingface.co/datasets/bones-studio/seed) | March 16, 2026  | [Link](https://huggingface.co/nvidia/Kimodo-SOMA-SEED-v1) | [NVIDIA Open Model](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/) |
| **Kimodo-G1-SEED-v1** | [Unitree G1](https://github.com/unitreerobotics/unitree_mujoco/tree/main/unitree_robots/g1) | [BONES-SEED](https://huggingface.co/datasets/bones-studio/seed) | March 16, 2026  | [Link](https://huggingface.co/nvidia/Kimodo-G1-SEED-v1) | [NVIDIA Open Model](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/) |
| **Kimodo-SMPLX-RP-v1** | [SMPL-X](https://github.com/vchoutas/smplx) | [Bones Rigplay 1](https://bones.studio/datasets#rp01) | March 16, 2026  | [Link](https://huggingface.co/nvidia/Kimodo-SMPLX-RP-v1) | [NVIDIA R&D Model](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-internal-scientific-research-and-development-model-license/) |

By default, we recommend using the models trained on the full Bones Rigplay 1 dataset (700 hours of mocap) for your motion generation needs.
The models trained on BONES-SEED use 288 hours of [publicly available mocap data](https://huggingface.co/datasets/bones-studio/seed) so are less capable, but are useful for comparing to other models trained on BONES-SEED. To easily compare motion generation models to Kimodo, check out our [Motion Generation Benchmark](#kimodo-motion-generation-benchmark).

### Changes in v1.1
The latest v1.1 Kimodo-SOMA models were released primarily for compatibility with our new [Motion Generation Benchmark](#kimodo-motion-generation-benchmark), but also contain minor quality improvements over v1. For details on these improvements, please see the Hugging Face pages for [Kimodo-SOMA-RP-v1.1](https://huggingface.co/nvidia/Kimodo-SOMA-RP-v1.1#changes-in-v11) and [Kimodo-SOMA-SEED-v1.1](https://huggingface.co/nvidia/Kimodo-SOMA-SEED-v1.1#changes-in-v11).

## Getting Started

Please see the full documentation for detailed installation instructions, how to use the CLI and Interactive Demo, and other practical tips for generating motions with Kimodo:

**[Full Documentation](https://research.nvidia.com/labs/sil/projects/kimodo/docs)**
- [Quick Start Guide](https://research.nvidia.com/labs/sil/projects/kimodo/docs/getting_started/quick_start.html)
- [Installation Instructions](https://research.nvidia.com/labs/sil/projects/kimodo/docs/getting_started/installation.html)
- [Interactive Motion Authoring Demo](https://research.nvidia.com/labs/sil/projects/kimodo/docs/interactive_demo/index.html)
- [Command-Line Interface](https://research.nvidia.com/labs/sil/projects/kimodo/docs/user_guide/cli.html)
- [Benchmark Instructions](https://research.nvidia.com/labs/sil/projects/kimodo/docs/benchmark/introduction.html)
- [API Reference](https://research.nvidia.com/labs/sil/projects/kimodo/docs/api_reference/index.html)

**Before getting started** with motion generation, please review the [best practices](https://research.nvidia.com/labs/sil/projects/kimodo/docs/key_concepts/limitations.html) and be aware of [model limitations](https://research.nvidia.com/labs/sil/projects/kimodo/docs/key_concepts/limitations.html#limitations).


Some notes on installation environment:
- Kimodo requires ~17GB of VRAM to generate locally entirely on GPU, primarily due to the text embedding model. If you have a smaller card, set `TEXT_ENCODER_DEVICE=cpu` when running Kimodo commands to force text encoding to the CPU. This is slightly slower but reduces VRAM usage to <3 GB.
- The model has been most extensively tested on GeForce RTX 3090, GeForce RTX 4090, and NVIDIA A100 GPUs, but should work on other recent cards with sufficient VRAM
- This repo was developed on Linux, though Windows should work especially if using Docker

### DGX Spark / ARM64 Installation

Kimodo can run natively on NVIDIA DGX Spark (Grace ARM64 CPU and Blackwell GPU). The bundled
MotionCorrection extension uses [SIMDe](https://github.com/simd-everywhere/simde) on ARM64 to map
its SSE/AVX intrinsic API to ARM NEON. CUDA model inference continues to run on the Blackwell GPU.

The following source installation flow has been validated on DGX Spark with Python 3.12,
PyTorch built for CUDA 13.0, and an NVIDIA GB10 GPU:

```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake libsimde-dev

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
```

Install a CUDA-enabled AArch64 build of PyTorch that is compatible with the CUDA stack installed
on your DGX Spark. Verify that PyTorch can see the Blackwell GPU before installing Kimodo:

```bash
python -c "import torch; print(torch.__version__, torch.version.cuda); print(torch.cuda.get_device_name(0))"
```

ScenePic 1.1.2 does not currently provide an AArch64 wheel on PyPI, and its PyPI source archive
is missing a generated JavaScript build artifact. Install the same release from its official
source tag before installing Kimodo:

```bash
python -m pip install "scenepic @ git+https://github.com/microsoft/scenepic.git@v1.1.2"
python -m pip install -e .
```

Confirm the installation and CUDA execution:

```bash
python -m pip check
python -c "import kimodo, motion_correction, torch; x = torch.tensor([1.0]).cuda(); print(torch.cuda.get_device_name(0), x.item())"
```

`pip check` should report `No broken requirements found`. If CMake reports that SIMDe headers
are missing, confirm that `libsimde-dev` is installed on the host where `pip install` is running.

## Interactive Motion Authoring Demo

<div align="center">
  <img src="assets/demo_screenshot.png" width="1000">
</div>

</br>

**[Demo Documentation and Tutorial](https://research.nvidia.com/labs/sil/projects/kimodo/docs/interactive_demo/index.html)**

The web-based interactive demo provides an intuitive interface for generating motions with any of the Kimodo model variations. After installation, the demo can be launched with the `kimodo_demo` command. It runs locally on http://127.0.0.1:7860. Open this URL in your browser to access the interface (or use port forwarding if set up on a server).

### Demo Features
- **Multiple Characters**: Supports generating with the SOMA, G1, and SMPL-X versions of Kimodo
- **Text Prompts**: Enter one or more natural language descriptions of desired motions on the timeline
- **Timeline Editor**: Add and edit keyframes and constrained intervals on multiple constraint tracks
- **Constraint Types**:
  - Full-Body: Complete joint position constraints at specific frames
  - 2D Root: Define waypoints or full paths to follow on the ground plane
  - End-Effectors: Control hands and feet positions/rotations
- **Constraint Editing**: Editing mode allows for re-posing of constraints or adjusting waypoints
- **3D Visualization**: Real-time rendering of generated motions with skeleton and skinned mesh options
- **Playback Controls**: Preview generated motions with adjustable playback speed
- **Multiple Samples**: Generate and compare multiple motion variations
- **Examples**: Load pre-existing examples to better understand Kimodo's capabilities
- **Export**: Save constraints and generated motions for later use

## Command-Line Interface

**[CLI Documentation and Examples](https://research.nvidia.com/labs/sil/projects/kimodo/docs/user_guide/cli.html)**

Motions can also be generated directly from the command line with the `kimodo_gen` command or by running `python -m kimodo.scripts.generate` directly.

**Key Arguments:**
- `prompt`: A single text description or sequence of texts for the desired motion (required)
- `--model`: Which Kimodo model to use for generation
- `--duration`: Motion duration in seconds
- `--num_samples`: Number of motion variations to generate
- `--constraints`: Constraint file to control the generated motion (e.g., saved from the web demo)
- `--diffusion_steps`: Number of denoising steps
- `--cfg_type` / `--cfg_weight`: Classifier-free guidance (`nocfg`, `regular` with one weight, or `separated` with two weights for text vs. constraints); see the [CLI docs](https://research.nvidia.com/labs/sil/projects/kimodo/docs/user_guide/cli.html#classifier-free-guidance-cfg)
- `--no-postprocess`: Flag to disable foot skate and constraint cleanup post-processing
- `--seed`: Random seed for reproducible results

The script supports different output formats depending on which skeleton is used. By default, a custom NPZ format is saved that is compatible with the web demo.
For Kimodo-G1 models, the motion can be saved in the standard MuJoCo qpos CSV format.
For Kimodo-SMPLX, motion can be saved in the standard AMASS npz format for compability with existing pipelines.

### Default NPZ Output Format
Generated motions are saved as NPZ files containing:
- `posed_joints`: Global joint positions `[T, J, 3]`
- `global_rot_mats`: Global joint rotation matrices `[T, J, 3, 3]`
- `local_rot_mats`: Local (parent-relative) joint rotation matrices `[T, J, 3, 3]`
- `foot_contacts`: Foot contact labels [left heel, left toe, right heel, right toes] `[T, 4]`
- `smooth_root_pos`: Smoothed root representations outputted from the model `[T, 3]`
- `root_positions`: The (non-smoothed) trajectory of the actual root joint (e.g., pelvis) `[T, 3]`
- `global_root_heading`: The heading direction output from the model `[T, 2]`

`T` the number of frames and `J` the number of joints.

## Low-Level Python API

**[Model API Documentation](https://research.nvidia.com/labs/sil/projects/kimodo/docs/api_reference/model.html#kimodo.model.kimodo_model.Kimodo.__call__)**

For maximum flexibility, the low-level model inference API can be called directly, rather than going through our high-level CLI.
This allows for advanced model configuration including classifier-free guidance weights and parameters related to transitions in multi-prompt sequences.

## Downstream Robotics Applications of Kimodo

### Visualizing G1 Motions with MuJoCo

<div align="center">
  <img src="assets/mujoco_result.gif" width="800">
</div>

After generating motions on the G1 robot skeleton and saving to the MuJoCo qpos CSV file format, they can be easily used and visualized within MuJoCo.
A minimal visualization script is available with:
```
python -m kimodo.scripts.mujoco_load
```
Make sure to edit the script to correctly point to your CSV file and install Mujoco before running this.

### Tracking Generated Motions with ProtoMotions

<div align="center">
  <img src="assets/protomotions_results.gif" width="1280">
</div>

[ProtoMotions](https://github.com/NVlabs/ProtoMotions) is a GPU-accelerated simulation and learning framework for training physically simulated digital humans and humanoid robots. The Kimodo NPZ and CSV output formats are both compatible with ProtoMotions making it easy to train physics-based policies with generated motions from Kimodo. ProtoMotions supports outputs on both the SOMA skeleton and Unitree G1

After generating motions with Kimodo, head over to the [ProtoMotions docs](https://github.com/NVlabs/ProtoMotions?tab=readme-ov-file#-motion-authoring-with-kimodo) to see how to import them.

### Retargeting Motions to Other Robots with GMR

<div align="center">
  <img src="assets/gmr_results.gif" width="1280">
</div>

Motions generated by Kimodo-SMPLX can be retargeted to other robots using [General Motion Retargeting (GMR)](https://github.com/YanjieZe/GMR).
GMR supports the AMASS NPZ format out of the box, so simply generate motions with Kimodo and use `--output` to save; the AMASS NPZ is written to `stem_amass.npz` (single sample) or in the output folder (multiple samples). Then, use the [SMPL-X to Robot script](https://github.com/YanjieZe/GMR?tab=readme-ov-file#retargeting-from-smpl-x-amass-omomo-to-robot) in GMR to retarget to any supported robot. For example:
```
# run within GMR codebase
python scripts/smplx_to_robot.py --smplx_file /path/to/saved/amass_format.npz --robot booster_t1
```

### Combining Kimodo with GEAR-SONIC

<div align="center">
  <img src="assets/sonic_kimodo_demo.gif" width="800">
</div>

As a proof of concept, we have also incorporated Kimodo into the [interactive GEAR-SONIC demo](https://nvlabs.github.io/GEAR-SONIC/demo.html). In the demo, Kimodo can be used to generate a kinematic motion on the G1 robot skeleton, then GEAR-SONIC tracks the motion in simulation.

## Kimodo Motion Generation Benchmark

[**[Benchmark Documentation](https://research.nvidia.com/labs/sil/projects/kimodo/docs/benchmark/introduction.html)**]
[**[Test Suite on Hugging Face](https://huggingface.co/datasets/nvidia/Kimodo-Motion-Gen-Benchmark)**]

Alongside the Kimodo models, we provide a benchmark designed to standardize evaluation for motion generation models with a comprehensive set of test cases. This includes:

* **Evaluation Data**: A suite of test cases [available on Hugging Face](https://huggingface.co/datasets/nvidia/Kimodo-Motion-Gen-Benchmark) is used in concert with the [BONES-SEED](https://huggingface.co/datasets/bones-studio/seed) dataset to construct the full benchmark. 
* **Diverse Test Cases**: Test cases cover a wide range of text-conditioned and constraint-conditioned motion generation.
* **Evaluation Pipeline**: Code for the full evaluation pipeline including benchmark construction, motion generation, and evaluation.
* **Metrics**: Several metrics to evaluate generated motions that cover motion quality, constraint following, and text alignment. Our [TMR-SOMA-RP-v1](https://huggingface.co/nvidia/TMR-SOMA-RP-v1) model trained on all 700 hours of the Bones Rigplay dataset is a powerful embedding model to compute common metrics like R-precision and FID.

To facilitate future research, we [report benchmark results](https://research.nvidia.com/labs/sil/projects/kimodo/docs/benchmark/results.html) for Kimodo-SOMA-v1.1 models, which are reproducible and easily comparable to other methods trained on the BONES-SEED data. 

## Timeline Annotations for BONES-SEED

As detailed in the [tech report](https://research.nvidia.com/labs/sil/projects/kimodo/assets/kimodo_tech_report.pdf), Kimodo is trained using fine-grained temporal text annotations of mocap clips.
While the full [Rigplay 1](https://bones.studio/datasets#rp01) dataset is proprietary, we have released the temporal segmentations for the public [BONES-SEED](https://huggingface.co/datasets/bones-studio/seed) subset.
These annotations are already included in the BONES-SEED dataset, but the standalone labels and additional information about them is [available on HuggingFace](https://huggingface.co/datasets/nvidia/SEED-Timeline-Annotations).


## Related Humanoid Work at NVIDIA
Kimodo is part of a larger effort to enable humanoid motion data for robotics, physical AI, and other applications.

Check out these related works:
* [ARDY](https://github.com/nv-tlabs/ardy) - builds on top of Kimodo to enable real-time controllable motion generation for interactive applications
* [MotionBricks](https://nvlabs.github.io/motionbricks/) - real-time motion generation framework that specializes in fast and robust motion in-betweening
* [SOMA Body Model](https://github.com/NVlabs/SOMA-X) - a unified parameteric human body model
* [BONES-SEED Dataset](https://huggingface.co/datasets/bones-studio/seed) - a large scale human(oid) motion capture dataset in SOMA and G1 format
* [ProtoMotions](https://github.com/NVlabs/ProtoMotions) - simulation and learning framework for training physically simulated human(oid)s
* [SOMA Retargeter](https://github.com/NVIDIA/soma-retargeter) - SOMA to G1 retargeting tool
* [GEM](https://github.com/NVlabs/GEM-X) - human motion reconstruction from video
* [GEAR SONIC](https://github.com/NVlabs/GR00T-WholeBodyControl) - humanoid behavior foundation model for physical robots

## Citation

If you use this code in your research, please cite:

```bibtex
@article{Kimodo2026,
  title={Kimodo: Scaling Controllable Human Motion Generation},
  author={Rempe, Davis and Petrovich, Mathis and Yuan, Ye and Zhang, Haotian and Peng, Xue Bin and Jiang, Yifeng and Wang, Tingwu and Iqbal, Umar and Minor, David and de Ruyter, Michael and Li, Jiefeng and Tessler, Chen and Lim, Edy and Jeong, Eugene and Wu, Sam and Hassani, Ehsan and Huang, Michael and Yu, Jin-Bey and Chung, Chaeyeon and Song, Lina and Dionne, Olivier and Kautz, Jan and Yuen, Simon and Fidler, Sanja},
  journal={arXiv:2603.15546},
  year={2026}
}
```

## License

This codebase is licensed under [Apache-2.0](LICENSE). Note that model checkpoints and data are licensed separately as indicated on the HuggingFace download pages.

This project will download and install additional third-party open source software projects. Review the license terms of these open source projects before use.

## Acknowledgments

This project builds upon excellent open-source projects:
- [Viser](https://github.com/nerfstudio-project/viser) for 3D motion authoring demo
- [LLM2Vec](https://github.com/McGill-NLP/llm2vec) for text encoding

## Contact

For questions or issues, please open an issue on this repository or reach out directly to the authors.

---
 
