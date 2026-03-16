import pytest

from app import pmt


@pytest.mark.parametrize(
    ("input_data", "expected_amount"),
    [
        pytest.param(
            {
                "rate": 0.05 / 12,
                "nper": 3 * 12,
                "pv": 10000,
            },
            -299.709,
            id="First example",
        ),
    ],
)
def test_pmt(
    input_data: dict,
    expected_amount: float,
):
    result = pmt(
        rate=input_data["rate"],
        nper=input_data["nper"],
        pv=input_data["pv"],
    )
    diff = abs(result - expected_amount)
    assert diff < 0.01, f"Expected {expected_amount}, but got {result}"
