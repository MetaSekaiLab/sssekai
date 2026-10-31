import base64, logging, os, shutil, struct, zlib

logger = logging.getLogger(__name__)


METADATA_MAGIC = b"\xaf\x1b\xb1\xfa"
SIG_DW_OP_piece = b"DW_OP_piece not implemented\x00x5\x00x10\x00"
METADATA_SENTINEL = bytes.fromhex("56 be f0 89 c2 53 89 f0")
# CRC32 preimages for the shared CN/TW/KR metadata key, encoded as Base85.
METADATA_KEY_TABLE = (
    b"4{ka2D9U8<D3B0mEYp;8J7Qd;wH`O7{VwF%dD5L>zd^_G49^q|*IVv2^^*<5M}i3p08F2`$|<5cSKBjt"
    b"-c#QNC!#le@Z?nJYuTl$l+vFYbd^<?0r0X(mE7iYKOz-(4CiGk0PyzZ`T&ch^t{OvNM0VUEk!0|xMsl1"
    b"x(3lH1&wmvgSNc^z#r+KDY9Kl6yH6}6sD0la@!K@Q1(C=DHE6OlmptC;it&&>O#YQASqu%0KHu2#Tw_F"
    b"Ik<=nB~|T}#pX``lt%iYtL)MJw2F~%n5@6_#Ay=x{XXx<SxUAN<|<wU1~!28b9kLj7!Q2MDHXwztHC72"
    b"c<$7=!u;|w`=D&oegJ;3P}kR^NbgTuXSp)ZX_OvN^t7Cb-1Prh2SDW*y<fy4ei^@1{BzScsl&X%z@K9q"
    b"kUHR5rICl7ENcozikTt`@tf%%K?v;BkR{x_CM_rqEDQYKZgJ+)3004HLavSYu!|w6_O>gP#&`golJFnc"
    b"7XbA+yX9R05e%fk)u%Q!G{%2VfHX%N+3MRH*?6vY7p7Udu@irL@8%{Na%5|m&v-{Dd4}PjtsDX;Skyst"
    b"&>wtjmTj>t@;Vp{lfSPpC5ibtfDfCWr3R81Mcb+?Si8AuGeT6#Oa-hjr}=DC-5<Qlhoc_HEgV5ZNQ+l_"
)


def decrypt_metadata(metadata, binary):
    if metadata[:8] == METADATA_SENTINEL:
        logger.info("Detected CN/TW/KR metadata format")
        metadata = metadata[8:]
        if len(metadata) < 0x20 or metadata[:8] != METADATA_MAGIC + struct.pack("<I", 31):
            raise ValueError("Unsupported prefixed metadata header or version")
        offset, size = struct.unpack_from("<II", metadata, 0x18)
        if offset + size > len(metadata):
            raise ValueError("Metadata XOR region out of range")
        preimages = base64.b85decode(METADATA_KEY_TABLE)
        key = [struct.pack("<I", zlib.crc32(preimages[i:i + 4]))
               for i in range(0, len(preimages), 4)]
        for i in range(0, size, 4):
            word = key[((i & 0xFF) + ((i >> 7) & 0xFF)) & 0x7F]
            for j in range(min(4, size - i)):
                metadata[offset + i + j] ^= word[j]
        return metadata
    assert (
        metadata[:4] != METADATA_MAGIC
    ), "Metadata file is unlikely to be protected with XOR cipher (non-obfuscated header)"
    try:
        import lief
    except ImportError as e:
        logger.error(
            "Please install sssekai[il2cpp] through your Python package manager to use the il2cpp entrypoint"
        )
        raise e
    logger.info("Loading binary from %s", binary)
    elf = lief.ELF.parse(binary)
    text: lief.ELF.Section = elf.get_section(".rodata")
    text = text.content.tobytes()
    # Yes - the heuristic is *that* simple.
    # We're probably fine if Unity never changes their bundled NDK for JP
    # Verified to work with JP 3.8.1 & 5.5.0
    off = text.find(SIG_DW_OP_piece)
    assert (
        off != -1
    ), "Unsupported metadata format: key signature not found in the binary"
    off += len(SIG_DW_OP_piece)
    key = text[off : off + 0x80]
    logger.info("Detected whole-file XOR metadata format (JP/EN)")
    for i in range(0, len(metadata)):
        metadata[i] ^= key[i & 0x7F]
        if i == 4:
            assert metadata[:4] == METADATA_MAGIC, "Metadata deobfuscation failed"
    return metadata


def main_il2cpp(args):
    logger.info("Loading metadata from %s", args.metadata)
    metadata = bytearray(open(args.metadata, "rb").read())
    if len(metadata) < 8:
        raise ValueError("Metadata file is too small")
    metadata = decrypt_metadata(metadata, args.binary)
    logger.info("Saving files to %s", args.outdir)
    os.makedirs(args.outdir, exist_ok=True)
    with open(os.path.join(args.outdir, "global-metadata.dat"), "wb") as f:
        f.write(metadata)
    shutil.copy(args.binary, os.path.join(args.outdir, "il2cpp.so"))
