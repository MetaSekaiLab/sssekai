from . import *

import base64
import dataclasses
import json

SECRET = "SUPER_SECRET_JWT_TOKEN_1234567890"


def _fake_jwt(user_id=1, signature="sig"):
    payload = base64.b64encode(json.dumps({"userId": user_id}).encode()).decode()
    return "e30." + payload.rstrip("=") + "." + signature


def _make_cache(credential=SECRET):
    from sssekai.abcache import AbCache, AbCacheConfig

    return AbCache(
        AbCacheConfig("jp", "1.0.0", "android", "hash", auth_credential=credential)
    )


def _make_secret_cache():
    """Credential + cached headers both carry the secret."""
    cache = _make_cache(_fake_jwt())
    cache.config.auth_credential = SECRET
    cache.database.cached_headers["X-Session-Token"] = SECRET
    cache.database.cached_headers["Cookie"] = SECRET
    return cache


def test_config_repr_hides_credential():
    cache = _make_cache()
    assert SECRET not in repr(cache.config)
    assert SECRET not in repr(cache)


def test_user_data_repr_hides_tokens():
    from sssekai.abcache import (
        SekaiUserAuthData,
        SekaiUserData,
        SekaiUserRegistrationData,
    )

    user = SekaiUserData(
        userRegistration=SekaiUserRegistrationData(userId=1),
        credential=SECRET,
        sessionToken=SECRET,
    )
    auth = SekaiUserAuthData(
        sessionToken=SECRET,
        appVersion="1.0.0",
        multiPlayVersion="1.0.0",
        dataVersion="1.0.0",
        assetVersion="1.0.0",
    )
    assert SECRET not in repr(user)
    assert SECRET not in repr(auth)


def test_database_repr_and_asdict_hide_cached_headers():
    cache = _make_secret_cache()
    assert SECRET not in repr(cache.database)
    asdict = dataclasses.asdict(cache.database)
    assert SECRET not in repr(asdict)
    # asdict's secret-free view must still cover the token-bearing field.
    assert "cached_headers" in asdict


def test_legacy_plain_dict_headers_are_normalized_on_load(caplog):
    """Caches written by older versions store a plain dict in cached_headers,
    and save() replaces that field with the live session headers. So the token
    must be put on the session headers to actually reach the cache file."""
    import io
    import pickle

    caplog.set_level(DEBUG)
    cache = _make_secret_cache()
    cache.headers["X-Session-Token"] = SECRET
    cache.headers["Cookie"] = SECRET
    buf = io.BytesIO()
    cache.save(buf)
    buf.seek(0)
    # Round-trip the raw pickle with the header field demoted to a plain dict,
    # exactly as an older sssekai wrote it.
    database = pickle.load(buf)
    database.cached_headers = dict(database.cached_headers)
    assert SECRET in repr(database.cached_headers)
    buf = io.BytesIO(pickle.dumps(database))
    from sssekai.abcache import AbCache, RedactedHeaders

    loaded = AbCache.from_file(buf)
    assert isinstance(loaded.database.cached_headers, RedactedHeaders)
    assert dict(loaded.database.cached_headers)["X-Session-Token"] == SECRET
    assert SECRET not in repr(loaded.database)
    assert SECRET not in repr(dataclasses.asdict(loaded.database))
    assert SECRET not in caplog.text


def test_save_and_load_do_not_log_credential(caplog):
    import io

    from sssekai.abcache import AbCache

    cache = _make_secret_cache()
    # Put the tokens where save() actually persists them: _update_request_
    # headers() copies the live session headers over database.cached_headers.
    cache.headers["X-Session-Token"] = SECRET
    cache.headers["Cookie"] = SECRET
    caplog.clear()
    caplog.set_level(DEBUG)
    buf = io.BytesIO()
    cache.save(buf)
    buf.seek(0)
    AbCache.from_file(buf)
    assert SECRET not in caplog.text
    # The secret must have been present, otherwise this passes vacuously.
    assert SECRET in dict(cache.headers).values()


def test_session_headers_are_redacted_after_load():
    import io

    from sssekai.abcache import AbCache, RedactedSessionHeaders

    cache = _make_secret_cache()
    cache.headers["X-Session-Token"] = SECRET
    cache.headers["Cookie"] = SECRET
    buf = io.BytesIO()
    cache.save(buf)
    buf.seek(0)
    loaded = AbCache.from_file(buf)
    assert isinstance(loaded.headers, RedactedSessionHeaders)
    assert SECRET not in repr(loaded.headers)
    assert SECRET not in repr(vars(loaded))
    # Values must survive intact so authentication keeps working.
    assert loaded.headers["X-Session-Token"] == SECRET


def test_redact_secrets_rewraps_user_data_from_disk():
    """redact_secrets() must re-wrap sekai_user_data/sekai_user_auth_data:
    pickle restores dataclasses without going through __setattr__, so their
    secret fields come back as plain str and would leak through repr."""
    import io
    import pickle

    from sssekai.abcache import (
        AbCache,
        RedactedStr,
        SekaiUserAuthData,
        SekaiUserData,
        SekaiUserRegistrationData,
    )

    cache = _make_secret_cache()
    buf = io.BytesIO()
    cache.save(buf)
    buf.seek(0)
    database = pickle.load(buf)
    # A real cache round-trips the dataclasses; their fields are plain str.
    database.sekai_user_data = SekaiUserData(
        userRegistration=SekaiUserRegistrationData(userId=1),
        credential=SECRET,
        sessionToken=SECRET,
    )
    database.sekai_user_auth_data = SekaiUserAuthData(
        sessionToken=SECRET,
        appVersion="1.0.0",
        multiPlayVersion="1.0.0",
        dataVersion="1.0.0",
        assetVersion="1.0.0",
    )
    # Undo the __setattr__ wrapping to mimic what pickle hands back.
    object.__setattr__(database.sekai_user_data, "credential", SECRET)
    object.__setattr__(database.sekai_user_data, "sessionToken", SECRET)
    object.__setattr__(database.sekai_user_auth_data, "sessionToken", SECRET)
    assert type(database.sekai_user_data.credential) is str
    assert SECRET in repr(dataclasses.asdict(database))

    buf = io.BytesIO(pickle.dumps(database))
    loaded = AbCache.from_file(buf)
    assert isinstance(loaded.database.sekai_user_data.credential, RedactedStr)
    assert isinstance(loaded.database.sekai_user_data.sessionToken, RedactedStr)
    assert isinstance(loaded.database.sekai_user_auth_data.sessionToken, RedactedStr)
    assert SECRET not in repr(dataclasses.asdict(loaded.database))
    # Values must remain usable, not just hidden.
    assert loaded.database.sekai_user_data.credential == SECRET
    assert loaded.database.sekai_user_auth_data.sessionToken == SECRET


def test_save_wraps_cached_headers_so_asdict_does_not_leak():
    import io

    from sssekai.abcache import RedactedHeaders

    cache = _make_secret_cache()
    cache.headers["X-Session-Token"] = SECRET
    buf = io.BytesIO()
    cache.save(buf)
    assert isinstance(cache.database.cached_headers, RedactedHeaders)
    assert SECRET not in repr(dataclasses.asdict(cache.database))


def test_legacy_dict_auth_data_is_normalized_on_load():
    """Caches from older versions may hold plain dicts for the auth fields;
    load() must turn them into dataclasses so attribute access and redaction
    both work."""
    import io
    import pickle

    from sssekai.abcache import AbCache, SekaiUserAuthData

    cache = _make_secret_cache()
    buf = io.BytesIO()
    cache.save(buf)
    buf.seek(0)
    database = pickle.load(buf)
    database.sekai_user_auth_data = {
        "sessionToken": SECRET,
        "appVersion": "1.0.0",
        "multiPlayVersion": "1.0.0",
        "dataVersion": "1.0.0",
        "assetVersion": "1.0.0",
    }
    buf = io.BytesIO(pickle.dumps(database))
    loaded = AbCache.from_file(buf)
    assert isinstance(loaded.database.sekai_user_auth_data, SekaiUserAuthData)
    assert loaded.database.sekai_user_auth_data.sessionToken == SECRET
    assert SECRET not in repr(dataclasses.asdict(loaded.database))


def test_registered_user_data_is_dataclass_and_not_leaked(caplog, monkeypatch):
    from sssekai.abcache import SekaiUserData
    from sssekai.abcache.auth import register_as_anonymous_user_sega

    cache = _make_cache(credential=None)
    cache.headers["X-Platform"] = "Android"
    cache.headers["X-DeviceModel"] = "test"
    cache.headers["X-OperatingSystem"] = "Android"

    monkeypatch.setattr(cache, "_update_request_headers", lambda: None)
    monkeypatch.setattr(cache, "update_signatures", lambda: None)
    monkeypatch.setattr(cache, "request_packed", lambda *a, **kw: object())
    monkeypatch.setattr(
        cache,
        "response_to_dict",
        lambda resp: {
            "credential": _fake_jwt(signature=SECRET),
            "userRegistration": {"userId": 1},
        },
    )

    caplog.clear()
    caplog.set_level(DEBUG)
    register_as_anonymous_user_sega(cache)
    assert isinstance(cache.database.sekai_user_data, SekaiUserData)
    # The credential must really be present, otherwise the assertions below
    # would pass vacuously.
    assert SECRET in cache.database.sekai_user_data.credential
    asdict = dataclasses.asdict(cache.database)
    assert SECRET not in repr(cache.database)
    assert SECRET not in repr(asdict)
    assert SECRET not in caplog.text


def test_legacy_dict_user_data_is_normalized_and_redacted(caplog):
    """sssekai <= 0.8.2 stored the raw API response dict in sekai_user_data."""
    import io
    import pickle

    from sssekai.abcache import AbCache, AbCacheConfig, SekaiUserData

    SECRET_LOCAL = "LEGACY_CREDENTIAL_XYZ"
    cache = AbCache(AbCacheConfig("jp", "1", "android", "h"))
    cache.database.sekai_user_data = {
        "credential": SECRET_LOCAL,
        "userRegistration": {"userId": 1},
    }
    buf = io.BytesIO()
    pickle.dump(cache.database, buf)
    buf.seek(0)

    caplog.clear()
    caplog.set_level(DEBUG)
    loaded = AbCache.from_file(buf)
    assert isinstance(loaded.database.sekai_user_data, SekaiUserData)
    assert loaded.SEKAI_CREDENTIAL == SECRET_LOCAL
    assert SECRET_LOCAL not in repr(loaded.database)
    assert SECRET_LOCAL not in repr(dataclasses.asdict(loaded.database))
    assert SECRET_LOCAL not in caplog.text
