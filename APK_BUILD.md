# Building Android APK (WSL2) for ChatApp

This guide shows how to build the Kivy app APK using WSL2 (Ubuntu) on Windows.

Prerequisites
- WSL2 installed with Ubuntu (or other Linux distro)
- At least 8GB disk and 8GB RAM recommended for build

Steps
1. Open WSL2 shell and install system deps:

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv openjdk-11-jdk git build-essential libssl-dev libffi-dev
sudo apt install -y zip unzip zlib1g-dev libncurses5 libstdc++6
```

2. Install `buildozer` and `python-for-android` requirements:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install buildozer
```

3. Install Android SDK/NDK and other tools (Buildozer can handle this automatically on first run — it will download the SDK/NDK to `~/.buildozer`).

4. Prepare project in WSL workspace (ensure shared project files accessible in WSL). Then run:

```bash
cd /path/to/work/mobile
buildozer android debug
```

This will download SDK/NDK and perform the build. For release builds, see `buildozer android release` and follow signing instructions.

CI note
- Building an APK in CI requires a Linux runner with sufficient disk and RAM. You can use a self-hosted runner or a Docker image preconfigured with Buildozer.

Common issues
- If dependencies fail, inspect `~/.buildozer/android/platform` and check logs in `.buildozer/android/platform/*/build`.

If you want, I can create a GitHub Actions workflow that runs Buildozer on a self-hosted runner or generate a Dockerfile for a reproducible build environment.
