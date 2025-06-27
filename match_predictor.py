import pandas as pd
import numpy as np
import glob, os
import warnings
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, classification_report

# Suppress specific pandas datetime parsing warnings
warnings.filterwarnings(
    "ignore",
    message="Parsing dates in %"
)


def convert_to_float(value):
    """Convert strings (including percentages and 'No information') to floats."""
    if isinstance(value, str):
        if value == 'No information':
            return np.nan
        if '%' in value:
            return float(value.rstrip('%'))
    return float(value) if pd.notnull(value) else np.nan


def load_and_process_data(directory='game stats cleaned'):
    """Load CSVs, robustly parse dates, and return a DataFrame of match records."""
    files = glob.glob(os.path.join(directory, "*_Combined_Performance.csv"))
    records = []
    for path in files:
        team = os.path.basename(path).replace('_Combined_Performance.csv', '')
        df = pd.read_csv(path)
        for _, row in df.iterrows():
            date_str = str(row.get('Date', ''))
            match_date = None
            for fmt in ('%d/%m/%Y, %H:%M', '%m/%d/%Y, %H:%M', '%Y-%m-%d %H:%M:%S'):
                try:
                    match_date = pd.to_datetime(date_str, format=fmt)
                    break
                except ValueError:
                    continue
            if match_date is None:
                match_date = pd.to_datetime(date_str, dayfirst=False,
                                           infer_datetime_format=True, errors='coerce')
            rec = {
                'team': team,
                'opponent': row.get('Opponent', np.nan),
                'date': match_date,
                'possession': convert_to_float(row.get('Ball possession For', np.nan)),
                'shots_for': convert_to_float(row.get('Total shots For', np.nan)),
                'shots_on_target_for': convert_to_float(row.get('Shots on target For', np.nan)),
                'passes_for': convert_to_float(row.get('Passes For', np.nan)),
                'accurate_passes_for': convert_to_float(row.get('Accurate passes For', np.nan)),
                'tackles_for': convert_to_float(row.get('Tackles For', np.nan)),
                'interceptions_for': convert_to_float(row.get('Interceptions For', np.nan)),
                'goals_for': convert_to_float(row.get('Goals For', np.nan)),
                'goals_against': convert_to_float(row.get('Goals Against', np.nan))
            }
            if pd.notnull(rec['goals_for']) and pd.notnull(rec['goals_against']):
                records.append(rec)
    df = pd.DataFrame(records)
    nums = df.select_dtypes(include=[np.number]).columns
    df[nums] = df[nums].fillna(df[nums].median())
    return df


def compute_match_features_and_labels(df):
    """Generate symmetric features and labels using only past data for each match."""
    X, y = [], []
    for _, row in df.iterrows():
        t, o, d = row['team'], row['opponent'], row['date']
        team1, team2 = sorted([t, o])
        if t == team1:
            label = 1 if row['goals_for'] > row['goals_against'] else (-1 if row['goals_for'] < row['goals_against'] else 0)
        else:
            label = 1 if row['goals_against'] > row['goals_for'] else (-1 if row['goals_against'] < row['goals_for'] else 0)
        past1 = df[(df['team'] == team1) & (df['date'] < d)]
        past2 = df[(df['team'] == team2) & (df['date'] < d)]
        if past1.empty or past2.empty:
            continue
        def stats(past_df):
            return [
                past_df['goals_for'].mean(),
                past_df['goals_against'].mean(),
                past_df['possession'].mean(),
                past_df['shots_for'].mean(),
                past_df['shots_on_target_for'].mean(),
                past_df['passes_for'].mean(),
                (past_df['goals_for'] > past_df['goals_against']).mean()
            ]
        feat1 = stats(past1)
        feat2 = stats(past2)
        X.append(feat1 + feat2)
        y.append(label)
    return np.array(X), np.array(y)


def create_features_for_match(team1, team2, df):
    """Compute features for a single hypothetical match between team1 and team2."""
    def stats(past_df):
        return [
            past_df['goals_for'].mean(),
            past_df['goals_against'].mean(),
            past_df['possession'].mean(),
            past_df['shots_for'].mean(),
            past_df['shots_on_target_for'].mean(),
            past_df['passes_for'].mean(),
            (past_df['goals_for'] > past_df['goals_against']).mean()
        ]
    now = pd.Timestamp.now()
    past1 = df[(df['team'] == team1) & (df['date'] < now)]
    past2 = df[(df['team'] == team2) & (df['date'] < now)]
    if past1.empty or past2.empty:
        return None
    feat1 = stats(past1)
    feat2 = stats(past2)
    return np.array(feat1 + feat2)


def train_model():
    df = load_and_process_data()
    X, y = compute_match_features_and_labels(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_leaf=5,
        class_weight='balanced',
        random_state=42
    )
    cv_scores = cross_val_score(model, X_train, y_train, cv=5)
    print(f"5-fold CV accuracy: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
    model.fit(X_train, y_train)
    print(f"Train accuracy: {model.score(X_train, y_train):.3f}")
    print(f"Test accuracy: {model.score(X_test, y_test):.3f}")
    preds = model.predict(X_test)
    print("Confusion Matrix:\n", confusion_matrix(y_test, preds))
    print(classification_report(y_test, preds))
    return model, scaler, df


if __name__ == "__main__":
    # Train and retrieve data
    model, scaler, df = train_model()

    # Interactive prediction loop
    print("\nEnter two team names separated by a comma to get a prediction (or 'exit' to quit):")
    while True:
        user_input = input("Team1,Team2: ").strip()
        if user_input.lower() in ('exit', 'quit'):
            break
        try:
            team1, team2 = [t.strip() for t in user_input.split(',')]
        except ValueError:
            print("Please enter exactly two team names separated by a comma.")
            continue
        features = create_features_for_match(team1, team2, df)
        if features is None:
            print(f"No historical data for one or both teams: {team1}, {team2}")
            continue
        feats_scaled = scaler.transform([features])
        pred = model.predict(feats_scaled)[0]
        probs = model.predict_proba(feats_scaled)[0]
        outcome = {1: f"{team1} wins", 0: "Draw", -1: f"{team2} wins"}[pred]
        print(f"Prediction: {outcome}")
        print(f"Probabilities -> {team1}: {probs[]:.2f}, Draw: {probs[1]:.2f}, {team2}: {probs[0]:.2f}\n")
