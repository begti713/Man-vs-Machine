import csv
import io
import os
import time
import requests
from google import genai
from google.genai import types
from PIL import Image

# --- Configuration ---
API_KEY = "YOUR_GEMINI_API_KEY"
SPREADSHEET_ID = "YOUR_SPREADSHEET_ID_HERE"
OUTPUT_FOLDER = "sheet_generated_images"

client = genai.Client(api_key=API_KEY)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv"

print(f"Starting live monitor. Saving images to '{OUTPUT_FOLDER}'.")
print("Press Ctrl+C in this terminal to stop the script.\n")

# The infinite loop that keeps the script running live
while True:
    try:
        # 1. Download the latest version of the Google Sheet
        response = requests.get(csv_url)
        
        if response.status_code == 200:
            csv_file = io.StringIO(response.text)
            reader = csv.DictReader(csv_file)
            
            # 2. Check every row in the sheet
            for idx, row in enumerate(reader, start=1):
                prompt = row.get("prompt", "").strip()
                custom_name = row.get("file_name", f"image_{idx}").strip()
                ratio = row.get("aspect_ratio", "1:1").strip() or "1:1"
                
                # Skip empty rows
                if not prompt:
                    continue
                
                output_path = os.path.join(OUTPUT_FOLDER, f"{custom_name}.png")
                
                # 3. THE MAGIC TRICK: Check if we already did this one
                if os.path.exists(output_path):
                    continue # Skip to the next row immediately
                    
                # 4. If we made it here, it's a NEW prompt!
                print(f"[*] New prompt detected! Generating '{custom_name}'...")
                
                try:
                    img_response = client.models.generate_images(
                        model="imagen-3.0-generate-002",
                        prompt=prompt,
                        config=types.GenerateImagesConfig(
                            number_of_images=1,
                            aspect_ratio=ratio,
                        ),
                    )
                    
                    # Save the new image
                    img_data = img_response.generated_images[0].image.image_bytes
                    image = Image.open(io.BytesIO(img_data))
                    image.save(output_path)
                    print(f"    ✅ Saved to {output_path}\n")
                    
                    # Pause briefly after a successful generation to respect API limits
                    time.sleep(3) 
                    
                except Exception as e:
                    print(f"    ❌ Error generating '{custom_name}': {e}\n")
                    time.sleep(3)

        else:
            print(f"Failed to fetch sheet. HTTP Status: {response.status_code}")
            
    except Exception as e:
        print(f"Network error while checking the sheet: {e}")
        
   
    time.sleep(30)