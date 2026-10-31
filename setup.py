import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import setuptools, sssekai

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sssekai",
    version=sssekai.__version__,
    author="greats3an",
    author_email="greats3an@gmail.com",
    maintainer="MetaSekaiLab",
    description="Project SEKAI Asset Utility / PJSK 资源工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MetaSekaiLab/sssekai",
    project_urls={
        "Source": "https://github.com/MetaSekaiLab/sssekai",
        "Issues": "https://github.com/MetaSekaiLab/sssekai/issues",
    },
    packages=setuptools.find_packages(include=["sssekai", "sssekai.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[        
        "msgpack",
        "requests",
        "pycryptodome",     
        "unitypy >= 1.25.0, < 2.0.0",
        "tqdm",
        "coloredlogs",
        "fsspec",
    ],
    extras_require={"gui": ["GooeyEx>=0.1.1"], "il2cpp": ["lief"], "criware": ["PyCriCodecsEx"]},
    entry_points={
        "console_scripts": [
            "sssekai = sssekai.__main__:__main__",
            "sssekai-gui = sssekai.__gui__:__main__",
        ],
        "fsspec.specs": ["abcache = sssekai.abcache.fs.AbCacheFilesystem"],
    },
    python_requires=">=3.10",
)
