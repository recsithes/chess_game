from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


def train_model(dataset_path: Path, output_model_path: Path) -> float:
    frame = pd.read_csv(dataset_path)
    if frame.empty:
        raise ValueError("Dataset is empty. Run preprocessing with valid PGN first.")

    feature_cols = [column for column in frame.columns if column.startswith("sq_")]
    x = frame[feature_cols]
    y = frame["move"]

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y if y.nunique() > 1 else None,
    )

    model = RandomForestClassifier(n_estimators=120, random_state=42, n_jobs=-1)
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)
    accuracy = accuracy_score(y_test, predictions)

    output_model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_model_path)

    return accuracy


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    dataset_path = base_dir / "data" / "training_examples.csv"
    model_path = Path(__file__).resolve().parent / "move_model.joblib"

    score = train_model(dataset_path, model_path)
    print(f"Model saved to: {model_path}")
    print(f"Validation accuracy: {score:.4f}")
