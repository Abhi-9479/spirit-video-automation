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

def create_quote_content() -> tuple[str, str, str]:
    """
    Generates a new, unique two-part spiritual fact, inspired by universal wisdom
    (such as from the Bhagavad Gita) without naming the source.
    """
    print("🧠 Activating AI Spiritual Facts generator...")
    
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
        print(f"🤖 Attempt {attempt + 1}/{MAX_ATTEMPTS}: Generating a new, unique spiritual fact...")
        
        # --- NEW THEME LIST FOR SPIRITUAL FACTS ---
        themes = [
            "the nature of the true self vs. the physical body", "the concept of performing your duty (dharma)",
            "the law of action and reaction (karma)", "detachment from the results of your work",
            "the illusion of the material world", "how to control the senses and the mind",
            "the eternal, unchanging nature of the soul", "finding peace in a chaotic world",
            "the idea that change is the only constant", "the three fundamental energies of nature (gunas)"
        ]
        chosen_theme = random.choice(themes)
        print(f"  Chosen Theme: {chosen_theme}")

        # --- NEW PROMPT FOCUSED ON SPIRITUAL FACTS ---
        master_prompt = f"""
        You are an AI that distills deep spiritual wisdom, based on ancient Eastern philosophy, into simple, two-part insights for a modern audience.
        Your insight MUST be about the specific theme of: **{chosen_theme}**.

        CRITICAL RULES:
        1.  Do NOT mention specific religious texts, scriptures, gods, or historical figures. Present the ideas as universal truths.
        2.  Your language MUST be super simple, profound, and easy to understand.
        3.  The first part must be a "hook". The second part must be the core "reveal".
        4.  Do NOT generate an insight similar to any in the "PREVIOUSLY USED" list.
        5.  Your ENTIRE response MUST be in the format below, with nothing else.

        **GOOD EXAMPLES OF THE REQUIRED STYLE:**
        * EXAMPLE 1 (Theme: the true self): `PART_1: The person you see in the mirror is not the real you…\nPART_2: …it is just the temporary vessel for the eternal energy that you truly are.\nTITLE: You Are Not Your Body`
        * EXAMPLE 2 (Theme: detachment): `PART_1: You have a right to your actions…\nPART_2: …but you have no right to the results of those actions.\nTITLE: The Secret to Inner Peace`

        **PREVIOUSLY USED INSIGHTS:**
        {history_list}

        **YOUR REQUIRED OUTPUT FORMAT:**
        PART_1:
        [The first part of the insight]

        PART_2:
        [The second part of the insight]

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
            print("✅ New, unique insight generated!")
            return part1, part2, title
        except Exception as e:
            print(f"⚠️ Could not parse the AI's response on this attempt. Retrying... Error: {e}")
            
    print(f"❌ Failed to generate a unique insight after {MAX_ATTEMPTS} attempts.")
    return "Error", "Could not generate unique insight.", "Error"

def generate_extra_tags(title: str, quote_parts: str) -> list:
    """Uses AI to brainstorm a list of relevant SEO tags for the spiritual/philosophy niche."""
    print("🤖 Brainstorming additional SEO tags for spiritual content...")
    prompt = f"""
Based on the following video title and content about spirituality and ancient wisdom, generate a list of 10-15 relevant, popular, and SEO-friendly YouTube tags.

TITLE: {title}
CONTENT: {quote_parts}

RULES:
- Return ONLY a comma-separated list of tags.
- Do not use hashtags (#).
- Include a mix of broad and specific tags (e.g., spirituality, ancient wisdom, philosophy, mindfulness, karma, dharma, life lessons, spiritual awakening, shorts).

Your comma-separated list of tags:
"""
    generation_config = GenerationConfig(temperature=0.7)
    response = gemini_model.generate_content(prompt, generation_config=generation_config)
    
    tags = [tag.strip() for tag in response.text.split(',')]
    print(f"✅ Generated {len(tags)} extra tags.")
    return tags

def generate_video_with_music(part1: str, part2: str, output_filename: str):
    """Generates a video with a sequentially chosen background, music, subtitles, and a heading."""
    try:
        change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})
    except Exception:
        print("⚠️ ImageMagick path not configured. Text may fail.")

    print(f"🎬 Generating video with music for '{output_filename}'...")
    VIDEO_DURATION = 12

    # All of the Ken Burns Effect logic can be removed, as it's now part of the main block below.

    # --- 1. Select Media (with new sequential logic) ---
    try:
        music_folder = 'spirit_music'
        available_music = [f for f in os.listdir(music_folder) if f.endswith('.mp3')]
        chosen_music_path = os.path.join(music_folder, random.choice(available_music))
        print(f"🎵 Using music: {chosen_music_path}")
        
        background_video_folder = 'spirit'
        available_videos = sorted([f for f in os.listdir(background_video_folder) if f.endswith('.mp4')]) # Sorted for consistent order
        
        if not available_videos:
            exit(f"❌ ERROR: No background videos found in '{background_video_folder}'.")

        # --- NEW: SEQUENTIAL VIDEO SELECTION LOGIC ---
        state_file = 'spirit/last_video_index.txt'
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
    heading_text = "Spirituality Teaches"
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
# --- MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    print("\n--- AI YouTube Shorts Factory ---")
    print("1: Generate a new video and save it locally.")
    print("2: Generate, Upload, and Update a new video on YouTube.")
    
    choice = input("Enter your choice (1 or 2): ")
    
    # This block runs for both choices, as both need a quote and a video file
    if choice == '1' or choice == '2':
        # --- Stage 1: Write Quote ---
        part1, part2, title = create_quote_content()
        if part1 == "Error": exit()
        print(f"\n  Part 1: {part1}\n  Part 2: {part2}\n  Title: {title}")
        
        # --- Stage 2: Generate Video File ---
        run_id = int(time.time())
        video_filename = f"quote_{run_id}.mp4"
        generate_video_with_music(part1, part2, video_filename)

        # --- Stage 3: UPLOAD and UPDATE (only if choice is 2) ---
        if choice == '2':
            print("\n--- Starting YouTube Upload & Update Process ---")
            try:
                # Get authenticated YouTube service
                youtube_service = get_authenticated_service()
                
                # <--- NEW: Define the hashtags and create the new title
                hashtags = "#shorts #ytshorts #spiritual #spiritualfacts #Quickfeelfact"
                title_with_hashtags = f"{title} {hashtags}"
                print(f"  Uploading with new title: {title_with_hashtags}")
                # ----------------------------------------------------
                
                # Step 3a: Upload the video as private
                initial_tags = ["spiritual", "facts", "shorts","ytshorts"]
                video_id = upload_video(
                    youtube_service=youtube_service,
                    file_path=video_filename,
                    title=title_with_hashtags, # <--- NEW: Use the title with hashtags
                    description=f"{part1}\n\n{part2}",
                    tags=initial_tags,
                    privacy_status='private' # Uploads as private or public
                )
                
                if video_id:
                    # Step 3b: Generate a better list of tags with AI
                    all_tags = generate_extra_tags(title, f"{part1} {part2}")
                    
                    # Step 3c: Update the video with the new tags
                    update_video_details(youtube_service, video_id, all_tags)
                    
                    # Step 3d: Log the final result to the sheet (still logs the original title)
                    log_to_sheet(part1, part2, title, video_filename, f"UPLOADED_PRIVATE_ID:{video_id}")
                else:
                    raise Exception("Upload failed, video ID not received.")

            except Exception as e:
                print(f"❌ An error occurred during the YouTube upload phase: {e}")
                log_to_sheet(part1, part2, title, video_filename, "UPLOAD_FAILED")
        
        # This part runs if the user only chose option '1'
        else:
            log_to_sheet(part1, part2, title, video_filename, "LOCAL_ONLY")

        print("\n🎉 Process complete!")
        
    else:
        print("Invalid choice.")