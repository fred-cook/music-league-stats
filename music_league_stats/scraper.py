import os
from pathlib import Path


from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
from  matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
cmap=LinearSegmentedColormap.from_list('rg',["r", "w", "g"], N=256) 


translator = {'Sacha Darwin': 'Sacha',
              'Bethany Dickens-Devereux': 'Bethany',
              'sam24ahhhhhh': 'Sam',
              'Martha Mukungurutse': 'Martha',
              'Victoria Whitehead': 'Victoria',
              'Andrej Zacharenkov': 'Andrej',
              'fred': 'Fred',
              'Jenny': 'Jenny',
              'Tim            :)': 'Tim P',
              'Mel Shallcrass': 'Mel',
              'Jamie England': 'Jamie',
              'Helen Adams': 'Helen',
              'Rory': 'Rory',
              'murraypurves101': 'Murray',
              'James Hardwick': 'James',
              'Olek': 'Olek',
              'Russell': 'Russell',
              'owainst': 'Owain',
              'Tim': 'Tim C'}


def create_dataframe(path: Path, translator: dict[str, str] | None=None) -> tuple[pd.DataFrame, list[str]]:
    """
    Given a path containing the html elements of the music league
    collect all of the data of who voted for who, as well as the
    spotify track ids for further scraping

    If a translator is passed in use it to conver the names

    return a dataframe of the scraped data, with rows as all votes
    for the submitter in that round, and a list of all the names
    of the players
    """

    df = pd.DataFrame()

    for file in path.iterdir():
        if not file.is_file(): # directory of content
            continue

        with open(file, encoding="utf8") as f:
            html_content = f.read()

        # Load HTML content into BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all rows containing voters
        entries = soup.find_all(class_="card mb-4")

        name_set: set[str] = set() # use this to gather all of the names
        
        for entry in entries:
            song_id = entry['id'][len('spotify:track:'):]
            submitter = entry.findNext(class_="mt-3").findNext("h6", class_="text-truncate").text.strip("\n")
            total = int(entry.findNext(class_="col-auto text-end").findNext("h3").contents[-1].text.strip())
            song, artist, album = entry.findNext(class_="text-truncate").findAll(("h6", "p"))
            
            votes: dict[str, int] = {}
            for row in entry.findNext(class_="card-footer").findAll(class_="row"):
                name = row.find_next(class_="text-truncate").text
                name_set |= {name}

                comment = row.findAll(class_="text-break ws-pre-wrap")
                comment = comment[0].text if len(comment) else None

                score = row.findAll(class_="m-0")
                score = int(score[0].text) if len(score) else 0

                votes[name] = score

            if sum(list(votes.values())) != total:
                votes = {name: 0 if value > 0 else value
                                    for name, value in votes.items()}

            df = pd.concat((df,
                    pd.DataFrame([votes | {"submitter": submitter,
                                "song_id": song_id,
                                "round": int(str(file).split('_')[-1].strip(".html"))}])))


    names = list(name_set)

    if translator is not None:
        df = df.replace(translator)
        df = df.rename(mapper=translator, axis=1)
        names = list(translator.values())

    #df = df.set_index(df["submitter"])
    df[pd.isna(df)] = 0
    return df, names

if __name__ == "__main__":
    df, names = create_dataframe(Path("c:/Users/Ferd/Downloads/music_league_2"), translator=translator)

    winning_order = df.groupby(df["submitter"])[names].sum().sum(axis=1)
    winning_order = winning_order.sort_values(ascending=False).index


    arr = np.concatenate([
        group.reindex(winning_order, fill_value=0.0).to_numpy()[None, :, :]
        for _, group in df.groupby("round")[winning_order]], axis=0)
    correlation = np.sum(arr, axis=0)

    norm = TwoSlopeNorm(vmin=np.min(correlation),
                        vcenter=0,
                        vmax=np.max(correlation))

    plt.imshow(correlation, cmap='RdYlGn', norm=norm, interpolation='nearest')
    plt.xticks(np.arange(len(winning_order)), winning_order, rotation='vertical')
    plt.yticks(np.arange(len(winning_order)), winning_order)


    cbar = plt.colorbar()

    plt.show()


    downvotes = np.where(arr < 0, arr, 0).sum(axis=(0, 2))
    plt.bar(np.arange(len(names)), sorted(downvotes))
    plt.xticks(np.arange(len(names)), winning_order[downvotes.argsort()],
            rotation="vertical")
    plt.show()

