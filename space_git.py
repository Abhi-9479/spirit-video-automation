import os
import gspread
import google.generativeai as genai
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
import time
import random
from moviepy.editor import *
from moviepy.config import change_settings
from google.generativeai.types import GenerationConfig
# Add this with your other imports
from upload_video import get_authenticated_service, upload_video
from upload_video import get_authenticated_service, upload_video, update_video_details
# --- SETUP AND AUTHENTICATION (Identical to previous version) ---
import os
import sys

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'credentials.json'
load_dotenv()
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    print("✅ Gemini AI Authenticated Successfully.")
except Exception as e: exit(f"❌ ERROR: Gemini AI Auth Failed. {e}")
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    gspread_client = gspread.authorize(creds)
    sheet = gspread_client.open("yt_story").sheet1
    print("✅ Google Sheets Authenticated and Opened Successfully.")
except Exception as e: exit(f"❌ ERROR: Google Sheets Auth Failed. {e}")


# --- AI & AUTOMATION FUNCTIONS ---

def setup_environment():
    """Configure environment for GitHub Actions or local development"""
    if os.getenv('GITHUB_ACTIONS'):
        print("🤖 Running in GitHub Actions automation mode")
        # Configure ImageMagick for Linux
        try:
            from moviepy.config import change_settings
            change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})
            print("✅ ImageMagick configured for Linux")
        except Exception as e:
            print(f"⚠️ ImageMagick setup warning: {e}")
        return True
    else:
        print("💻 Running in local development mode")
        # Your existing Windows ImageMagick setup
        try:
            from moviepy.config import change_settings
            change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})
        except Exception:
            print("⚠️ ImageMagick path not configured for Windows. Text may fail.")
        return False

def get_user_choice():
    """Get user choice, auto-select for automation"""
    if os.getenv('GITHUB_ACTIONS'):
        print("🚀 Auto-selecting option 2: Generate, Upload, and Update video")
        return '2'
    else:
        print("\n--- AI YouTube Shorts Factory ---")
        print("1: Generate a new video and save it locally.")
        print("2: Generate, Upload, and Update a new video on YouTube.")
        return input("Enter your choice (1 or 2): ")

def verify_media_files():
    """Verify that media files are available"""
    music_files = [f for f in os.listdir('space_music') if f.endswith('.mp3')] if os.path.exists('space_music') else []
    video_files = [f for f in os.listdir('space_temp') if f.endswith('.mp4')] if os.path.exists('space_temp') else []
    
    print(f"📁 Found {len(music_files)} music files and {len(video_files)} video templates")
    
    if len(music_files) == 0 or len(video_files) == 0:
        print("❌ ERROR: Missing media files!")
        print(f"Music files in space_music/: {music_files}")
        print(f"Video files in space_temp/: {video_files}")
        return False
    return True

def create_quote_content() -> tuple[str, str, str]:
    """Generates a new, unique two-part space fact using dynamic theming."""
    print("🧠 Activating AI Space Facts generator...")
    
    try:
        print("📚 Reading previously generated facts from Google Sheet...")
        used_facts = sheet.col_values(1)[1:] 
        history_list = "\n".join(f"- {fact}" for fact in used_facts)
        print(f"  Found {len(used_facts)} previously used facts.")
    except Exception as e:
        print(f"⚠️ Could not read sheet history, proceeding without it. Error: {e}")
        used_facts = []
        history_list = "None."
        
    MAX_ATTEMPTS = 5
    for attempt in range(MAX_ATTEMPTS):
        print(f"🤖 Attempt {attempt + 1}/{MAX_ATTEMPTS}: Generating a new, unique space fact...")
        
        # --- NEW THEME LIST FOR SPACE FACTS ---
        themes = [
            "a mind-bending fact about black holes", "Interstellar travel",
            "the actual speed of light", "the scale of the largest known star",
            "a weird exoplanet discovery", "the concept of time dilation in space",
             "strange weather on another planet",
            "strangest moons in the solar system", "what space smells like according to astronauts"
        ]
        chosen_theme = random.choice(themes)
        print(f"  Chosen Theme: {chosen_theme}")

        # --- NEW PROMPT FOCUSED ON SPACE FACTS ---
        master_prompt = f"""
        You are an AI that creates mind-blowing, two-part facts about space and astronomy.
        Your fact MUST be about the specific theme of: **{chosen_theme}**.

        CRITICAL RULES:
        1. Your language MUST be super simple and easy to understand for a general audience.
        2. The first part must be a "hook" that makes the reader curious.
        3. The second part must be the "reveal" or the core fact.
        4. Do NOT generate a fact that is similar to any in the "PREVIOUSLY USED" list.
        5. Your ENTIRE response MUST be in the format below, with nothing else.

        **GOOD EXAMPLES OF THE REQUIRED STYLE:**
        * EXAMPLE 1 (Theme: black holes): `PART_1: If you fell into a black hole…\nPART_2: …you could theoretically see both the beginning and end of the universe at once.\nTITLE: The Ultimate Time Machine`
        * EXAMPLE 2 (Theme: neutron stars): `PART_1: A single teaspoon of a neutron star…\nPART_2: …weighs more than all of humanity combined.\nTITLE: The Heaviest Thing in the Universe`

        **PREVIOUSLY USED QUOTES:**
        {history_list}

        **YOUR REQUIRED OUTPUT FORMAT:**
        PART_1:
        [The first part of the fact]

        PART_2:
        [The second part of the fact]

        TITLE:
        [The video title]
        """
        
        generation_config = GenerationConfig(temperature=0.8)
        response = gemini_model.generate_content(master_prompt, generation_config=generation_config)
        
        try:
            part1 = response.text.split("PART_2:")[0].replace("PART_1:", "").strip()
            if part1 in used_facts:
                print(f"⚠️ AI generated a duplicate fact. Retrying...")
                continue
            part2 = response.text.split("TITLE:")[0].split("PART_2:")[1].strip()
            title = response.text.split("TITLE:")[1].strip()
            print("✅ New, unique fact generated!")
            return part1, part2, title
        except Exception as e:
            print(f"⚠️ Could not parse the AI's response on this attempt. Retrying... Error: {e}")
            
    print(f"❌ Failed to generate a unique fact after {MAX_ATTEMPTS} attempts.")
    return "Error", "Could not generate unique fact.", "Error"

def generate_extra_tags(title: str, quote_parts: str) -> list:
    """Uses AI to brainstorm a list of relevant SEO tags for the space facts niche."""
    print("🤖 Brainstorming additional SEO tags for space content...")
    prompt = f"""
Based on the following video title and content about space and astronomy, generate a list of 10-15 relevant, popular, and SEO-friendly YouTube tags.

TITLE: {title}
CONTENT: {quote_parts}

RULES:
- Return ONLY a comma-separated list of tags.
- Do not use hashtags (#).
- Include a mix of broad and specific tags (e.g., space facts, astronomy, universe, black hole, science, astrophysics, interesting facts, shorts).

Your comma-separated list of tags:
"""
    generation_config = GenerationConfig(temperature=0.7)
    response = gemini_model.generate_content(prompt, generation_config=generation_config)
    
    tags = [tag.strip() for tag in response.text.split(',')]
    print(f"✅ Generated {len(tags)} extra tags.")
    return tags

def generate_video_with_music(part1: str, part2: str, output_filename: str):
    """Generates a video with a sequentially chosen background, music, subtitles, and a heading."""
    print(f"🎬 Generating video with music for '{output_filename}'...")
    VIDEO_DURATION = 12

    # All of the Ken Burns Effect logic can be removed, as it's now part of the main block below.

    # --- 1. Select Media (with new sequential logic) ---
    try:
        music_folder = 'space_music'
        available_music = [f for f in os.listdir(music_folder) if f.endswith('.mp3')]
        chosen_music_path = os.path.join(music_folder, random.choice(available_music))
        print(f"🎵 Using music: {chosen_music_path}")
        
        background_video_folder = 'space_temp'
        available_videos = sorted([f for f in os.listdir(background_video_folder) if f.endswith('.mp4')]) # Sorted for consistent order
        
        if not available_videos:
            exit(f"❌ ERROR: No background videos found in '{background_video_folder}'.")

        # --- NEW: SEQUENTIAL VIDEO SELECTION LOGIC ---
        state_file = 'space_temp/last_video_index.txt'
        last_index = -1
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                try:
                    last_index = int(f.read())
                except ValueError:
                    last_index = -1 # Start from beginning if file is empty or corrupt

        # Calculate the next index, looping back to 0 if at the end of the list
        next_index = (last_index + 1) % len(available_videos)
        
        chosen_video_filename = available_videos[next_index]
        chosen_video_path = os.path.join(background_video_folder, chosen_video_filename)

        # Save the new index for the next run
        with open(state_file, 'w') as f:
            f.write(str(next_index))
        
        print(f"🔄 Sequentially selected video #{next_index + 1}: {chosen_video_path}")
        # --- END OF NEW LOGIC ---

    except Exception as e:
        exit(f"❌ ERROR: Could not find media files. Details: {e}")

    # --- 2. Load and Prepare Clips ---
    music_clip = AudioFileClip(chosen_music_path).subclip(0, VIDEO_DURATION)
    background_clip = VideoFileClip(chosen_video_path)
    if background_clip.duration < VIDEO_DURATION:
        background_clip = background_clip.loop(duration=VIDEO_DURATION)
    final_background = background_clip.subclip(0, VIDEO_DURATION).resize(height=1920).crop(x_center=background_clip.w/2, width=1080)
    
    # The Ken Burns Effect can be here if you want it applied to all videos,
    # or you can re-implement the conditional logic if needed.
    final_background = final_background.resize(lambda t: 1 + 0.02 * t)
    final_background = final_background.crop(x_center=final_background.w / 2, y_center=final_background.h / 2, width=1080, height=1920)

    # --- 3. Create Permanent Heading ---
    # The heading and text clip creation is the same as before.
    print(" Adding permanent heading...")
    heading_text = "Space Facts"
    box_width = int(1080 * 0.7)
    box_height = 110
    vertical_position_percent = 0.20
    vertical_pixel_position = int(1920 * vertical_position_percent)
    final_position = ('center', vertical_pixel_position)
    
    heading_bg = ColorClip(size=(box_width, box_height), color=(255, 255, 255)).set_position(final_position).set_duration(VIDEO_DURATION)
    heading_clip = TextClip(heading_text, fontsize=75, color='black', font='Arial-Bold', size=heading_bg.size).set_position(final_position).set_duration(VIDEO_DURATION)

    # --- 4. Create Animated and Fading Quote Clips ---
    part1_duration = 6
    part2_start_time = 6
    part2_duration = 6
    
    quote_clip1 = TextClip(part1, fontsize=80, color='white', font='Arial-Bold', stroke_color='black', stroke_width=3,
                           size=(1080 * 0.9, None), method='caption')
    quote_clip1 = quote_clip1.set_position('center').set_duration(part1_duration)
    quote_clip1 = quote_clip1.fx(vfx.fadein, 1).fx(vfx.fadeout, 0.5)

    quote_clip2 = TextClip(part2, fontsize=80, color='white', font='Arial-Bold', stroke_color='black', stroke_width=3,
                           size=(1080 * 0.9, None), method='caption')
    quote_clip2 = quote_clip2.set_position('center').set_start(part2_start_time).set_duration(part2_duration)
    quote_clip2 = quote_clip2.fx(vfx.fadein, 0.5)

    # --- 5. Composite Final Video ---
    print(" Compositing final video...")
    final_video = CompositeVideoClip(
        [final_background, heading_bg, heading_clip, quote_clip1, quote_clip2]
    ).set_duration(VIDEO_DURATION)
    
    final_video = final_video.set_audio(music_clip)
    final_video.write_videofile(output_filename, fps=24, codec='libx264', threads=4)
    print(f"✅ Video saved successfully as {output_filename}")
    
        
def log_to_sheet(part1: str, part2: str, title: str, filename: str, status: str):
    """Adds the details of the generated video to the Google Sheet."""
    print(f"✍️ Logging details to Google Sheet...")
    try:
        # This new_row now uses the 'status' variable we pass to it
        new_row = [part1, part2, title, filename, status]
        sheet.append_row(new_row)
        print("✅ Logged to Google Sheet successfully.")
    except Exception as e:
        print(f"⚠️ Could not log to Google Sheet. Details: {e}")

# --- MAIN EXECUTION BLOCK ---

# --- MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    print("\n🚀 --- AI YouTube Shorts Factory ---")

    # Setup environment for GitHub Actions or local use
    is_automated = setup_environment()

    # Verify that essential media files exist before proceeding
    if not verify_media_files():
        exit("❌ Cannot proceed without media files. Halting execution.")

    # Get user choice (automatically selects '2' for GitHub Actions)
    choice = get_user_choice()

    if choice in ['1', '2']:
        # --- STAGE 1: GENERATING CONTENT ---
        print("\n--- STAGE 1: GENERATING CONTENT ---")
        part1, part2, title = create_quote_content()
        if part1 == "Error":
            exit("❌ Failed to generate content from AI. Halting execution.")
        print(f"✅ Content Generated: {title}")

        # --- STAGE 2: GENERATING VIDEO ---
        print("\n--- STAGE 2: GENERATING VIDEO ---")
        # Create a unique filename to prevent conflicts
        timestamp = int(time.time())
        output_filename = f"quote_{timestamp}.mp4"
        
        # Call the function to create the .mp4 file
        generate_video_with_music(part1, part2, output_filename)

        # --- STAGE 3: UPLOADING TO YOUTUBE (if choice is '2') ---
        upload_status = "Generated Locally" # Default status for logging
        if choice == '2':
            print("\n--- STAGE 3: UPLOADING TO YOUTUBE ---")
            try:
                youtube = get_authenticated_service()
                print("✅ YouTube Authentication Successful.")

                # Create description and a robust set of tags
                description = f"""{part1} {part2}\n\n#space #facts #shorts #astronomy #science #universe"""
                base_tags = ["space", "facts", "shorts", "astronomy", "science", "universe", "nasa", "space exploration"]
                ai_tags = generate_extra_tags(title, f"{part1} {part2}")
                final_tags = list(set(base_tags + ai_tags)) # Combine and remove duplicates

                print(f"🚀 Uploading '{output_filename}' to YouTube...")
                # Call the function from upload_video.py
                upload_video(
                    youtube,
                    file_path=output_filename,
                    title=title,
                    description=description,
                    tags=final_tags,
                    privacy_status="public"
                )
                upload_status = "Uploaded to YouTube"
                print("✅ Video Uploaded Successfully!")

            except Exception as e:
                print(f"❌ ERROR: YouTube upload failed. Details: {e}")
                upload_status = f"YouTube Upload Failed: {e}"

        # --- STAGE 4: LOGGING TO GOOGLE SHEETS ---
        print("\n--- STAGE 4: LOGGING TO GOOGLE SHEETS ---")
        log_to_sheet(part1, part2, title, output_filename, upload_status)

        print("\n✅ --- All tasks completed. ---")

    else:
        print("❌ Invalid choice. Please run again and enter 1 or 2.")
