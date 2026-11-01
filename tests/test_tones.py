import plistlib

from iring.tones import add_tone, clean_title, empty_library, find_tones, remove_tones


def library(**tones):
    return {"Ringtones": {fname: {"Name": name, "GUID": "X", "PID": 1} for fname, name in tones.items()}}


def test_clean_title_drops_text_after_first_pipe():
    title = "Cartoon, Jéja - On & On (feat. Daniel Levi) | Electronic Pop | NCS - Copyright Free Music"
    assert clean_title(title) == "Cartoon, Jéja - On & On (feat. Daniel Levi)"


def test_clean_title_keeps_plain_titles():
    assert clean_title("  Midi Blosso - The Sound Of Your Fear ") == "Midi Blosso - The Sound Of Your Fear"


def test_add_tone_adds_entry_with_expected_fields():
    lib = library(KPKI="anime-ringtone")
    updated, fname, removed = add_tone(lib, "On & On", 30000, existing_files={"KPKI.m4r"})

    assert removed == []
    assert fname.endswith(".m4r") and len(fname) == 8 and fname[:4].isupper()
    entry = updated["Ringtones"][fname]
    assert entry["Name"] == "On & On"
    assert entry["Total Time"] == 30000
    assert entry["Protected Content"] is False
    assert len(entry["GUID"]) == 16 and entry["GUID"] == entry["GUID"].upper()
    assert 0 < entry["PID"] < 2**63
    # serialisable the way the phone stores it
    plistlib.dumps(updated, fmt=plistlib.FMT_BINARY)


def test_add_tone_keeps_other_tones_and_does_not_mutate_input():
    lib = library(KPKI="anime-ringtone")
    updated, _, _ = add_tone(lib, "On & On", 30000, existing_files=set())
    assert "KPKI" in updated["Ringtones"]
    assert list(lib["Ringtones"]) == ["KPKI"]


def test_add_tone_replaces_tone_with_same_name():
    lib = library(**{"AAAA.m4r": "On & On", "BBBB.m4r": "Other"})
    updated, fname, removed = add_tone(lib, "On & On", 30000, existing_files={"AAAA.m4r", "BBBB.m4r"})

    assert removed == ["AAAA.m4r"]
    assert "AAAA.m4r" not in updated["Ringtones"]
    assert "BBBB.m4r" in updated["Ringtones"]
    assert [e["Name"] for e in updated["Ringtones"].values()].count("On & On") == 1
    assert fname != "AAAA.m4r"


def test_add_tone_avoids_existing_file_names(monkeypatch):
    names = iter(["AAAA", "AAAA", "CCCC"])
    monkeypatch.setattr("iring.tones._random_name", lambda: next(names))
    _, fname, _ = add_tone(library(), "x", 1000, existing_files={"AAAA.m4r"})
    assert fname == "CCCC.m4r"


def test_empty_library():
    assert empty_library() == {"Ringtones": {}}


def test_find_tones_matches_case_insensitive_substring():
    lib = library(**{"AAAA.m4r": "Janji - Heroes Tonight", "BBBB.m4r": "anime-ringtone"})
    assert find_tones(lib, "heroes") == {"AAAA.m4r": "Janji - Heroes Tonight"}


def test_find_tones_prefers_exact_match_over_substrings():
    lib = library(**{"AAAA.m4r": "Song", "BBBB.m4r": "Song (remix)"})
    assert find_tones(lib, "song") == {"AAAA.m4r": "Song"}


def test_find_tones_returns_all_partial_matches():
    lib = library(**{"AAAA.m4r": "Song one", "BBBB.m4r": "Song two", "CCCC.m4r": "Other"})
    assert set(find_tones(lib, "song")) == {"AAAA.m4r", "BBBB.m4r"}


def test_find_tones_no_match():
    assert find_tones(library(**{"AAAA.m4r": "Song"}), "nope") == {}


def test_remove_tones_drops_entries_without_mutating_input():
    lib = library(**{"AAAA.m4r": "Song", "BBBB.m4r": "Other"})
    updated = remove_tones(lib, ["AAAA.m4r"])
    assert list(updated["Ringtones"]) == ["BBBB.m4r"]
    assert set(lib["Ringtones"]) == {"AAAA.m4r", "BBBB.m4r"}
