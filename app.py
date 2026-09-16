import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from data_cleaner import DataCleaner
from google import genai


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="Data Cleaner Agent",
    page_icon="🧹",
    layout="wide"
)

st.title("🧹 Data Cleaner Agent")
st.write("AI-Based Data Cleaning and Analytics System")


# =========================================================
# GEMINI AI
# =========================================================

try:
    client = genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )
except Exception:
    client = None


# =========================================================
# SESSION STATE
# =========================================================

if "df" not in st.session_state:
    st.session_state.df = None

if "cleaned_df" not in st.session_state:
    st.session_state.cleaned_df = None

if "stats" not in st.session_state:
    st.session_state.stats = None

if "dashboard_generated" not in st.session_state:
    st.session_state.dashboard_generated = False

if "ai_insight" not in st.session_state:
    st.session_state.ai_insight = None


cleaner = DataCleaner()


# =========================================================
# SIDEBAR - DATA SOURCE
# =========================================================

st.sidebar.header("📂 Data Source")

source = st.sidebar.radio(
    "Select Data Source",
    [
        "Upload File",
        "MySQL"
    ]
)


# =========================================================
# UPLOAD FILE
# =========================================================

if source == "Upload File":

    uploaded_file = st.sidebar.file_uploader(
        "Choose Dataset",
        type=[
            "csv",
            "xlsx",
            "xls",
            "json",
            "parquet",
            "db",
            "sqlite",
            "sqlite3"
        ]
    )

    if uploaded_file is not None:

        # Prevent unnecessary reload on every rerun
        file_id = (
            uploaded_file.name,
            uploaded_file.size
        )

        if st.session_state.get("file_id") != file_id:

            try:

                df = cleaner.load_file(
                    uploaded_file
                )

                st.session_state.df = df
                st.session_state.cleaned_df = None
                st.session_state.stats = None
                st.session_state.dashboard_generated = False
                st.session_state.ai_insight = None
                st.session_state.file_id = file_id

                st.sidebar.success(
                    "✅ Dataset Loaded Successfully"
                )

            except Exception as e:

                st.sidebar.error(
                    f"❌ Error: {e}"
                )


# =========================================================
# MYSQL
# =========================================================

elif source == "MySQL":

    st.sidebar.subheader(
        "MySQL Connection"
    )

    host = st.sidebar.text_input(
        "Host",
        "localhost"
    )

    port = st.sidebar.text_input(
        "Port",
        "3306"
    )

    username = st.sidebar.text_input(
        "Username"
    )

    password = st.sidebar.text_input(
        "Password",
        type="password"
    )

    database = st.sidebar.text_input(
        "Database"
    )

    table = st.sidebar.text_input(
        "Table"
    )

    if st.sidebar.button(
        "🔌 Connect MySQL"
    ):

        try:

            df = cleaner.load_database(
                "MySQL",
                host,
                port,
                username,
                password,
                database,
                table
            )

            st.session_state.df = df
            st.session_state.cleaned_df = None
            st.session_state.stats = None
            st.session_state.dashboard_generated = False
            st.session_state.ai_insight = None

            st.sidebar.success(
                "✅ MySQL Connected"
            )

        except Exception as e:

            st.sidebar.error(
                f"❌ {e}"
            )




# =========================================================
# GEMINI TEST
# =========================================================

st.sidebar.markdown("---")

if st.sidebar.button(
    "🤖 Test Gemini API"
):

    if client is None:

        st.sidebar.error(
            "❌ Gemini API Key not found."
        )

    else:

        try:

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents="Say Hello in one simple sentence."
            )

            st.sidebar.success(
                "✅ Gemini API Connected!"
            )

            st.sidebar.write(
                response.text
            )

        except Exception as e:

            st.sidebar.error(
                f"❌ Gemini Error: {e}"
            )


# =========================================================
# CHECK DATASET
# =========================================================

df = st.session_state.df

if df is None:

    st.info(
        "👈 Please upload a dataset or connect to a database."
    )

    st.stop()


# =========================================================
# DATASET DASHBOARD
# =========================================================

st.header("📊 Dataset Dashboard")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "Total Rows",
        len(df)
    )

with c2:
    st.metric(
        "Total Columns",
        len(df.columns)
    )

with c3:
    st.metric(
        "Missing Values",
        int(df.isna().sum().sum())
    )

with c4:
    st.metric(
        "Duplicate Rows",
        int(df.duplicated().sum())
    )


# =========================================================
# ORIGINAL DATA
# =========================================================

st.subheader("👀 Original Dataset")

st.dataframe(
    df.head(20),
    use_container_width=True
)


# =========================================================
# DATA ANALYSIS
# =========================================================

st.header("🔍 Data Analysis")

analysis = cleaner.analyze_data(df)

st.dataframe(
    analysis,
    use_container_width=True
)


# =========================================================
# DATA CLEANING
# =========================================================

st.header("🧹 Data Cleaning")

cleaning_method = st.selectbox(
    "Select Cleaning Method",
    [
        "Auto Cleaning",
        "Mean",
        "Median",
        "Mode",
        "Drop Rows",
        "Drop Columns"
    ],
    key="cleaning_method"
)


strategy_map = {

    "Auto Cleaning": "auto",
    "Mean": "mean",
    "Median": "median",
    "Mode": "mode",
    "Drop Rows": "drop_rows",
    "Drop Columns": "drop_columns"

}


if st.button(
    "🚀 Start Cleaning",
    type="primary"
):

    try:

        strategy = strategy_map[
            cleaning_method
        ]

        cleaned_df, stats = cleaner.quick_clean(
            df,
            strategy
        )

        st.session_state.cleaned_df = cleaned_df
        st.session_state.stats = stats

        # New cleaning means new dashboard
        st.session_state.dashboard_generated = False
        st.session_state.ai_insight = None

        st.success(
            "✅ Data Cleaning Completed Successfully!"
        )

        st.rerun()

    except Exception as e:

        st.error(
            f"❌ Cleaning Error: {e}"
        )


# =========================================================
# GET CLEANED DATA FROM SESSION
# =========================================================

cleaned_df = st.session_state.cleaned_df


# =========================================================
# CLEANED DATA
# =========================================================

if cleaned_df is not None:

    st.header("✅ Cleaned Dataset")

    stats = st.session_state.stats

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:

        st.metric(
            "Rows Before",
            stats["rows_before"]
        )

    with c2:

        st.metric(
            "Rows After",
            stats["rows_after"]
        )

    with c3:

        st.metric(
            "Missing Before",
            stats["missing_before"]
        )

    with c4:

        st.metric(
            "Missing After",
            stats["missing_after"]
        )

    with c5:

        st.metric(
            "Duplicates Removed",
            stats["duplicates_removed"]
        )


    st.subheader(
        "📋 Cleaned Data Preview"
    )

    st.dataframe(
        cleaned_df.head(50),
        use_container_width=True
    )


    if stats["dropped_columns"]:

        st.warning(
            "Dropped Columns: "
            + ", ".join(
                stats["dropped_columns"]
            )
        )


    st.info(
        f"Rows Removed: {stats['removed_rows']}"
    )


# =========================================================
# AUTOMATIC VISUALIZATION DASHBOARD
# =========================================================

if cleaned_df is not None:

    st.markdown("---")

    st.header(
        "🤖 AI Automatic Visualization Dashboard"
    )

    st.write(
        "AI analyzes the cleaned dataset and generates "
        "useful visualizations automatically."
    )


    if st.button(
        "📊 Generate Dashboard",
        type="primary"
    ):

        st.session_state.dashboard_generated = True

        st.rerun()


    # =====================================================
    # SHOW DASHBOARD
    # =====================================================

    if st.session_state.dashboard_generated:

        st.success(
            "✅ Dashboard Generated Successfully!"
        )


        numeric_cols = list(
            cleaned_df.select_dtypes(
                include=np.number
            ).columns
        )

        categorical_cols = list(
            cleaned_df.select_dtypes(
                exclude=np.number
            ).columns
        )


        # =================================================
        # NUMERICAL DASHBOARD
        # =================================================

        if numeric_cols:

            st.subheader(
                "📈 Numerical Analysis"
            )

            chart_columns = st.columns(2)

            for i, column in enumerate(
                numeric_cols[:6]
            ):

                fig = px.histogram(
                    cleaned_df,
                    x=column,
                    title=f"Distribution of {column}",
                    marginal="box"
                )

                fig.update_layout(
                    height=400
                )

                with chart_columns[i % 2]:

                    st.plotly_chart(
                        fig,
                        use_container_width=True
                    )


        # =================================================
        # OUTLIER ANALYSIS
        # =================================================

        if numeric_cols:

            st.subheader(
                "📦 Outlier Analysis"
            )

            chart_columns = st.columns(2)

            for i, column in enumerate(
                numeric_cols[:6]
            ):

                fig = px.box(
                    cleaned_df,
                    y=column,
                    title=f"Box Plot - {column}"
                )

                fig.update_layout(
                    height=400
                )

                with chart_columns[i % 2]:

                    st.plotly_chart(
                        fig,
                        use_container_width=True
                    )


        # =================================================
        # CATEGORICAL ANALYSIS
        # =================================================

        if categorical_cols:

            st.subheader(
                "📊 Categorical Analysis"
            )

            chart_columns = st.columns(2)

            for i, column in enumerate(
                categorical_cols[:6]
            ):

                temp = (
                    cleaned_df[column]
                    .value_counts()
                    .head(10)
                    .reset_index()
                )

                temp.columns = [
                    column,
                    "Count"
                ]

                fig = px.bar(
                    temp,
                    x=column,
                    y="Count",
                    title=f"Count of {column}"
                )

                fig.update_layout(
                    height=400
                )

                with chart_columns[i % 2]:

                    st.plotly_chart(
                        fig,
                        use_container_width=True
                    )


        # =================================================
        # PIE CHART
        # =================================================

        if categorical_cols:

            column = categorical_cols[0]

            pie_data = (
                cleaned_df[column]
                .value_counts()
                .head(8)
                .reset_index()
            )

            pie_data.columns = [
                column,
                "Count"
            ]

            fig = px.pie(
                pie_data,
                names=column,
                values="Count",
                title=f"Distribution of {column}"
            )

            st.subheader(
                "🥧 Category Distribution"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


        # =================================================
        # BAR CHART
        # =================================================

        if (
            categorical_cols
            and numeric_cols
        ):

            category = categorical_cols[0]
            number = numeric_cols[0]

            temp = (
                cleaned_df
                .groupby(category)[number]
                .mean()
                .reset_index()
                .sort_values(
                    number,
                    ascending=False
                )
                .head(15)
            )

            fig = px.bar(
                temp,
                x=category,
                y=number,
                title=f"Average {number} by {category}"
            )

            st.subheader(
                "📊 Category vs Numerical"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


        # =================================================
        # SCATTER PLOT
        # =================================================

        if len(numeric_cols) >= 2:

            x_col = numeric_cols[0]
            y_col = numeric_cols[1]

            fig = px.scatter(
                cleaned_df,
                x=x_col,
                y=y_col,
                title=f"{x_col} vs {y_col}"
            )

            st.subheader(
                "🔵 Relationship Analysis"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


        # =================================================
        # CORRELATION HEATMAP
        # =================================================

        if len(numeric_cols) >= 2:

            correlation = (
                cleaned_df[numeric_cols]
                .corr()
            )

            fig = px.imshow(
                correlation,
                text_auto=True,
                aspect="auto",
                title="Correlation Heatmap"
            )

            st.subheader(
                "🔥 Correlation Analysis"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


        # =================================================
        # DATE / TIME TREND
        # =================================================

        date_columns = []

        for column in cleaned_df.columns:

            if (
                "date" in column.lower()
                or "time" in column.lower()
                or "year" in column.lower()
            ):

                date_columns.append(
                    column
                )


        if (
            date_columns
            and numeric_cols
        ):

            date_col = date_columns[0]
            value_col = numeric_cols[0]

            temp = cleaned_df.copy()

            try:

                temp[date_col] = pd.to_datetime(
                    temp[date_col]
                )

                temp = temp.sort_values(
                    date_col
                )

                fig = px.line(
                    temp,
                    x=date_col,
                    y=value_col,
                    title=f"{value_col} Trend Over Time"
                )

                st.subheader(
                    "📈 Trend Analysis"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            except Exception:
                pass


# =========================================================
# AI INSIGHTS
# =========================================================

if cleaned_df is not None:

    st.markdown("---")

    st.header(
        "🧠 AI Insights & Business Recommendations"
    )

    if st.button(
        "✨ Generate AI Insights"
    ):

        if client is None:

            st.error(
                "❌ Gemini API is not connected."
            )

        else:

            try:

                prompt = f"""

You are an expert Data Analyst.

Analyze this cleaned dataset.

Dataset Shape:
{cleaned_df.shape}

Columns:
{list(cleaned_df.columns)}

Data Types:
{cleaned_df.dtypes.to_string()}

Sample Data:
{cleaned_df.head(20).to_string(index=False)}

Statistical Summary:
{cleaned_df.describe(
    include="all"
).to_string()}

Give the analysis in these sections:

1. Dataset Overview
2. Important Patterns
3. Key Insights
4. Trends
5. Outlier Observations
6. Recommended Visualizations
7. Business Recommendations

Use simple language.
Do not invent information.
"""

                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt
                )

                st.session_state.ai_insight = (
                    response.text
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"❌ Gemini AI Error: {e}"
                )


    if st.session_state.ai_insight:

        st.markdown(
            st.session_state.ai_insight
        )


# =========================================================
# DOWNLOAD
# =========================================================

if cleaned_df is not None:

    st.markdown("---")

    st.header(
        "⬇️ Download Cleaned Dataset"
    )

    csv_data = cleaned_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="📥 Download Cleaned CSV",
        data=csv_data,
        file_name="cleaned_data.csv",
        mime="text/csv"
    )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "Data Cleaner Agent | "
    "AI-Based Data Cleaning, Visualization & Analytics"
)