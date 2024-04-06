import pandas as pd
import warnings
import pathlib
import requests
import shutil

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


def disambiguateName(name, songid):
    if name in transition["sameName"]:
        name = transition["sameName"][name][songid]
    return name


def getLinkName(songid):
    name = songlist[songid]["title_localized"]["en"]
    # convert to display name if possible
    name = transition["songNameToDisplayName"].get(name, name)
    return disambiguateName(name, songid)


def getConstants(songid):
    raw = chartconstant[songid]
    constants = [entry.get("constant", pd.NA) if entry else pd.NA for entry in raw]
    for _ in range(5 - len(constants)):
        constants.append(pd.NA)
    return constants


def getAllFlat():
    songids = list(chartconstant.keys())

    matrix = []
    for songid in songids:
        constants = getConstants(songid)
        song = {
            "songid": songid,
            "linkName": getLinkName(songid),
            "title": songlist[songid]["title_localized"][
                "en"
            ],  # will get disambiguated later
        }
        for i, diff in enumerate(DIFFICULTIES):
            song_diff = song.copy()
            # I hate Lowiro for this stupid json structure
            # try to see if there's a difficulty-specific title
            diffs = songlist[songid]["difficulties"]
            diffclasses = [dff["ratingClass"] for dff in diffs]
            if i not in diffclasses:
                continue
            diffsInd = diffclasses.index(i)
            if "title_localized" in diffs[diffsInd]:
                song_diff["title"] = diffs[diffsInd]["title_localized"]["en"]
            song_diff["title"] = disambiguateName(song_diff["title"], songid)
            song_diff["label"] = diff.upper()
            song_diff["detail"] = constants[i]
            matrix.append(song_diff)

    return pd.DataFrame.from_records(matrix, index=["songid", "label"]).dropna()


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
    FILE_NAME = "put_your_score_in_here.xlsx"
    SHEET_NAME = "Sheet1"
    df = getAllFlat()
    df = df[df["detail"] >= 8]

    make_backup(FILE_NAME)

    try:
        df_in = pd.read_excel(FILE_NAME).set_index(["songid", "label"])
        df_in = df_in[["score"]]
        df_output = df.join(df_in, how="outer", on=["songid", "label"])
    except (FileNotFoundError, KeyError, ValueError) as e:
        df_output = df
        df_output["score"] = pd.NA
        warnings.warn(
            "Unable to process old scores, continuing without them", UserWarning
        )
        print(e)

    print(df_output)
    df_output.reset_index(inplace=True)

    df_output["name"] = df_output["title"]
    df_output["name_for_sorting"] = df_output["name"].str.upper()
    df_output["title"] = "https://arcwiki.mcd.blue/" + df_output["linkName"]

    df_output.sort_values(
        ["label", "name_for_sorting"], inplace=True, ascending=[True, True]
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
    worksheet.write_column(1, 0, df_output["name"], workbook.get_default_url_format())
    worksheet.set_column(0, 0, 50)
    worksheet.set_column(1, 2, 8, base_format)
    worksheet.set_column(3, 3, 15, base_format)
    worksheet.set_column(4, 4, None, None, {"hidden": True})  # hide songid column
    for col_num, value in enumerate(OUTPUT_COLUMNS):
        worksheet.write(0, col_num, value, header_format)

    for difficulty, color in DIFFICULTY_COLORS.items():
        worksheet.conditional_format(
            1,
            1,
            len(df),
            1,
            {
                "type": "cell",
                "criteria": "equal to",
                "value": f'"{difficulty.upper()}"',
                "format": workbook.add_format({"bg_color": color}),
            },
        )

    writer.close()


if __name__ == "__main__":
    main()
