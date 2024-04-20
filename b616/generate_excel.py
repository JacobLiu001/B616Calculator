from dataclasses import dataclass
from itertools import chain

import pandas as pd
import requests
import xlsxwriter  # type: ignore

URLTEMPLATE = r"https://arcwiki.mcd.blue/index.php?title={}&action=raw"
DIFFICULTIES = ["PST", "PRS", "FTR", "BYD", "ETR"]
DIFFICULTY_COLORS = {
    "PST": "#40A0A0",
    "PRS": "#9FD094",
    "FTR": "#A665C3",
    "BYD": "#BE6666",
    "ETR": "#BEA2C6",
}


class Resources:
    def __init__(self):
        self._chartconstant = None
        self._songlist = None
        self._transition = None

    @classmethod
    def __preprocess_songlist(cls, raw):
        raw = raw["songs"]
        songlist = {song["id"]: song for song in raw}
        return songlist

    def fetch(self):
        self._chartconstant = requests.get(
            URLTEMPLATE.format("Template:ChartConstant.json")
        ).json()
        self._songlist = self.__preprocess_songlist(
            requests.get(URLTEMPLATE.format("Template:Songlist.json")).json()
        )
        self._transition = requests.get(
            URLTEMPLATE.format("Template:Transition.json")
        ).json()

    @property
    def chartconstant(self):
        if self._chartconstant is None:
            self.fetch()
        return self._chartconstant

    @property
    def songlist(self):
        if self._songlist is None:
            self.fetch()
        return self._songlist

    @property
    def transition(self):
        if self._transition is None:
            self.fetch()
        return self._transition


class Song:
    @dataclass
    class Difficulty:
        rating_class: str
        title: str | None
        rating: float  # +0.5 for ratingPlus
        detail: float  # true chart constant (i.e., "detailed" rating)

    def __init__(self, resources: Resources, songid: str):
        self.songid = songid
        self.link_name = self.__get_link_name(resources)
        self.base_title = resources.songlist[songid]["title_localized"]["en"]
        self.title = self.__disambiguate_base_title(resources)
        self.difficulties = self.__get_difficulties(resources)

    def __disambiguate_base_title(self, resources: Resources):
        if self.base_title in resources.transition["sameName"]:
            return resources.transition["sameName"][self.base_title][self.songid]
        return self.base_title

    def __get_link_name(self, resources: Resources):
        name = resources.songlist[self.songid]["title_localized"]["en"]
        # convert to display name if possible
        name = resources.transition["songNameToDisplayName"].get(name, name)
        if name in resources.transition["sameName"]:
            name = resources.transition["sameName"][name][self.songid]
        return name

    def __get_difficulties(self, resources: Resources):
        difficulties: list[Song.Difficulty] = []
        for difficulty_entry in resources.songlist[self.songid]["difficulties"]:
            if difficulty_entry["rating"] == 0:
                continue
            if difficulty_entry.get("hidden_until", "never") == "always":
                continue
            rating_class_id = difficulty_entry["ratingClass"]
            rating_class = DIFFICULTIES[rating_class_id]
            rating = float(difficulty_entry["rating"])
            if difficulty_entry.get("ratingPlus", False):
                rating += 0.5
            detail = resources.chartconstant[self.songid][rating_class_id]["constant"]
            title = difficulty_entry.get("title_localized", {}).get("en", None)
            difficulties.append(Song.Difficulty(rating_class, title, rating, detail))
        return difficulties

    def iter_entries(self):
        for difficulty in self.difficulties:
            yield {
                "songid": self.songid,
                "label": difficulty.rating_class,
                "title": self.title if difficulty.title is None else difficulty.title,
                "detail": difficulty.detail,
                "linkName": self.link_name,
                "detail_for_sorting": difficulty.rating,
            }


def get_all_entries(resources: Resources):
    return chain.from_iterable(
        Song(resources, songid).iter_entries() for songid in resources.songlist
    )


def write_to_excel(df: pd.DataFrame, filename: str, sheetname: str):
    df = df.reset_index()

    df["name"] = df["title"]
    df["name_for_sorting"] = df["name"].str.upper()
    # Xlsxwriter hackery: write links first, then write the text
    # And it will still point to the correct link
    df["title"] = "https://arcwiki.mcd.blue/" + df["linkName"]

    df.sort_values(
        ["label", "detail_for_sorting", "name_for_sorting"],
        inplace=True,
        ascending=[True, False, True],
    )

    OUTPUT_COLUMNS = ["title", "label", "detail", "score", "songid"]
    writer = pd.ExcelWriter(filename, engine="xlsxwriter")
    df.to_excel(writer, index=False, columns=OUTPUT_COLUMNS, sheet_name=sheetname)

    workbook: xlsxwriter.Workbook = writer.book
    worksheet = writer.sheets[sheetname]
    header_format = workbook.add_format(
        {
            "font_name": "calibri",
            "bold": True,
            "valign": "vcenter",
            "bg_color": "#FFE699",
            "border": 1,
            "align": "center",
        }
    )
    base_format = workbook.add_format(
        {"font_name": "calibri", "valign": "vcenter", "align": "center"}
    )
    songid_format = workbook.add_format(
        {"font_name": "calibri", "valign": "vcenter", "align": "left"}
    )
    # Write the names over the links; this preserves the link
    worksheet.write_column(1, 0, df["name"], workbook.get_default_url_format())
    worksheet.set_column(0, 0, 50)  # Names (links)
    worksheet.set_column(1, 2, 8, base_format)  # Difficulty label and detail constant
    worksheet.set_column(3, 3, 15, base_format)  # Score, wide since max ~1e7
    # Don't hide songid column (4) so the user won't forget to include it if they sort
    worksheet.set_column(4, 4, 15, songid_format, {"hidden": False})

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


def merge_scores(df: pd.DataFrame, df_old: pd.DataFrame | None) -> pd.DataFrame:
    """Merges the new scores with the old scores, if they exist.
    If the old scores do not exist, scores are left blank.

    Both dataframes are expected to have the columns "songid" and "label".
    It is recommended to set the index to ["songid", "label"] before calling this function.
    """
    if df.index.names != ["songid", "label"]:
        df = df.reset_index().set_index(["songid", "label"])
    if df_old is None:
        df["score"] = ""
        return df
    if df_old.index.names != ["songid", "label"]:
        df_old = df_old.reset_index().set_index(["songid", "label"])
    df_old = df_old[["score"]]  # Only keep the score column so we can just join
    # left join, discarding any old scores whose songid/label is not in the new data
    print(df, df_old)
    return df.join(df_old, on=["songid", "label"], how="left")


def main():
    FILE_NAME = "scores.xlsx"
    SHEET_NAME = "Sheet1"
    resources = Resources()
    resources.fetch()

    df = pd.DataFrame.from_records(
        get_all_entries(resources), index=["songid", "label"]
    ).dropna()

    # We're only interested in entries with chart constant >= 8
    df = df[df["detail"] >= 8]

    # Read the old scores and merge them
    try:
        df_old = pd.read_excel(FILE_NAME)
    except FileNotFoundError:
        df_old = None

    df_output = merge_scores(df, df_old)

    write_to_excel(df_output, FILE_NAME, SHEET_NAME)


if __name__ == "__main__":
    main()
