from . import *

import json
from types import SimpleNamespace


class _FakeTextAsset:
    def __init__(self, name, script: bytes):
        self.m_Name = name
        self.m_Script = script.decode("utf-8", "surrogateescape")


class _FakeObject:
    def __init__(self, name, script: bytes):
        from UnityPy.enums import ClassIDType

        self.type = ClassIDType.TextAsset
        self._data = _FakeTextAsset(name, script)

    def read(self):
        return self._data


class _FakeEnv:
    def __init__(self, objects):
        self.objects = objects


def test_rla2json_archive_header_is_parsed(monkeypatch):
    """Regression: the RLH header is bytes but was indexed as a dict."""
    from sssekai.entrypoint import rla2json

    header = json.dumps(
        {"version": "1.0", "splitSeconds": 0, "splitFileIds": []}
    ).encode("utf-8")
    env = _FakeEnv([_FakeObject("sekai.rlh", header)])
    monkeypatch.setattr(rla2json, "load_assetbundle", lambda f: env)

    args = SimpleNamespace(
        input=sample_file_path("rla", "streaming_live_vbs_1-0_0.bin"),
        outdir=TEMP_DIR,
        strict=False,
    )
    # Should not raise; no split files means nothing is dumped.
    rla2json.main_rla2json(args)


def test_rla2json_missing_header(monkeypatch):
    from sssekai.entrypoint import rla2json

    env = _FakeEnv([])
    monkeypatch.setattr(rla2json, "load_assetbundle", lambda f: env)

    args = SimpleNamespace(
        input=sample_file_path("rla", "streaming_live_vbs_1-0_0.bin"),
        outdir=TEMP_DIR,
        strict=False,
    )
    try:
        rla2json.main_rla2json(args)
    except AssertionError:
        pass
    else:
        raise AssertionError("missing RLH header should assert")
