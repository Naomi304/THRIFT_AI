import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

# Train on the real collected marketplace data (real_training_data.csv).
# The real data has brand, item_type, condition and an actual sale_price, but
# NO size column, so the model uses Brand + Item Type + Condition as features.
# Size is still collected in the UI for display/search but is not a model input.

DATA_FILE = "real_training_data.csv"
TARGET = "sale_price"


def clean_condition(value):
    """Normalize the messy real-world condition field to 'new' or 'used'.

    Returns None for junk values (shipping blurbs, stray attributes, NaN) so
    those rows can be dropped.
    """
    if not isinstance(value, str):
        return None
    v = value.strip().lower()
    if v.startswith("new"):          # "new", "new (other)"
        return "new"
    if v == "used":
        return "used"
    return None                       # drop anything else


def load_and_clean():
    df = pd.read_csv(DATA_FILE)

    # Keep only what we model + the target, drop rows missing essentials.
    df = df[["brand", "item_type", "condition", TARGET]].copy()
    df = df.dropna(subset=["brand", "item_type", TARGET])

    # Normalize condition and drop junk-condition rows.
    df["condition"] = df["condition"].apply(clean_condition)
    df = df.dropna(subset=["condition"])

    # Normalize text casing so lookups are predictable:
    #   brands title-ish as stored, item types lowercase.
    df["brand"] = df["brand"].astype(str).str.strip()
    df["item_type"] = df["item_type"].astype(str).str.strip().str.lower()

    # Drop non-positive / absurd prices.
    df = df[(df[TARGET] > 0) & (df[TARGET] <= 1000)]

    return df.reset_index(drop=True)


def train_models():
    print(f"Loading real data from {DATA_FILE} ...")
    df = load_and_clean()
    print(f"Usable rows after cleaning: {len(df)}")
    print(f"Brands: {sorted(df['brand'].unique())}")
    print(f"Item types: {sorted(df['item_type'].unique())}")
    print(f"Conditions: {sorted(df['condition'].unique())}")

    X = df[["brand", "item_type", "condition"]]
    y = df[TARGET]

    # One encoder shared across brand + item type (matches app lookup logic),
    # a separate one for condition.
    label_encoder = LabelEncoder()
    condition_encoder = LabelEncoder()

    label_encoder.fit(pd.concat([X["brand"], X["item_type"]]))
    condition_encoder.fit(X["condition"])

    X_encoded = pd.DataFrame({
        "Brand": label_encoder.transform(X["brand"]),
        "Item Type": label_encoder.transform(X["item_type"]),
        "Condition": condition_encoder.transform(X["condition"]),
    })

    X_train, X_test, y_train, y_test = train_test_split(
        X_encoded, y, test_size=0.2, random_state=42
    )

    print("Training Random Forest model...")
    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print("Model Performance:")
    print(f"  Mean Absolute Error: ${mae:.2f}")
    print(f"  R2 Score: {r2:.3f}")
    print(f"  (price median=${y.median():.2f}, mean=${y.mean():.2f})")

    print("Saving models...")
    joblib.dump(model, "price_predictor_model.pkl")
    joblib.dump(label_encoder, "label_encoder.pkl")
    joblib.dump(condition_encoder, "condition_encoder.pkl")
    print("Saved: price_predictor_model.pkl, label_encoder.pkl, condition_encoder.pkl")

    return model, label_encoder, condition_encoder


def test_model():
    print("\nTesting the trained model...")
    model = joblib.load("price_predictor_model.pkl")
    label_encoder = joblib.load("label_encoder.pkl")
    condition_encoder = joblib.load("condition_encoder.pkl")

    test_cases = [
        {"brand": "Nike", "item_type": "t-shirt", "condition": "used"},
        {"brand": "Levi's", "item_type": "jeans", "condition": "used"},
        {"brand": "Zara", "item_type": "jacket", "condition": "new"},
    ]

    for i, case in enumerate(test_cases, 1):
        try:
            b = label_encoder.transform([case["brand"]])[0]
            it = label_encoder.transform([case["item_type"]])[0]
            c = condition_encoder.transform([case["condition"]])[0]
            X = pd.DataFrame([[b, it, c]], columns=["Brand", "Item Type", "Condition"])
            price = model.predict(X)[0]
            print(f"Test {i}: {case['brand']} {case['item_type']} ({case['condition']}) -> ${price:.2f}")
        except ValueError as e:
            print(f"Test {i} failed: {e}")


if __name__ == "__main__":
    print("=== THRIFT_AI Model Training (real data) ===")
    try:
        train_models()
        test_model()
        print("\n[OK] Model training completed successfully!")
    except Exception as e:
        print(f"[ERROR] during training: {e}")
        raise
