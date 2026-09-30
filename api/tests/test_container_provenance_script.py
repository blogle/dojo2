def test_live_image_validator_uses_valid_docker_label_template() -> None:
    pathlib = __import__("pathlib")
    repo_root = pathlib.Path(__file__).parents[2]
    script = (repo_root / "ops" / "container" / "validate-image-provenance.sh").read_text(
        encoding="utf-8"
    )

    valid_template = """--format '{{ index .Config.Labels "org.opencontainers.image.revision" }}'"""
    invalid_template = r"""--format '{{ index .Config.Labels \"org.opencontainers.image.revision\" }}'"""
    assert valid_template in script
    assert invalid_template not in script
