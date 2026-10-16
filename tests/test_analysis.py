import pytest

from app.services import analysis
from tests.conftest import SAMPLE_CSV


def test_parse_csv_ok():
    df = analysis.parse_csv(SAMPLE_CSV)
    assert df.shape == (4, 4)


@pytest.mark.parametrize("content", [b"", b"nombre,edad\n"])
def test_parse_csv_rejects_empty_content(content):
    with pytest.raises(analysis.AnalysisError):
        analysis.parse_csv(content)


def test_summarize_numeric_and_text_columns():
    result = analysis.summarize(analysis.parse_csv(SAMPLE_CSV))

    assert result["rows"] == 4
    assert result["stats"]["edad"]["nulls"] == 1
    assert result["stats"]["precio"]["mean"] == 19.0
    assert result["stats"]["ciudad"]["top"] == "Lima"


def test_correlations_diagonal_is_one():
    result = analysis.correlations(analysis.parse_csv(SAMPLE_CSV))

    assert result["columns"] == ["edad", "precio"]
    assert result["matrix"][0][0] == 1.0
    assert result["matrix"][1][1] == 1.0


def test_correlations_requires_two_numeric_columns():
    df = analysis.parse_csv(b"a,b\n1,x\n2,y\n")
    with pytest.raises(analysis.AnalysisError):
        analysis.correlations(df)


def test_histogram_returns_png_bytes():
    png = analysis.histogram_png(analysis.parse_csv(SAMPLE_CSV), "precio")
    assert png.startswith(b"\x89PNG")


def test_histogram_rejects_text_column():
    with pytest.raises(analysis.AnalysisError):
        analysis.histogram_png(analysis.parse_csv(SAMPLE_CSV), "ciudad")
