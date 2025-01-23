import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import ast
from typing import List, Dict, Optional
import pickle
import os
from tqdm import tqdm
import gc
import h5py
import warnings
warnings.filterwarnings('ignore')

class RecipeGenerator:
    def __init__(self):
        self.cache_dir = 'cache'
        os.makedirs(self.cache_dir, exist_ok=True)
        
        print("Loading sentence transformer model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        self.recipes_df, self.embedding_file = self._load_or_create_cache()
        self.h5_file = h5py.File(self.embedding_file, 'r')
        self.embeddings = self.h5_file['embeddings']

    def __del__(self):
        if hasattr(self, 'h5_file'):
            self.h5_file.close()

    def _load_dataset(self) -> pd.DataFrame:
        print("Loading and preprocessing dataset...")
        recipes = pd.read_csv('RAW_recipes.csv')
        
        recipes['ingredients'] = recipes['ingredients'].apply(ast.literal_eval)
        recipes['steps'] = recipes['steps'].apply(ast.literal_eval)
        
        recipes = recipes[['name', 'ingredients', 'steps', 'minutes']].drop_duplicates(subset=['name'])
        
        recipes = recipes[
            (recipes['ingredients'].apply(len) <= 30) & 
            (recipes['steps'].apply(len) <= 40) &
            (recipes['minutes'] <= 300)
        ]
        
        recipes = recipes.head(100000)
        recipes['difficulty'] = recipes.apply(self._calculate_difficulty, axis=1)
        
        return recipes

    def _calculate_difficulty(self, row):
        num_steps = len(row['steps'])
        num_ingredients = len(row['ingredients'])
        
        if num_steps <= 5 and num_ingredients <= 5:
            return "Easy"
        elif num_steps >= 12 or num_ingredients >= 12:
            return "Hard"
        else:
            return "Medium"

    def _create_embeddings_batch(self, texts: List[str], output_file: str, batch_size: int = 64):
        total_batches = len(texts) // batch_size + (1 if len(texts) % batch_size else 0)
        embedding_size = self.model.encode(['test'])[0].shape[0]
        
        with h5py.File(output_file, 'w') as f:
            dset = f.create_dataset('embeddings', 
                                  shape=(len(texts), embedding_size),
                                  dtype='float32',
                                  chunks=True)
            
            for i in tqdm(range(0, len(texts), batch_size), desc="Creating embeddings"):
                batch = texts[i:i + batch_size]
                batch_embeddings = self.model.encode(batch)
                dset[i:i + len(batch)] = batch_embeddings
                del batch_embeddings
                gc.collect()

    def _load_or_create_cache(self):
        recipe_cache = os.path.join(self.cache_dir, 'recipes_100k.pkl')
        embedding_cache = os.path.join(self.cache_dir, 'embeddings_100k.h5')
        
        if os.path.exists(recipe_cache) and os.path.exists(embedding_cache):
            print("Loading cached recipe data...")
            with open(recipe_cache, 'rb') as f:
                recipes_df = pickle.load(f)
            return recipes_df, embedding_cache
        
        print("Creating new recipe cache...")
        recipes_df = self._load_dataset()
        
        with open(recipe_cache, 'wb') as f:
            pickle.dump(recipes_df, f)
        
        print("Creating embeddings (this will take a while)...")
        ingredient_texts = [' '.join(ingredients) for ingredients in recipes_df['ingredients']]
        self._create_embeddings_batch(ingredient_texts, embedding_cache)
        
        return recipes_df, embedding_cache

    def generate_dominant_recipes(self, main_ingredient, side_ingredient=None, count=3, offset=0):
        filtered_df = self.recipes_df[self.recipes_df['ingredients'].apply(
            lambda x: any(main_ingredient.lower() in ing.lower() for ing in x[:2])
        )]
        
        if side_ingredient:
            filtered_df = filtered_df[filtered_df['ingredients'].apply(
                lambda x: any(side_ingredient.lower() in ing.lower() for ing in x)
            )]
        
        if len(filtered_df) < count:
            filtered_df = self.recipes_df[self.recipes_df['ingredients'].apply(
                lambda x: any(main_ingredient.lower() in ing.lower() for ing in x)
            )]
            if side_ingredient:
                filtered_df = filtered_df[filtered_df['ingredients'].apply(
                    lambda x: any(side_ingredient.lower() in ing.lower() for ing in x)
                )]
        
        recipes = filtered_df.iloc[offset:offset + count]
        
        return [{
            'name': row['name'],
            'description': f"A {row['difficulty'].lower()} recipe that takes {self._format_time(row['minutes'])} to prepare.",
            'ingredients': row['ingredients'],
            'instructions': row['steps'],
            'cooking_time': self._format_time(row['minutes']),
            'difficulty': row['difficulty']
        } for _, row in recipes.iterrows()]

    def _format_time(self, minutes: int) -> str:
        if minutes < 60:
            return f"{minutes} minutes"
        hours = minutes // 60
        mins = minutes % 60
        if mins == 0:
            return f"{hours} hour{'s' if hours > 1 else ''}"
        return f"{hours} hour{'s' if hours > 1 else ''} {mins} minutes"
