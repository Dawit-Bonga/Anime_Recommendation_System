import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD
import joblib
import os

DATA_PATH = '../data/clean_ratings.csv' 
MODEL_PATH = '../models/svd_model.pkl'

#---Configiratuion and loading-----
print("STEP 1: Loadinf Dataa-------")

if not os.path.exists(DATA_PATH):
    print(f"Error: Could not find {DATA_PATH}. Did you move the file to the 'data' folder?")
    exit()


dtype_dict = {
    'score': 'float32',   # Uses half the memory of standard numbers
    'anime_id': 'int32'   # Sufficient for IDs up to 2 billion
}
use_cols = ['username', 'anime_id', 'score']


#this is loading the data
df = pd.read_csv(DATA_PATH, dtype=dtype_dict,usecols=use_cols)
print(f"Loaded {len(df):,} ratings successfully.")



print("STEP 2: Mapping IDS----------")
#this is so usernames are converted into something the AI can read/undertsand
df['user_idx'] = df['username'].astype('category').cat.codes

unique_anime_ids = df['anime_id'].unique()

anime_id_to_idx = {anime_id: i for i, anime_id in enumerate(unique_anime_ids)}
idx_to_anime_id = {i: anime_id for anime_id, i in anime_id_to_idx.items()}

df['anime_idx'] = df['anime_id'].map(anime_id_to_idx)

print(f"Unique Users: {df['user_idx'].nunique():,}")
print(f"Unique Animes: {df['anime_idx'].nunique():,}")

print("\n--- STEP 3: CREATING SPARSE MATRIX ---")

user_item_matrix = csr_matrix(
    (df['score'], (df['user_idx'], df['anime_idx'])), 
    shape=(df['user_idx'].nunique(), len(unique_anime_ids))
)
print(f"Matrix Shape: {user_item_matrix.shape} (Users x Animes)")

print("\n--- STEP 4: TRAINING THE BRAIN (SVD) ---")
print("Crunching the numbers... (This usually takes 2-5 minutes)")

svd = TruncatedSVD(n_components=50, random_state=42)

# This learns the relationship between users and those 50 features
svd.fit(user_item_matrix)

print("Training Complete!")
print(f"Explained Variance: {svd.explained_variance_ratio_.sum():.4f}") 

print("\n--- STEP 5: SAVING THE BRAIN ---")
# We save the model AND the ID mappings into one file.
# The App needs the mappings to know that ID 55 = "Naruto"
save_data = {
    'model': svd,
    'matrix': user_item_matrix,        # Optional: We might need this for 'Similar Users' later
    'anime_id_to_idx': anime_id_to_idx,
    'idx_to_anime_id': idx_to_anime_id
}

joblib.dump(save_data, MODEL_PATH)
print(f"SUCCESS! Model saved to {MODEL_PATH}")

