from . import *


def test_apphash():
    from sssekai.entrypoint.apphash import main_apphash

    result = main_apphash(
        NamedDict(
            {"ab_src": sample_file_path("apphash", "6350e2ec327334c8a9b7f494f344a761")}
        )
    )


def test_abserve_host_defaults_to_loopback():
    """abserve used to bind 0.0.0.0, exposing the local cache to the LAN."""
    from sssekai.__main__ import create_parser

    parser = create_parser()
    args = parser.parse_args(["abserve"])
    assert args.host == "127.0.0.1"


if __name__ == "__main__":
    test_apphash()
