# recipe_model.py
from transformers import pipeline

# Load the pre-trained model
generator = pipeline('text-generation', model='gpt2')

def generate_recipe(ingredients, meal_type, cuisine, time_limit):
    # Refine the prompt with detailed instructions
    prompt = (f"Generate a detailed and accurate {cuisine} {meal_type} recipe with the following ingredients: "
              f"{', '.join(ingredients)}. The recipe should be prepared in less than {time_limit} minutes and include "
              "clear, step-by-step instructions. Ensure that the recipe is highly relevant to the given ingredients.")
    generated_text = generator(prompt, max_length=400, num_return_sequences=1)[0]['generated_text']
    
    # Post-process to remove any unwanted text and format as steps
    recipe = generated_text.split("Recipe:")[-1].split("Related:")[0].split("Image Source")[0].strip()
    
    # Convert the recipe to a list of steps
    steps = recipe.split('. ')
    formatted_recipe = [step.strip() for step in steps if step.strip()]
    
    return formatted_recipe