import json

from examples.run_pipeline import main


def test_synthetic_example_runs_end_to_end(capsys):
    main()
    output = json.loads(capsys.readouterr().out)
    assert len(output["documents"]) == 4
    assert output["validation"]["confusion_matrix"] == {
        "false_negative": 1,
        "false_positive": 0,
        "true_negative": 1,
        "true_positive": 2,
    }
