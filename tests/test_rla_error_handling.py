from . import *

import binascii

# --- Packet builders -------------------------------------------------------
# RTVL wire format: "RTVL" + 6 hex total length + base64 flag + split flag +
# 3 digit signature + body. Split bodies start with five zero-padded decimal
# fields: splitId(5) splitIndex(5) splitNum(5) dataLength(10) totalDataLength(10).
# A non-split body is signature + 5 byte payload header + streaming data; the
# 5 byte header's first byte after the signature selects raw vs gzip decoding.


def _split_packet(sid, idx, num, declared_total, payload, b64=True, sig=2):
    info = b"%05d%05d%05d%010d%010d" % (
        sid,
        idx,
        num,
        len(payload),
        declared_total,
    )
    body = info + payload
    total = len(body) + 15
    flag = b"T" if b64 else b"F"
    return b"RTVL" + b"%06X" % total + flag + b"T" + b"%03d" % sig + body


def _payload_body(streaming_payload, sig=0):
    """Body of a non-split packet: decoder signature + streaming payload."""
    return bytes([sig]) + b"\x01\x00\x00\x00" + streaming_payload


def _payload_packet(streaming_payload, sig=0):
    body = _payload_body(streaming_payload, sig)
    total = len(body) + 15
    return b"RTVL" + b"%06X" % total + b"F" + b"F" + b"%03d" % sig + body


VALID_PAYLOAD = b"\x08\x00\x00\x00" + b"\x00\x00\x00\x00" + b"\x02\x00" + b"\x00\x00"
# pose count = 0x7fffffff with no pose data -> array reader hits EOF
TRUNCATED_PAYLOAD = (
    b"\x08\x00\x00\x00" + b"\x7f\xff\xff\xff" + b"\x02\x00" + b"\x00\x0c"
)


# --- Non-split packets -----------------------------------------------------


def test_rla_garbage_is_skipped_when_not_strict():
    from sssekai.fmt.rla import read_rla_frames

    frames = list(read_rla_frames([(1, b"GARBAGE")], (1, 6), strict=False))
    assert frames == []


def test_rla_garbage_raises_when_strict():
    from sssekai.fmt.rla import read_rla_frames

    try:
        list(read_rla_frames([(1, b"GARBAGE")], (1, 6), strict=True))
    except AssertionError:
        pass
    else:
        raise AssertionError("strict mode should raise on malformed packets")


def test_rla_payload_failure_is_skipped_when_not_strict(monkeypatch):
    """A valid RTVL header with an undecodable payload must not abort the stream."""
    from sssekai.fmt import rla

    packet = _payload_packet(VALID_PAYLOAD)
    calls = {"n": 0}

    def fake_decode_payload(buffer):
        calls["n"] += 1
        raise ValueError("cannot decode payload")

    monkeypatch.setattr(rla, "decode_buffer_payload", fake_decode_payload)
    frames = list(rla.read_rla_frames([(1, packet)], (1, 6), strict=False))
    assert frames == []
    assert calls["n"] == 1


def test_rla_payload_failure_raises_when_strict(monkeypatch):
    from sssekai.fmt import rla

    def fake_decode_payload(buffer):
        raise ValueError("cannot decode payload")

    monkeypatch.setattr(rla, "decode_buffer_payload", fake_decode_payload)
    packet = _payload_packet(VALID_PAYLOAD)
    try:
        list(rla.read_rla_frames([(1, packet)], (1, 6), strict=True))
    except ValueError:
        pass
    else:
        raise AssertionError("strict mode should propagate payload errors")


def test_rla_truncated_payload_raises_truncated_error():
    """Truncation is reported distinctly so callers can tell it from corruption."""
    from sssekai.fmt.rla import StreamingDataTruncatedException, decode_streaming_data

    try:
        decode_streaming_data((1, 6), 0, TRUNCATED_PAYLOAD, strict=False)
    except StreamingDataTruncatedException:
        pass
    else:
        raise AssertionError(
            "truncated payload should raise StreamingDataTruncatedException"
        )


def test_rla_truncated_payload_drops_frame_but_keeps_stream():
    from sssekai.fmt.rla import read_rla_frames

    packets = [
        (1, _payload_packet(VALID_PAYLOAD)),
        (2, _payload_packet(TRUNCATED_PAYLOAD)),
    ]
    frames = list(read_rla_frames(packets, (1, 6), strict=False))
    assert [(tick, f["type"]) for tick, f in frames] == [(1, "MotionData")]


# --- Split packets ---------------------------------------------------------


def test_rla_split_bad_base64_skipped_when_not_strict():
    from sssekai.fmt.rla import read_rla_frames

    # "abcde" is not valid base64 (length 5 mod 4 == 1)
    packet = _split_packet(1, 0, 1, 5, b"abcde", b64=True)
    assert list(read_rla_frames([(1, packet)], (1, 6), strict=False)) == []


def test_rla_split_bad_base64_raises_when_strict():
    from sssekai.fmt.rla import read_rla_frames

    packet = _split_packet(1, 0, 1, 5, b"abcde", b64=True)
    try:
        list(read_rla_frames([(1, packet)], (1, 6), strict=True))
    except binascii.Error:
        pass
    else:
        raise AssertionError("strict mode should raise on malformed split base64")


def test_rla_split_length_mismatch_skipped_when_not_strict():
    from sssekai.fmt.rla import read_rla_frames

    packet = _split_packet(1, 0, 1, 999, b"abcdef", b64=False)
    assert list(read_rla_frames([(1, packet)], (1, 6), strict=False)) == []


def test_rla_split_length_mismatch_raises_when_strict():
    from sssekai.fmt.rla import read_rla_frames

    packet = _split_packet(1, 0, 1, 999, b"abcdef", b64=False)
    try:
        list(read_rla_frames([(1, packet)], (1, 6), strict=True))
    except AssertionError as e:
        assert "incomplete split packet" in str(e)
    else:
        raise AssertionError("strict mode should assert on split length mismatch")


def test_rla_split_group_is_cleared_after_skip():
    """A discarded group must not bleed into a later packet with the same id."""
    from sssekai.fmt.rla import read_rla_frames

    bad = _split_packet(7, 0, 1, 999, b"abcdef", b64=False)
    good_body = _payload_body(VALID_PAYLOAD)
    good = _split_packet(7, 0, 1, len(good_body), good_body, b64=False, sig=0)
    frames = list(read_rla_frames([(1, bad), (2, good)], (1, 6), strict=False))
    assert [(tick, f["type"]) for tick, f in frames] == [(2, "MotionData")]


def test_rla_split_reassembles_in_index_order():
    from sssekai.fmt.rla import read_rla_frames

    body = _payload_body(VALID_PAYLOAD)
    half = len(body) // 2
    p0 = _split_packet(3, 0, 2, len(body), body[:half], b64=False, sig=0)
    p1 = _split_packet(3, 1, 2, len(body), body[half:], b64=False, sig=0)
    # Delivered out of order; reassembly sorts by splitIndex.
    frames = list(read_rla_frames([(2, p1), (1, p0)], (1, 6), strict=False))
    assert [f["type"] for _, f in frames] == ["MotionData"]
