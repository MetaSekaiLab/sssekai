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
Additionally, you can use the GUI version of `sssekai` by installing the `[gui]` extra, which in turn installs [GooeyEx](https://github.com/mos9527/GooeyEx/).

```bash
pip install -U "sssekai[gui]"
```
Then you can run the GUI version by:
```bash
sssekai-gui
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
