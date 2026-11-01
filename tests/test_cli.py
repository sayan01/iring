from typer.testing import CliRunner

from iring import cli

runner = CliRunner()

LIBRARY = {
    "Ringtones": {
        "AAAA.m4r": {"Name": "Janji - Heroes Tonight", "Total Time": 30000},
        "BBBB.m4r": {"Name": "anime-ringtone", "Total Time": 13862},
    }
}


def fake_read_library(monkeypatch):
    async def read_library(backup_dir):
        return "Test iPhone", LIBRARY

    monkeypatch.setattr(cli, "read_library", read_library)


def test_clip_too_long_fails_before_downloading(monkeypatch):
    monkeypatch.setattr(cli, "download", lambda *a: (_ for _ in ()).throw(AssertionError("downloaded")))
    result = runner.invoke(cli.app, ["https://youtu.be/x", "-s", "0:00", "-e", "0:45"])
    assert result.exit_code == 1
    assert "at most 40s" in result.output


def test_list_shows_tones(monkeypatch):
    fake_read_library(monkeypatch)
    result = runner.invoke(cli.app, ["--list"])
    assert result.exit_code == 0
    assert "Janji - Heroes Tonight" in result.output
    assert "anime-ringtone" in result.output
    assert "30s" in result.output


def test_delete_asks_and_deletes_matches(monkeypatch):
    fake_read_library(monkeypatch)
    deleted = []

    async def delete_ringtones(fnames, backup_dir):
        deleted.extend(fnames)
        return "Test iPhone"

    monkeypatch.setattr(cli, "delete_ringtones", delete_ringtones)
    result = runner.invoke(cli.app, ["--delete", "heroes"], input="y\n")
    assert result.exit_code == 0, result.output
    assert deleted == ["AAAA.m4r"]


def test_delete_can_be_declined(monkeypatch):
    fake_read_library(monkeypatch)
    monkeypatch.setattr(cli, "delete_ringtones", lambda *a: (_ for _ in ()).throw(AssertionError("deleted")))
    result = runner.invoke(cli.app, ["--delete", "heroes"], input="n\n")
    assert result.exit_code != 0


def test_delete_without_match_is_an_error(monkeypatch):
    fake_read_library(monkeypatch)
    result = runner.invoke(cli.app, ["--delete", "nope"])
    assert result.exit_code == 1
    assert "matches 'nope'" in result.output


def test_list_with_url_is_rejected():
    result = runner.invoke(cli.app, ["https://youtu.be/x", "--list"])
    assert result.exit_code != 0
