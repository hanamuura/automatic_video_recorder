import argparse
import csv
from pathlib import Path

import qscript


def main():
    parser = argparse.ArgumentParser(
        description="Record one browser automation video for every CSV row."
    )
    parser.add_argument("--csv", default="input.csv", help="Input CSV file")
    parser.add_argument(
        "--video-folder",
        default=None,
        help="Output folder (defaults to qscript.PATH_TO_VIDEO_FOLDER)",
    )
    args = parser.parse_args()

    if args.video_folder:
        qscript.PATH_TO_VIDEO_FOLDER = args.video_folder

    csv_path = Path(args.csv)
    if not csv_path.is_file():
        parser.error("CSV file not found: {}".format(csv_path))

    processed = 0
    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=";", quotechar='"')

        expected_columns = [
            "URL", "Company Name", "Language", "Country",
            "Postcode", "City", "Street", "HouseNo",
        ]
        if reader.fieldnames != expected_columns:
            raise ValueError(
                "CSV header must be exactly: {}".format(";".join(expected_columns))
            )

        for row_number, row in enumerate(reader, start=2):
            processed += 1
            try:
                video_path = qscript.CaptureVideo_Magento(
                    row["URL"],
                    row["Company Name"],
                    row["Language"],
                    row["Country"],
                    row["Postcode"],
                    row["City"],
                    row["Street"],
                    row["HouseNo"],
                )
                if video_path:
                    print("[row {}] Saved: {}".format(row_number, video_path))
                else:
                    print("[row {}] Failed: no video was created".format(row_number))
            except Exception as exc:
                print("[row {}] Error: {}".format(row_number, exc))
    print("Finished. Processed {} data row(s).".format(processed))


if __name__ == "__main__":
    main()
