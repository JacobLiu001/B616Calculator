import pathlib
import shutil
import warnings

import pandas as pd
import requests

DIFFICULTIES = ["PST", "PRS", "FTR", "BYD", "ETR"]
DIFFICULTY_COLORS = {
    "PST": "#40A0A0",
    "PRS": "#9FD094",
    "FTR": "#A665C3",
    "BYD": "#BE6666",
    "ETR": "#BEA2C6",
}


def preprocess_songlist(raw):
    raw = raw["songs"]
    songlist = {song["id"]: song for song in raw}
    return songlist


# sequentially request the files
URLTEMPLATE = r"https://arcwiki.mcd.blue/index.php?title={}&action=raw"
chartconstant = requests.get(URLTEMPLATE.format("Template:ChartConstant.json")).json()
songlist = requests.get(URLTEMPLATE.format("Template:Songlist.json")).json()
songlist = preprocess_songlist(songlist)
transition = requests.get(URLTEMPLATE.format("Template:Transition.json")).json()

print("Done fetching data")


def disambiguate_name(name: str, songid: str) -> str:
    if name in transition["sameName"]:
        name = transition["sameName"][name][songid]
    return name


def get_link_name(songid: str) -> str:
    name = songlist[songid]["title_localized"]["en"]
    # convert to display name if possible
    name = transition["songNameToDisplayName"].get(name, name)
    return disambiguate_name(name, songid)


def get_detail_for_sorting(difficulty_record) -> float:
    base_difficulty = float(difficulty_record["rating"])
    rating_plus = difficulty_record.get("ratingPlus", False)
    if rating_plus:
        # just for sorting purposes, such that 9 < 9+ < 10
        base_difficulty += 0.5
    return base_difficulty


def get_all_entries():
    rows = []
    for songid, song_info in songlist.items():
        for difficulty_record in song_info["difficulties"]:
            if difficulty_record["rating"] == 0:
                # Last | Eternity has three 0-rated non-existent charts
                continue
            if difficulty_record.get("hidden_until", "never") == "always":
                # Skip other hidden charts for future-proofing
                continue
            ratingClass = difficulty_record["ratingClass"]
            title = song_info["title_localized"]["en"]
            if "title_localized" in difficulty_record:
                # If the difficulty has a different name, use that
                title = difficulty_record["title_localized"]["en"]
            rows.append(
                {
                    "songid": songid,
                    "label": DIFFICULTIES[ratingClass],
                    "title": disambiguate_name(title, songid),
                    "detail": chartconstant[songid][ratingClass]["constant"],
                    "linkName": get_link_name(songid),
                    "detail_for_sorting": get_detail_for_sorting(difficulty_record),
                }
            )

    return pd.DataFrame.from_records(rows, index=["songid", "label"]).dropna()


def make_backup(filename):
    filepath = pathlib.Path(filename)

    if not filepath.exists():
        warnings.warn("File not found, not making backup", UserWarning)
        return
    backupname = filepath.with_stem(filepath.stem + "_backup")

    if backupname.exists():
        warnings.warn("Overwriting the backup", UserWarning)
        backupname.unlink()
    shutil.copy2(filename, backupname)


def main():
    FILE_NAME = "put_your_score_here.xlsx"
    SHEET_NAME = "Sheet1"
    df = get_all_entries()
    df = df[df["detail"] >= 8]

    make_backup(FILE_NAME)

    # Read the old scores and merge them
    try:
        df_in = pd.read_excel(FILE_NAME).set_index(["songid", "label"])
        df_in = df_in[["score"]]
        df_output = df.join(df_in, how="outer", on=["songid", "label"])
    except (FileNotFoundError, KeyError, ValueError) as e:
        df_output = df
        df_output["score"] = pd.NA
        warnings.warn(
            f"Unable to process old scores, continuing without them. Error: {e}"
        )

    df_output.reset_index(inplace=True)

    df_output["name"] = df_output["title"]
    df_output["name_for_sorting"] = df_output["name"].str.upper()
    # Xlsxwriter hackery: write links first, then write the text
    # And it will still point to the correct link
    df_output["title"] = "https://arcwiki.mcd.blue/" + df_output["linkName"]

    df_output.sort_values(
        ["label", "detail_for_sorting", "name_for_sorting"],
        inplace=True,
        ascending=[True, False, True],
    )

    OUTPUT_COLUMNS = ["title", "label", "detail", "score", "songid"]
    writer = pd.ExcelWriter(FILE_NAME, engine="xlsxwriter")
    df_output.to_excel(
        writer, index=False, columns=OUTPUT_COLUMNS, sheet_name=SHEET_NAME
    )

    workbook = writer.book
    worksheet = writer.sheets[SHEET_NAME]
    header_format = workbook.add_format(
        {
            "font_name": "calibri",
            "bold": True,
            "valign": "top",
            "bg_color": "#FFE699",
            "border": 1,
            "align": "center",
        }
    )
    base_format = workbook.add_format(
        {"font_name": "calibri", "valign": "top", "align": "center"}
    )
    # Write the names over the links; this preserves the link
    worksheet.write_column(1, 0, df_output["name"], workbook.get_default_url_format())
    worksheet.set_column(0, 0, 50)  # Names (links)
    worksheet.set_column(1, 2, 8, base_format)  # Difficulty label and detail constant
    worksheet.set_column(3, 3, 15, base_format)  # Score, wide since max ~1e7
    worksheet.set_column(4, 4, None, None, {"hidden": True})  # hide songid column

    # Format the header row
    for col_num, value in enumerate(OUTPUT_COLUMNS):
        worksheet.write(0, col_num, value, header_format)

    # Conditional coloring for difficulty
    for difficulty, color in DIFFICULTY_COLORS.items():
        worksheet.conditional_format(
            1,  # Row 2
            1,  # Column B
            len(df),  # Last row
            1,  # Column B
            {
                "type": "cell",
                "criteria": "equal to",
                "value": f'"{difficulty}"',
                "format": workbook.add_format({"bg_color": color}),
            },
        )

    writer.close()


if __name__ == "__main__":
    main()
