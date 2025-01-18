from flask import Flask, render_template, request
from recipe_model import generate_recipe
import pyttsx3

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        ingredients = request.form.get("ingredients").split(",")
        meal_type = request.form.get("meal_type")
        cuisine = request.form.get("cuisine")
        time_limit = request.form.get("time_limit")
        recipe = generate_recipe(ingredients, meal_type, cuisine, time_limit)
        return render_template("index.html", recipe=recipe)
    return render_template("index.html", recipe="")

@app.route("/play_recipe", methods=["POST"])
def play_recipe():
    recipe_text = request.form.get("recipe")
    
    # Initialize pyttsx3 engine
    engine = pyttsx3.init()
    # Set properties (optional)
    engine.setProperty('rate', 150)  # Speed percent (can go over 100)
    engine.setProperty('volume', 0.9)  # Volume 0-1
    
    # Save the recipe to an audio file and play it
    engine.save_to_file(recipe_text, 'recipe.mp3')
    engine.runAndWait()
    
    # Play the saved file (or you can directly speak it without saving)
    engine.say(recipe_text)
    engine.runAndWait()
    
    return "Playing recipe..."

if __name__ == "__main__":
    app.run(debug=True)