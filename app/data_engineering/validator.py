class DataValidator:

    REQUIRED_COLUMNS = [

        "age",
        "job",
        "marital",
        "education",
        "default",
        "housing",
        "loan",
        "contact",
        "month",
        "day_of_week",
        "duration",
        "campaign",
        "pdays",
        "previous",
        "poutcome",
        "emp.var.rate",
        "cons.price.idx",
        "cons.conf.idx",
        "euribor3m",
        "nr.employed",
        "y"

    ]

    def validate_columns(self, dataframe):

        missing_columns = []

        for column in self.REQUIRED_COLUMNS:

            if column not in dataframe.columns:

                missing_columns.append(column)

        if missing_columns:

            raise Exception(
                f"Missing columns: {missing_columns}"
            )

        print("Dataset validation successful.")