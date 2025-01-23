from flask import Flask, render_template, request, jsonify
from recipe_model import RecipeGenerator
import os
import pyttsx3

app = Flask(__name__)
recipe_generator = RecipeGenerator()

@app.route("/api/videos", methods=["POST"])
def get_recipe_videos():
    data = request.json
    recipe_name = data.get("recipe_name", "")
    
    # Mock video data - replace with actual video database/API
    videos = [
        {
            "title": f"How to make {recipe_name}",
            "url": "/static/videos/recipe1.mp4",
            "thumbnail": "/static/thumbnails/recipe1.jpg",
            "duration": "5:30"
        },
        {
            "title": f"{recipe_name} Quick Recipe",
            "url": "/static/videos/recipe2.mp4", 
            "thumbnail": "/static/thumbnails/recipe2.jpg",
            "duration": "3:45"
        }
    ]
    
    return jsonify({"videos": videos})

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/api/recipes", methods=["POST"])
def get_recipes():
    try:
        data = request.json
        main_ingredient = data.get("ingredient", "")
        side_ingredient = data.get("sideIngredient", "")
        offset = data.get("offset", 0)
        
        if not main_ingredient:
            return jsonify({"error": "Main ingredient is required"}), 400
            
        recipes = recipe_generator.generate_dominant_recipes(
            main_ingredient,
            side_ingredient if side_ingredient else None,
            offset=offset
        )
        
        if not recipes:
            return jsonify({"error": "No recipes found"}), 404
            
        return jsonify({"recipes": recipes})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/speak", methods=["POST"])
def speak_recipe():
    try:
        recipe_text = request.json.get("text", "")
        if not recipe_text:
            return jsonify({"error": "No text provided"}), 400

        audio_dir = os.path.join(app.static_folder, "audio")
        os.makedirs(audio_dir, exist_ok=True)
        filename = f"recipe_{hash(recipe_text)}.mp3"
        audio_path = os.path.join(audio_dir, filename)

        if not os.path.exists(audio_path):
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.setProperty('volume', 0.9)
            engine.save_to_file(recipe_text, audio_path)
            engine.runAndWait()

        return jsonify({
            "status": "success",
            "audio_url": f"/static/audio/{filename}"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
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
