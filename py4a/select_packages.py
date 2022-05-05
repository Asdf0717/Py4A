import pandas as pd

if __name__ == "__main__":
    LIO_PKG_PATH = "../libraries-1.6.0-2020-01-12/projects-1.6.0-2020-01-12.csv"

    projects = pd.read_csv(LIO_PKG_PATH, low_memory=False)
    projects = projects[projects["Platform"] == "Pypi"]
    projects = projects.sort_values(
        by="Dependent Repositories Count", ascending=False
    ).head(10000)

    pkgs = []
    for i, row in projects.iterrows():
        pkgs.append(
            {
                "pkg_name": row["Name"],
                "repo_url": row["Repository URL"],
                "dependent_repo_count": row["Dependent Repositories Count"],
            }
        )
    pd.DataFrame(pkgs).to_csv("data/packages.csv", index=False)
