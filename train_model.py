import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import os

def create_sample_data():
    """Create sample training data for clothing price prediction"""
    np.random.seed(42)
    
    # Sample brands
    brands = ['Nike', 'Adidas', 'H&M', 'Zara', 'Gap', 'Levi\'s', 'Tommy Hilfiger', 
              'Calvin Klein', 'Ralph Lauren', 'Gucci', 'Prada', 'Burberry']
    
    # Sample item types
    item_types = ['t-shirt', 'jeans', 'jacket', 'dress', 'shirt', 'sweater', 
                  'pants', 'skirt', 'blouse', 'coat', 'shorts', 'hoodie']
    
    # Sample sizes
    sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
    
    # Generate 1000 sample records
    n_samples = 1000
    data = []
    
    for _ in range(n_samples):
        brand = np.random.choice(brands)
        item_type = np.random.choice(item_types)
        size = np.random.choice(sizes)
        
        # Base price influenced by brand and item type
        brand_multiplier = {
            'Gucci': 8.0, 'Prada': 7.5, 'Burberry': 6.0,
            'Ralph Lauren': 3.0, 'Calvin Klein': 2.5, 'Tommy Hilfiger': 2.2,
            'Levi\'s': 2.0, 'Nike': 1.8, 'Adidas': 1.7,
            'Gap': 1.3, 'Zara': 1.2, 'H&M': 1.0
        }.get(brand, 1.5)
        
        item_base_price = {
            'coat': 150, 'jacket': 100, 'dress': 80, 'jeans': 70,
            'pants': 60, 'shirt': 45, 'blouse': 50, 'sweater': 65,
            'hoodie': 55, 't-shirt': 25, 'shorts': 35, 'skirt': 40
        }.get(item_type, 50)
        
        # Size multiplier (larger sizes might cost more)
        size_multiplier = {'XS': 1.0, 'S': 1.0, 'M': 1.0, 'L': 1.1, 'XL': 1.15, 'XXL': 1.2}.get(size, 1.0)
        
        # Calculate price with some randomness
        base_price = item_base_price * brand_multiplier * size_multiplier
        price = max(10, base_price + np.random.normal(0, base_price * 0.2))  # Add 20% variance
        
        data.append({
            'Brand': brand,
            'Item Type': item_type,
            'Size': size,
            'Price': round(price, 2)
        })
    
    return pd.DataFrame(data)

def train_models():
    """Train ML models and save them"""
    print("Creating sample training data...")
    df = create_sample_data()
    
    print(f"Dataset shape: {df.shape}")
    print(f"Sample data:\n{df.head()}")
    
    # Prepare features and target
    X = df[['Brand', 'Item Type', 'Size']]
    y = df['Price']
    
    # Create label encoders
    print("Creating label encoders...")
    label_encoder = LabelEncoder()
    size_encoder = LabelEncoder()
    
    # Encode categorical features
    all_categories = pd.concat([X['Brand'], X['Item Type']])
    label_encoder.fit(all_categories)
    
    # Encode Size separately
    size_encoder.fit(X['Size'])
    
    # Transform the data
    X_encoded = pd.DataFrame({
        'Brand': label_encoder.transform(X['Brand']),
        'Item Type': label_encoder.transform(X['Item Type']),
        'Size': size_encoder.transform(X['Size'])
    })
    
    print(f"Encoded features shape: {X_encoded.shape}")
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(
        X_encoded, y, test_size=0.2, random_state=42
    )
    
    # Train the model
    print("Training Random Forest model...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate the model
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"Model Performance:")
    print(f"Mean Absolute Error: ${mae:.2f}")
    print(f"R² Score: {r2:.3f}")
    
    # Save the models
    print("Saving models...")
    joblib.dump(model, 'price_predictor_model.pkl')
    joblib.dump(label_encoder, 'label_encoder.pkl')
    joblib.dump(size_encoder, 'size_encoder.pkl')
    
    # Also save the training data for reference
    df.to_csv('training_data.csv', index=False)
    
    print("Models saved successfully!")
    print("Files created:")
    print("- price_predictor_model.pkl")
    print("- label_encoder.pkl")
    print("- size_encoder.pkl")
    print("- training_data.csv")
    
    return model, label_encoder, size_encoder

def test_model():
    """Test the trained model with sample predictions"""
    print("\nTesting the trained model...")
    
    # Load the saved models
    model = joblib.load('price_predictor_model.pkl')
    label_encoder = joblib.load('label_encoder.pkl')
    size_encoder = joblib.load('size_encoder.pkl')
    
    # Test cases
    test_cases = [
        {'brand': 'Nike', 'item_type': 't-shirt', 'size': 'M'},
        {'brand': 'Gucci', 'item_type': 'jacket', 'size': 'L'},
        {'brand': 'H&M', 'item_type': 'jeans', 'size': 'S'},
    ]
    
    for i, case in enumerate(test_cases, 1):
        try:
            brand_encoded = label_encoder.transform([case['brand']])[0]
            item_type_encoded = label_encoder.transform([case['item_type']])[0]
            size_encoded = size_encoder.transform([case['size']])[0]
            
            input_data = pd.DataFrame([[brand_encoded, item_type_encoded, size_encoded]], 
                                    columns=['Brand', 'Item Type', 'Size'])
            
            predicted_price = model.predict(input_data)[0]
            
            print(f"Test {i}: {case['brand']} {case['item_type']} (size {case['size']}) -> ${predicted_price:.2f}")
            
        except ValueError as e:
            print(f"Test {i} failed: {e}")

if __name__ == "__main__":
    print("=== THRIFT_AI Model Training ===")
    
    try:
        # Train the models
        model, label_encoder, size_encoder = train_models()
        
        # Test the models
        test_model()
        
        print("\n✅ Model training completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during training: {e}")
        raise