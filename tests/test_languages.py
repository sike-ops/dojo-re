from dojo_re.languages import language_spec
from dojo_re.models import Language


def test_language_specs_have_source_and_program_output() -> None:
    for language in Language:
        spec = language_spec(language)
        assert spec.filename.startswith("source.")
        assert "program" in spec.compile_command
