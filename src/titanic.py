import pandas as pd
from sklearn.preprocessing import StandardScaler
from src.kaggle_api import get_dataset
from src.gen import train_test_from_null
from src.settings import DATA_PATH


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the raw train and test datasets for a given dataset.
    :return: train_dataset, test_dataset
    """
    # TODO: Abstract this, have a string input for dataset name, optional kwargs for train/test names.
    path = get_dataset("titanic")
    raw_train_data = pd.read_csv(path / "train.csv")
    raw_test_data = pd.read_csv(path / "test.csv")

    return raw_train_data, raw_test_data


def get_title(df: pd.DataFrame) -> pd.DataFrame:
    """
    Function to extract title from name
    :param df: Input titanic dataframe
    :return: Dataframe with encoded titles
    """
    # TODO: Function is specific to titanic dataset, currently no checks to validate format of input dataframe
    # TODO: Currently overworked, this should just extract title and other functions should deal with outliers and
    #  encoding.
    df["Title"] = df["Name"].str.extract(r",\s?(\w*).{1}")

    is_male = df["Sex"] == "male"
    is_female = df["Sex"] == "female"
    outlier_male = is_male & (~df["Title"].isin(["Mr", "Master"]))
    df.loc[outlier_male, "Title"] = "Mr"

    # All men under 18 = Master, over = Mr
    df.loc[is_male & (df["Age"] >= 18), "Title"] = "Mr"
    df.loc[is_male & (df["Age"] < 18), "Title"] = "Master"

    outlier_female = is_female & (~df["Title"].isin(["Miss", "Mrs"]))
    df.loc[outlier_female, "Title"] = "Mrs"

    # All women over 18 = Mrs, under = Miss
    df.loc[is_female & (df["Age"] >= 18), "Title"] = "Mrs"
    df.loc[is_female & (df["Age"] < 18), "Title"] = "Miss"
    out = pd.get_dummies(df["Title"], drop_first=True)

    return out


def prepare_dataset_pandas(dfs: list[pd.DataFrame], scale=True, drop=None, target=None) -> list[pd.DataFrame]:
    """
    Wrangle dataset to get necessary features using pandas.
    :param dfs: Input datasets to be wrangled where the training dataset is the first item in the list to allow
        scaler to be fit.
    :param scale: Scale data based on min-max.
    :param drop: Columns to drop.
    :param target: Columns to be predicted. These will not be scaled.
    :return: Prepared datasets.
    """

    # numerical_columns = ["Fare"]
    # ordinal_columns = ["Pclass", "Age", "SibSp", "Parch"]
    categorical_columns = ["Title", "Embarked"]

    scaler = StandardScaler()

    out_df = []
    for i, df in enumerate(dfs):

        if drop is not None:
            df = df.drop(drop, axis=1)

        df["SibSp"] = df["SibSp"].clip(upper=3)
        df["Parch"] = df["Parch"].clip(upper=2)

        # Get one-hot vectors for categorical variables
        df = pd.get_dummies(df, columns=categorical_columns, drop_first=True)

        if scale:
            # TODO: This should be predefined but get_dummies creates additional labels, find workaround
            scale_columns = [c for c in df.columns if target is not None and c not in target]

            if i == 0:
                scaled_data = scaler.fit_transform(df[scale_columns])
            else:
                scaled_data = scaler.transform(df[scale_columns])

            df[scale_columns] = scaled_data

        out_df.append(df)

    return out_df


if __name__ == "__main__":

    clean_comb_data = pd.read_csv(DATA_PATH / "titanic" / "all_data_clean.csv", index_col=0)

    clean_train_data, clean_test_data = train_test_from_null(clean_comb_data, "Survived")
    train_data = prepare_dataset_pandas(clean_train_data)
