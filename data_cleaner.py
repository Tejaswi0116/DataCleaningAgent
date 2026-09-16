import pandas as pd
import numpy as np
import sqlite3
import tempfile
import os
from sqlalchemy import create_engine


class DataCleaner:

    def __init__(self):
        self.df = None

    # =====================================================
    # LOAD FILE
    # =====================================================

    def load_file(self, file):

        filename = file.name.lower()

        # CSV
        if filename.endswith(".csv"):
            self.df = pd.read_csv(file)

        # Excel
        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            self.df = pd.read_excel(file)

        # JSON
        elif filename.endswith(".json"):
            self.df = pd.read_json(file)

        # Parquet
        elif filename.endswith(".parquet"):
            self.df = pd.read_parquet(file)

        # SQLite
        elif filename.endswith((".db", ".sqlite", ".sqlite3")):

            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=os.path.splitext(filename)[1]
            )

            temp_file.write(file.getbuffer())
            temp_file.close()

            connection = sqlite3.connect(temp_file.name)

            tables = pd.read_sql(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                AND name NOT LIKE 'sqlite_%'
                """,
                connection
            )

            if tables.empty:
                connection.close()
                os.unlink(temp_file.name)

                raise ValueError(
                    "No tables found in SQLite database."
                )

            table_name = tables.iloc[0]["name"]

            self.df = pd.read_sql(
                f'SELECT * FROM "{table_name}"',
                connection
            )

            connection.close()
            os.unlink(temp_file.name)

        else:

            raise ValueError(
                "Unsupported file format."
            )

        return self.df

    # =====================================================
    # LOAD MYSQL DATABASE
    # =====================================================

    def load_database(
        self,
        database_type,
        host,
        port,
        username,
        password,
        database,
        table
    ):

        if database_type == "MySQL":

            connection_string = (
                f"mysql+pymysql://"
                f"{username}:{password}@"
                f"{host}:{port}/{database}"
            )

        else:

            raise ValueError(
                "Unsupported database."
            )

        engine = create_engine(
            connection_string
        )

        try:

            self.df = pd.read_sql(
                f'SELECT * FROM `{table}`',
                engine
            )

        finally:

            engine.dispose()

        return self.df

    # =====================================================
    # ANALYZE DATA
    # =====================================================

    def analyze_data(self, df):

        result = []

        total = len(df)

        for col in df.columns:

            missing = int(
                df[col].isna().sum()
            )

            if total > 0:

                missing_percent = (
                    missing / total
                ) * 100

            else:

                missing_percent = 100

            if missing == 0:

                recommendation = "No Action"

            elif missing_percent > 40:

                recommendation = "Drop Column"

            elif pd.api.types.is_numeric_dtype(
                df[col]
            ):

                values = df[col].dropna()

                if len(values) > 1:

                    skewness = values.skew()

                    if abs(skewness) > 1:

                        recommendation = "Median"

                    else:

                        recommendation = "Mean"

                else:

                    recommendation = "Drop Column"

            else:

                recommendation = "Mode"

            result.append({

                "Column": col,

                "Data Type":
                    str(df[col].dtype),

                "Missing Values":
                    missing,

                "Missing %":
                    round(
                        missing_percent,
                        2
                    ),

                "Recommendation":
                    recommendation
            })

        return pd.DataFrame(result)

    # =====================================================
    # AUTO CLEAN
    # =====================================================

    def auto_clean(
        self,
        df,
        column_threshold=40,
        row_null_limit=5
    ):

        df = df.copy()

        dropped_columns = []

        removed_rows = 0

        # -------------------------------------------------
        # DROP HIGH MISSING COLUMNS
        # -------------------------------------------------

        for col in list(df.columns):

            if len(df) == 0:
                continue

            missing_percent = (
                df[col].isna().mean()
            ) * 100

            if missing_percent > column_threshold:

                df.drop(
                    columns=[col],
                    inplace=True
                )

                dropped_columns.append(col)

        # -------------------------------------------------
        # DROP ROWS WITH 5 OR MORE NULL VALUES
        # -------------------------------------------------

        if len(df.columns) > 0:

            null_count = df.isna().sum(axis=1)

            rows_to_remove = (
                null_count >= row_null_limit
            )

            removed_rows = int(
                rows_to_remove.sum()
            )

            df = df.loc[
                ~rows_to_remove
            ].copy()

        # -------------------------------------------------
        # FILL REMAINING NULL VALUES
        # -------------------------------------------------

        for col in list(df.columns):

            if not df[col].isna().any():
                continue

            # NUMERICAL
            if pd.api.types.is_numeric_dtype(
                df[col]
            ):

                values = df[col].dropna()

                if len(values) == 0:

                    df.drop(
                        columns=[col],
                        inplace=True
                    )

                    dropped_columns.append(col)

                    continue

                if len(values) > 1:

                    skewness = values.skew()

                else:

                    skewness = 0

                if abs(skewness) > 1:

                    fill_value = values.median()

                else:

                    fill_value = values.mean()

                df[col] = df[col].fillna(
                    fill_value
                )

            # CATEGORICAL
            else:

                mode = df[col].mode(
                    dropna=True
                )

                if not mode.empty:

                    df[col] = df[col].fillna(
                        mode.iloc[0]
                    )

        return (
            df,
            dropped_columns,
            removed_rows
        )

    # =====================================================
    # MANUAL CLEAN
    # =====================================================

    def manual_clean(
        self,
        df,
        strategy
    ):

        df = df.copy()

        numerical_columns = (
            df.select_dtypes(
                include=np.number
            ).columns
        )

        categorical_columns = (
            df.select_dtypes(
                exclude=np.number
            ).columns
        )

        # MEAN
        if strategy == "mean":

            for col in numerical_columns:

                if df[col].isna().any():

                    value = df[col].mean()

                    if pd.notna(value):

                        df[col] = df[col].fillna(
                            value
                        )

            for col in categorical_columns:

                if df[col].isna().any():

                    mode = df[col].mode(
                        dropna=True
                    )

                    if not mode.empty:

                        df[col] = df[col].fillna(
                            mode.iloc[0]
                        )

        # MEDIAN
        elif strategy == "median":

            for col in numerical_columns:

                if df[col].isna().any():

                    value = df[col].median()

                    if pd.notna(value):

                        df[col] = df[col].fillna(
                            value
                        )

            for col in categorical_columns:

                if df[col].isna().any():

                    mode = df[col].mode(
                        dropna=True
                    )

                    if not mode.empty:

                        df[col] = df[col].fillna(
                            mode.iloc[0]
                        )

        # MODE
        elif strategy == "mode":

            for col in df.columns:

                if df[col].isna().any():

                    mode = df[col].mode(
                        dropna=True
                    )

                    if not mode.empty:

                        df[col] = df[col].fillna(
                            mode.iloc[0]
                        )

        # DROP ROWS
        elif strategy == "drop_rows":

            df = df.dropna()

        # DROP COLUMNS
        elif strategy == "drop_columns":

            columns_to_drop = []

            for col in df.columns:

                missing_percent = (
                    df[col].isna().mean()
                ) * 100

                if missing_percent > 40:

                    columns_to_drop.append(col)

            if columns_to_drop:

                df = df.drop(
                    columns=columns_to_drop
                )

        return df

    # =====================================================
    # CLEAN DATA
    # =====================================================

    def clean_data(
        self,
        df,
        strategy="auto"
    ):

        if strategy == "auto":

            (
                cleaned_df,
                dropped_columns,
                removed_rows
            ) = self.auto_clean(
                df,
                column_threshold=40,
                row_null_limit=5
            )

        else:

            cleaned_df = self.manual_clean(
                df,
                strategy
            )

            dropped_columns = []

            removed_rows = 0

        # REMOVE DUPLICATES

        before_duplicates = len(
            cleaned_df
        )

        cleaned_df = (
            cleaned_df.drop_duplicates()
        )

        duplicates_removed = (
            before_duplicates
            - len(cleaned_df)
        )

        return (
            cleaned_df,
            dropped_columns,
            removed_rows,
            duplicates_removed
        )

    # =====================================================
    # QUICK CLEAN
    # =====================================================

    def quick_clean(
        self,
        df,
        strategy="auto"
    ):

        rows_before = len(df)

        columns_before = len(
            df.columns
        )

        missing_before = int(
            df.isna().sum().sum()
        )

        (
            cleaned_df,
            dropped_columns,
            removed_rows,
            duplicates_removed
        ) = self.clean_data(
            df,
            strategy
        )

        rows_after = len(
            cleaned_df
        )

        columns_after = len(
            cleaned_df.columns
        )

        missing_after = int(
            cleaned_df.isna().sum().sum()
        )

        stats = {

            "rows_before":
                rows_before,

            "rows_after":
                rows_after,

            "columns_before":
                columns_before,

            "columns_after":
                columns_after,

            "missing_before":
                missing_before,

            "missing_after":
                missing_after,

            "removed_rows":
                removed_rows,

            "duplicates_removed":
                duplicates_removed,

            "dropped_columns":
                dropped_columns
        }

        return cleaned_df, stats