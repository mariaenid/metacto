"""Domain value-object invariants."""

import pytest

from apps.identity.domain import Email, InvalidEmail, Password, WeakPassword


@pytest.mark.unit
class TestEmail:
    def test_normalises_case_and_whitespace(self) -> None:
        assert Email("  Foo@Bar.COM ").value == "foo@bar.com"

    @pytest.mark.parametrize("bad", ["", "no-at-sign", "a@b", "a@b.", "@x.com", "x@.com"])
    def test_rejects_invalid(self, bad: str) -> None:
        with pytest.raises(InvalidEmail):
            Email(bad)


@pytest.mark.unit
class TestPassword:
    def test_accepts_strong_password(self) -> None:
        Password("CorrectHorseBattery!7")

    @pytest.mark.parametrize("bad", ["short", " " * 20, "ab " * 4 + "x   yz"])
    def test_rejects_weak(self, bad: str) -> None:
        with pytest.raises(WeakPassword):
            Password(bad)
