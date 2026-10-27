"""Extract APK/XAPK inputs for the existing IL2CPP command."""

import shutil
import tempfile
import zipfile
from pathlib import Path
from types import SimpleNamespace

from .il2cpp import main_il2cpp


def main_il2cppextract(args):
    paths = {
        "lib/arm64-v8a/libil2cpp.so": "libil2cpp.so",
        "assets/bin/Data/Managed/Metadata/global-metadata.dat": "global-metadata.dat",
    }
    with tempfile.TemporaryDirectory() as temp:
        found = set()

        def unpack(apk):
            for entry in apk.infolist():
                if entry.filename not in paths:
                    continue
                if entry.filename in found:
                    raise ValueError(f"Multiple candidates for {entry.filename}")
                found.add(entry.filename)
                target = Path(temp) / paths[entry.filename]
                with apk.open(entry) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)

        with zipfile.ZipFile(args.infile) as archive:
            if Path(args.infile).suffix.lower() == ".xapk":
                for entry in archive.infolist():
                    if entry.is_dir() or not entry.filename.lower().endswith(".apk"):
                        continue
                    with tempfile.TemporaryFile() as nested:
                        with archive.open(entry) as src:
                            shutil.copyfileobj(src, nested)
                        nested.seek(0)
                        with zipfile.ZipFile(nested) as apk:
                            unpack(apk)
            else:
                unpack(archive)

        missing = paths.keys() - found
        if missing:
            raise ValueError(f"Missing APK files: {', '.join(sorted(missing))}")
        main_il2cpp(SimpleNamespace(
            metadata=str(Path(temp) / "global-metadata.dat"),
            binary=str(Path(temp) / "libil2cpp.so"),
            outdir=args.outdir,
        ))
