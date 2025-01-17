def test_settings(mocker, monkeypatch):
    def __open(file, *args, **kwargs):
        if str(file).startswith("/etc/lava-server/settings"):
            raise FileNotFoundError
        return open(file, *args, **kwargs)

    mocker.patch("io.open", __open)
    mocker.patch(
        "lava_server.settings.config_file.ConfigFile.load",
        side_effect=FileNotFoundError,
    )

    monkeypatch.setenv("LAVA_SETTINGS_HELLO", "world")
    monkeypatch.setenv(
        "LAVA_JSON_SETTINGS", "eyJXT1JLRVJfQVVUT19SRUdJU1RFUl9ORVRNQVNLIjogWyI6OjEiXX0="
    )
    import lava_server.settings.prod as settings

    assert settings.HELLO == "world"
    assert settings.WORKER_AUTO_REGISTER_NETMASK == ["::1"]
