import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score

# Import Dataset
matches = pd.read_csv("matches.csv", index_col = 0)

# Data Preparing
matches["Date"] = pd.to_datetime(matches["Date"])
matches["Target"] = (matches["Result"] == "W").astype("int")
matches["Venue_code"] = matches["Venue"].astype("category").cat.codes
matches["Opp_code"] = matches["Opponent"].astype("category").cat.codes
matches["hour"] = matches["Time"].str.replace(":.+", "", regex=True).astype("int")
matches["Day_code"] = matches["Date"].dt.dayofweek

# Data Modelling for Machine Learning
# Random Forest Classification
rf = RandomForestClassifier(n_estimators=1000, min_samples_split=4, random_state=1)
train_dataset = matches[matches["Date"] <= '2022-03-01']
test_dataset = matches[matches["Date"] > '2022-03-01']
predictors = ["Venue_code", "Opp_code", "hour", "Day_code"]
rf.fit(train_dataset[predictors], train_dataset["Target"])
preds = rf.predict(test_dataset[predictors])

combined = pd.DataFrame(dict(actual=test_dataset["Target"], predicted=preds))
pd.crosstab(index=combined["actual"], columns=combined["predicted"])

# Testing Model Result
accuracy_error = accuracy_score(test_dataset["Target"], preds)
prec_score = precision_score(test_dataset["Target"], preds)

grouped_matches = matches.groupby("Team")
group = grouped_matches.get_group("Real Madrid").sort_values("Date")

# Enhancement ML Model
def calculate_med(group, cols, derived_columns):
    group = group.sort_values("Date")
    calculate_stats = group[cols].rolling(5, closed='left').mean()
    group[derived_columns] = calculate_stats
    group = group.dropna(subset=derived_columns)
    return group


# Combining Average Model
cols = ["GF", "GA", "Sh", "SoT", "Dist", "FK", "PK", "PKatt"]
derived_columns = [f"{c}_rolling" for c in cols]
calculate_med(group, cols, derived_columns)
combine_matches = matches.groupby("Team").apply(lambda x: calculate_med(x, cols, derived_columns))
combine_matches = combine_matches.droplevel('Team')
combine_matches.index = range(combine_matches.shape[0])

# Prediction
def make_predictions(data, predictors):
    train_dataset = data[data["Date"] < '2022-01-01']
    test_dataset = data[data["Date"] > '2022-01-01']
    rf.fit(train_dataset[predictors], train_dataset["Target"])
    preds = rf.predict(test_dataset[predictors])
    combined = pd.DataFrame(dict(actual=test_dataset["Target"], predicted=preds), index=test_dataset.index)
    error = precision_score(test_dataset["Target"], preds)
    return combined, error


combined, error = make_predictions(combine_matches, predictors + derived_columns)
combined = combined.merge(combine_matches[["Date", "Team", "Opponent", "Result"]], left_index=True, right_index=True)
merged = combined.merge(combined, left_on=["Date", "Team"], right_on=["Date", "Opponent"])
merged = merged[(merged["predicted_x"] == 1) & (merged["predicted_y"] ==0)]["actual_x"].value_counts()

print(merged)



