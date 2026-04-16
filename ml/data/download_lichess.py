from pathlib import Path

import requests


LICHESS_EXAMPLE_URL = "https://database.lichess.org/standard/lichess_db_standard_rated_2013-01.pgn.zst"


def download_sample_dataset(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "lichess_sample_2013-01.pgn.zst"

    if output_path.exists():
        print(f"Dataset already exists: {output_path}")
        return output_path

    with requests.get(LICHESS_EXAMPLE_URL, stream=True, timeout=120) as response:
        response.raise_for_status()
        with output_path.open("wb") as file_obj:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file_obj.write(chunk)

    print(f"Downloaded dataset to: {output_path}")
    return output_path


if __name__ == "__main__":
    dataset_path = download_sample_dataset(Path(__file__).resolve().parent)
    print(dataset_path)
