from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import classification_report, top_k_accuracy_score
from sklearn.model_selection import train_test_split


def evaluate_model(dataset_path: Path, model_path: Path) -> None:
    frame = pd.read_csv(dataset_path)
    feature_cols = [column for column in frame.columns if column.startswith("sq_")]
    x = frame[feature_cols]
    y = frame["move"]

    _, x_test, _, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y if y.nunique() > 1 else None,
    )

    model = joblib.load(model_path)
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)

    labels = list(model.classes_)
    top3 = top_k_accuracy_score(y_test, probabilities, k=min(3, len(labels)), labels=labels)

    print("Top-3 accuracy:", round(top3, 4))
    print(classification_report(y_test, predictions, zero_division=0))


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    dataset_path = base_dir / "data" / "training_examples.csv"
    model_path = base_dir / "train" / "move_model.joblib"

    evaluate_model(dataset_path, model_path)
