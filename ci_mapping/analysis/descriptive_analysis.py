import pandas as pd
import altair as alt
import ci_mapping
from ci_mapping import logger


def annual_publication_increase(data, filename="annual_publication_increase"):
    """Annual increase of publications.

    Args:
        data (`pd.DataFrame`): MAG paper data.
        filename (str): Name of the HTML file to store the plot.

    """
    frames = []
    for cat in data.type.unique():
        frame = pd.DataFrame(
            data[data.type == cat].groupby("year")["id"].count()
            / data[data.type == cat].groupby("year")["id"].count().iloc[0]
        ).reset_index()
        frame = pd.DataFrame(frame).rename(index=str, columns={"id": "value"})
        frame["type"] = cat
        frames.append(frame)

    df = pd.concat(frames)

    # Plotting
    alt.Chart(df).mark_line(point=True).encode(
        alt.X("year", axis=alt.Axis(labelFontSize=12, titleFontSize=12)),
        alt.Y("value", axis=alt.Axis(labelFontSize=12, titleFontSize=12)),
        alt.Color("type", legend=alt.Legend(title="Category")),
        tooltip=["year", "value", "type"],
    ).properties(
        title="Annual publication increase (base year = 2000)"
    ).configure_legend(
        titleFontSize=12, labelFontSize=12
    ).interactive().save(
        f"{ci_mapping.project_dir}/reports/figures/{filename}.html"
    )
    logger.info(f"Stored {filename} plot.")


def annual_citation_sum(data, filename="annual_citation_sum"):
    """Sum of annual citations for CI and AI+CI.

    Args:
        data (`pd.DataFrame`): MAG paper data.
        filename (str): Name of the HTML file to store the plot.

    """
    df = pd.DataFrame(data.groupby(["year", "type"])["citations"].sum()).reset_index()

    # Plotting
    alt.Chart(df).mark_circle(opacity=1, stroke="black", strokeWidth=0.5).encode(
        alt.X("year", axis=alt.Axis(labelAngle=0)),
        alt.Y("type"),
        alt.Size(
            "citations",
            scale=alt.Scale(range=[0, 1500]),
            legend=alt.Legend(title="Citations"),
        ),
        alt.Color("type", legend=None),
    ).properties(width=780, height=150, title="Sum of citations for CI and AI+CI").save(
        f"{ci_mapping.project_dir}/reports/figures/{filename}.html"
    )
    logger.info(f"Stored {filename} plot.")


def publications_by_affiliation_type(data, filename="publications_by_affiliation_type"):
    """
    Share of publications in CI, AI+CI by industry and non-industry affiliations.

    Args:
        data (`pd.DataFrame`): Author-level affiliation data.
        filename (str): Name of the HTML file to store the plot.

    """
    frames = []
    for (num, comp) in zip([0, 1], ["non-Industry", "Industry"]):
        for cat in data.type.unique():
            df = data[data.non_company == num].drop_duplicates("paper_id")
            nominator = df[df.type == cat].groupby("year")["paper_id"].count()
            denominator = df[df.type == cat].groupby("year")["paper_id"].count().iloc[0]
            frame = pd.DataFrame(nominator / denominator).reset_index()
            frame = pd.DataFrame(frame).rename(index=str, columns={"paper_id": "value"})
            frame["type"] = cat
            frame["category"] = comp
            frames.append(frame)

    df = pd.concat(frames)

    # Plotting
    alt.Chart(df).mark_point(opacity=1, filled=True, size=50).encode(
        alt.X("category:N", title=None),
        alt.Y("value:Q",),
        alt.Color("type:N", legend=alt.Legend(title="Category")),
        alt.Column("year"),
        tooltip=["year", "value", "type", "category"],
    ).properties(width=25).configure_facet(spacing=15).configure_legend(
        titleFontSize=12, labelFontSize=12
    ).configure_axis(
        labelFontSize=12, titleFontSize=12
    ).interactive().save(
        f"{ci_mapping.project_dir}/reports/figures/{filename}.html"
    )
    logger.info(f"Stored {filename} plot.")


def international_collaborations(
    paper_author_aff, aff_location, filename="international_collaborations"
):
    """International collaborations: % of cross-country teams in CI, AI+CI.

    Args:
        paper_author_aff (`pd.DataFrame`): Author-level affiliation data.
        aff_location (`pd.DataFrame`): Geocoded affiliations.
        filename (str): Name of the HTML file to store the plot.

    """
    df = paper_author_aff.merge(
        aff_location[["affiliation_id", "country"]],
        left_on="affiliation_id",
        right_on="affiliation_id",
    )
    df = df.drop_duplicates(["paper_id", "affiliation_id"])
    # group countries
    df = df.groupby(["type", "year", "paper_id"])["country"].apply(list)
    df = pd.DataFrame(df)
    # binary label showing if a paper had affiliations from different countries
    df["cross_country_collab"] = df.country.apply(lambda x: 1 if len(set(x)) > 1 else 0)
    # multiply by 100 to get the proportion
    df = pd.DataFrame(
        df.reset_index().groupby(["type", "year"])["cross_country_collab"].mean() * 100
    ).reset_index()

    # Plotting
    bubbles = (
        alt.Chart(df)
        .mark_point(opacity=1, filled=True, size=50)
        .encode(
            alt.X(
                "year",
                title="Year",
                scale=alt.Scale(zero=False),
                axis=alt.Axis(grid=False, labelAngle=0),
            ),
            alt.Y("cross_country_collab", title="(%)", axis=alt.Axis(grid=False)),
            color=alt.Color("type", legend=alt.Legend(title="Category")),
        )
        .properties(width=750, title="Cross-country collaboration in CI, AI+CI")
    )

    line = (
        alt.Chart(df)
        .mark_line(strokeWidth=1, color="darkgrey", strokeDash=[1, 1])
        .encode(alt.X("year"), alt.Y("cross_country_collab"), detail="year")
    )

    (bubbles + line).configure_legend(
        titleFontSize=12, labelFontSize=12
    ).configure_axis(labelFontSize=12, titleFontSize=12).save(
        f"{ci_mapping.project_dir}/reports/figures/{filename}.html"
    )
    logger.info(f"Stored {filename} plot.")


def industry_non_industry_collaborations(
    paper_author_aff, filename="industry_non_industry_collaborations",
):
    """Industry - academia collaborations: % in CI, AI+CI

    Args:
        paper_author_aff (`pd.DataFrame`): Author-level affiliation data.
        filename (str): Name of the HTML file to store the plot.

    """
    df = paper_author_aff.drop_duplicates(["paper_id", "affiliation_id"])
    # group countries
    df = df.groupby(["type", "year", "paper_id"])["non_company"].apply(list)
    df = pd.DataFrame(df)
    # binary label showing if a paper had affiliations from industry and academia
    df["industry_academia_collab"] = df.non_company.apply(
        lambda x: 1 if len(set(x)) > 1 else 0
    )
    # multiply by 100 to get the proportion
    df = pd.DataFrame(
        df.reset_index().groupby(["type", "year"])["industry_academia_collab"].mean()
        * 100
    ).reset_index()

    # Plotting
    bubbles = (
        alt.Chart(df)
        .mark_point(opacity=1, filled=True, size=50)
        .encode(
            alt.X(
                "year",
                title="Year",
                #         sort=alt.EncodingSortField(field="delta", order='descending'),
                scale=alt.Scale(zero=False),
                axis=alt.Axis(grid=False, labelAngle=0),
            ),
            alt.Y(
                "industry_academia_collab",
                title="(%)",
                #         sort='-x',
                axis=alt.Axis(grid=False),
            ),
            color=alt.Color("type", legend=alt.Legend(title="Category")),
        )
        .properties(width=750, title="Industry-academia collaboration in CI, AI+CI")
    )

    line = (
        alt.Chart(df)
        .mark_line(strokeWidth=1, color="darkgrey", strokeDash=[1, 1])
        .encode(alt.X("year"), alt.Y("industry_academia_collab"), detail="year")
    )

    (bubbles + line).configure_legend(
        titleFontSize=12, labelFontSize=12
    ).configure_axis(labelFontSize=12, titleFontSize=12).save(
        f"{ci_mapping.project_dir}/reports/figures/{filename}.html"
    )
    logger.info(f"Stored {filename} plot.")


def open_access_publications(
    data, journals, open_access, filename="open_access_publications"
):
    """Adoption of open access by CI, AI+CI.

    Args:
        data (`pd.DataFrame`): MAG paper data.
        journals (`pd.DataFrame`): Academic journals.
        conferences (`pd.DataFrame`): Academic conferences.
        filename (str): Name of the HTML file to store the plot.

    """
    paper_journal = (
        data[["id", "year", "type"]]
        .merge(journals, left_on="id", right_on="paper_id")
        .merge(open_access, left_on="id_y", right_on="id")
    )

    frames = []
    for (num, comp) in zip([0, 1], ["Paywalled", "Preprints"]):
        for cat in paper_journal.type.unique():
            df = paper_journal[paper_journal.open_access == num].drop_duplicates(
                "paper_id"
            )
            nominator = df[df.type == cat].groupby("year")["paper_id"].count()
            denominator = df[df.type == cat].groupby("year")["paper_id"].count().iloc[0]
            frame = pd.DataFrame(nominator / denominator).reset_index()
            frame = pd.DataFrame(frame).rename(index=str, columns={"paper_id": "value"})
            frame["type"] = cat
            frame["category"] = comp
            frames.append(frame)

    df = pd.concat(frames)

    alt.Chart(df).mark_point(opacity=1, filled=True, size=50).encode(
        alt.X("category:N", title=None),
        alt.Y("value:Q"),
        alt.Color("type:N", legend=alt.Legend(title="Category")),
        column="year",
    ).properties(width=25).configure_facet(spacing=15).configure_legend(
        titleFontSize=12, labelFontSize=12
    ).configure_axis(
        labelFontSize=12, titleFontSize=12
    ).save(
        f"{ci_mapping.project_dir}/reports/figures/{filename}.html"
    )
    logger.info(f"Stored {filename} plot.")


def annual_fields_of_study_usage(
    data, pfos, fos_metadata, fos_level, top_n, filename="annual_fields_of_study_usage"
):
    """Field of study comparison for CI, AI+CI. 

    Args:
        data (`pd.DataFrame`): MAG paper data.
        pfos (`pd.DataFrame`): Paper-level fields of study.
        fos_metadata (`pd.DataFrame`): Level of the FoS in MAG hierarchy.
        fos_level (int): Level in the MAG hierarchy to plot for.
        top_n (int): Number of most used FoS to plot.
        filename (str): Name of the HTML file to store the plot.

    """
    df = data.merge(pfos, left_on="id", right_on="paper_id").merge(
        fos_metadata, left_on="field_of_study_id", right_on="id"
    )
    df = df[df["level"] == fos_level][["paper_id", "type", "year", "name"]]

    # Combine most used CI and AI+CI FoS
    ci_top_fos = df[df.type == "CI"].name.value_counts().index[:top_n]
    aici_top_fos = df[df.type == "AI_CI"].name.value_counts().index[:top_n]
    combined_fos = [
        x
        for x in set(ci_top_fos.append(aici_top_fos))
        if x != "The other" and x != "Effect of" and x != "Wide range"
    ]

    df = pd.DataFrame(
        df.groupby(["type", "year", "name"])["paper_id"].count()
    ).reset_index()
    df = df[df.type.isin(["CI", "AI_CI"])]
    df = df[df.name.isin(combined_fos)]

    df["year"] = df.year.astype(int)

    lst = []
    for year in df.year.unique():
        for name in df.name.unique():
            if len(df[(df.name == name) & (df.year == year)]["type"].values) == 2:
                continue
            elif len(df[(df.name == name) & (df.year == year)]["type"].values) == 1:
                if df[(df.name == name) & (df.year == year)]["type"].values[0] == "CI":
                    lst.append(
                        {"type": "AI_CI", "year": year, "name": name, "paper_id": 0}
                    )
                else:
                    lst.append(
                        {"type": "CI", "year": year, "name": name, "paper_id": 0}
                    )
            else:
                lst.append({"type": "AI_CI", "year": year, "name": name, "paper_id": 0})
                lst.append({"type": "CI", "year": year, "name": name, "paper_id": 0})

    df = pd.concat([df, pd.DataFrame(lst)])

    fraq = []
    for _, row in df.iterrows():
        fraq.append(
            (
                row["paper_id"]
                / df[(df.type == row["type"]) & (df.year == row["year"])][
                    "paper_id"
                ].sum()
            )
            * 100
        )

    df["fraq"] = fraq
    df = df.fillna(0)

    slider = alt.binding_range(min=2000, max=2020, step=1)
    select_year = alt.selection_single(
        name="selected", fields=["year"], bind=slider, init={"year": 2000}
    )

    base = (
        alt.Chart(df)
        .add_selection(select_year)
        .transform_filter(select_year)
        .transform_calculate(
            category=alt.expr.if_(alt.datum.type == "CI", "CI", "AI+CI")
        )
        .properties(width=350,)
    )

    color_scale = alt.Scale(domain=["CI", "AI+CI"])

    left = (
        base.transform_filter(alt.datum.category == "CI")
        .encode(
            y=alt.Y("name", axis=None),
            x=alt.X(
                "fraq",
                title="(%)",
                sort=alt.SortOrder("descending"),
                scale=alt.Scale(domain=[0, 100]),
            ),
            color=alt.Color("category:N", legend=None),
        )
        .mark_bar()
        .properties(title="CI", width=270)
    )

    middle = (
        base.encode(y=alt.Y("name", axis=None), text=alt.Text("name"),)
        .mark_text()
        .properties(width=200)
    )

    right = (
        base.transform_filter(alt.datum.category == "AI+CI")
        .encode(
            y=alt.Y("name", axis=None),
            x=alt.X("fraq", title="(%)", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color("category:N", scale=color_scale, legend=None),
        )
        .mark_bar()
        .properties(title="AI+CI", width=270)
    )

    f = (
        alt.concat(left, middle, right, spacing=5)
        .configure_legend(titleFontSize=12, labelFontSize=12)
        .configure_axis(labelFontSize=12, titleFontSize=12)
    )
    f.save(f"{ci_mapping.project_dir}/reports/figures/{filename}_{fos_level}.html")
    logger.info(f"Stored {filename}_{fos_level} plot.")


def papers_in_journals_and_conferences(
    data, journals, conferences, top_n, filename="papers_in_journals_and_conferences",
):
    """Annual publications in conferences and journals.

    Args:
        data (`pd.DataFrame`): MAG paper data.
        journals (`pd.DataFrame`): Academic journals.
        conferences (`pd.DataFrame`): Academic conferences.
        top_n (int): Number of most used journals and conferences to plot.
        filename (str): Name of the HTML file to store the plot.

    """
    # Merge journals with mag_papers
    paper_journal = data[["id", "year", "type"]].merge(
        journals, left_on="id", right_on="paper_id"
    )

    # Merge conferences with mag_papers
    paper_conference = data[["id", "year", "type"]].merge(
        conferences, left_on="id", right_on="paper_id"
    )

    # Journals
    annual_papers_in_journals = pd.DataFrame(
        paper_journal.groupby(["year", "journal_name"])["paper_id"].count()
    ).reset_index()
    annual_papers_in_journals = annual_papers_in_journals.astype({"year": "int"})

    # Conferences
    annual_papers_in_conferences = pd.DataFrame(
        paper_conference.groupby(["year", "conference_name"])["paper_id"].count()
    ).reset_index()
    annual_papers_in_conferences = annual_papers_in_conferences.astype({"year": "int"})

    # Plot
    slider = alt.binding_range(min=2000, max=2020, step=1)
    year = alt.selection_single(
        name="selected", fields=["year"], bind=slider, init={"year": 2000}
    )

    j = (
        alt.Chart(annual_papers_in_journals)
        .mark_bar()
        .encode(
            x=alt.Y("paper_id", title="Count", scale=alt.Scale(domain=[0, 90])),
            y=alt.X("journal_name", title="Journal name", sort="-x"),
        )
        .properties(width=500, height=300, title="Publications in journals")
        .add_selection(year)
        .transform_filter(year)
        .transform_window(
            row_number="row_number(paper_id)",
            sort=[alt.SortField("paper_id", order="descending")],
        )
        .transform_filter((alt.datum.row_number <= 25))
    )

    c = (
        alt.Chart(annual_papers_in_conferences)
        .mark_bar()
        .encode(
            x=alt.Y("paper_id", title="Count", scale=alt.Scale(domain=[0, 90])),
            y=alt.X("conference_name", title="Conference name", sort="-x"),
        )
        .properties(width=500, height=300, title="Publications in conferences")
        .add_selection(year)
        .transform_filter(year)
        .transform_window(
            row_number="row_number(paper_id)",
            sort=[alt.SortField("paper_id", order="descending")],
        )
        .transform_filter((alt.datum.row_number <= 25))
    )

    alt.hconcat(j, c).save(f"{ci_mapping.project_dir}/reports/figures/{filename}.html")
    logger.info(f"Stored {filename} plot.")
