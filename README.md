# sssekai

本项目基于 [mos9527/sssekai](https://github.com/mos9527/sssekai)，由 [MetaSekaiLab](https://github.com/MetaSekaiLab) 继续维护。感谢原作者及历代贡献者。

[![Windows Build](https://github.com/MetaSekaiLab/sssekai/actions/workflows/python-publish.yml/badge.svg)](https://github.com/MetaSekaiLab/sssekai/actions/workflows/python-publish.yml) [![Releases](https://img.shields.io/github/downloads/MetaSekaiLab/sssekai/total.svg)](https://github.com/MetaSekaiLab/sssekai/releases/) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Command-line tool (w/Python API support) for Project SEKAI (JP: プロジェクトセカイ カラフルステージ！ feat.初音ミク) game assets.

# Installing & Updating
**Windows 用户**：请查看本仓库的 [Releases](https://github.com/MetaSekaiLab/sssekai/releases)。

Python >=3.10 is required to run this tool.

通过 PyPI 安装或更新：
```bash
pip install -U sssekai
```
To use the latest development version, you can install directly from GitHub:
```bash
pip install -U git+https://github.com/MetaSekaiLab/sssekai
```
## Using the GUI version
The GUI depends on [GooeyEx](https://github.com/mos9527/GooeyEx/), which is **not published on PyPI at all**. Install it from upstream (a `git` executable and network access are required), then run the GUI:

```bash
pip install -U "GooeyEx @ git+https://github.com/mos9527/GooeyEx"
sssekai-gui
```

If the import fails, check the installed version with `python -c "import GooeyEx; print(getattr(GooeyEx, '__version__', 'unknown'))"`. If git is unavailable, use the CLI executable from Releases instead.

To build the GUI executable yourself, install GooeyEx from a clone with its submodules (`git clone --recurse-submodules https://github.com/mos9527/GooeyEx`) so `GooeyEx/images` is populated, then run `pyinstaller sssekai-gui.spec`. Images pulled from a plain `pip install` are incomplete.

## Serving the cache (`abserve`)
`sssekai abserve` serves the local AssetBundle cache over HTTP. It binds to `127.0.0.1` by default; pass `--host 0.0.0.0` to expose it to your network (anyone who can reach the port can read the cache and its credentials).

```bash
sssekai abserve --db ~/.sssekai/abcache.db
```
# 问题反馈
使用问题和缺陷请提交至本仓库的 [Issues](https://github.com/MetaSekaiLab/sssekai/issues)。

# See Also
https://github.com/mos9527/sssekai_blender_io

# License
MIT

# References
- https://github.com/K0lb3/UnityPy
- https://mos9527.github.io/tags/project-sekai/
