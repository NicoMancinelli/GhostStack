import subprocess
import sys


def test_cli_help_profiles_exist():
    result = subprocess.run(
        [sys.executable, "scripts/ghoststack_ctl.py", "--help"],
        capture_output=True,
        text=True,
        cwd=".",
    )
    assert result.returncode == 0
    assert "start-rf" in result.stdout
    assert "start-network" in result.stdout
    assert "sentry" in result.stdout


def test_modules_profiles():
    from ghoststack.modules import profile_for

    assert len(profile_for("start-rf")) >= 2
    assert len(profile_for("start-all", sentry=True)) > len(profile_for("start-all"))
