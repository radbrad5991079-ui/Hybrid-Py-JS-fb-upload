import os
import time
import json
import random
import subprocess
import sys
from datetime import datetime, timezone, timedelta

print("\n" + "="*50)
print("   🚀 PYTHON-JS HYBRID VIDEO FACTORY (PROXY + METADATA)")
print("="*50)

# ==========================================
# ⚙️ SETTINGS
# ==========================================
TITLES_INPUT = os.environ.get('TITLES_LIST', 'Live Match Today,,Watch Full Match DC vs GT')
DESCS_INPUT = os.environ.get('DESCS_LIST', 'Watch the live action here')
HASHTAGS = os.environ.get('HASHTAGS', '#IPL2026 #DCvsGT #CricketLovers #LiveMatch')

WAIT_TIME_MS = 300 * 1000 
START_TIME = time.time() * 1000
END_TIME_LIMIT_MS = (5 * 60 * 60 + 50 * 60) * 1000 

consecutiveLinkFails = 0

def format_pkt():
    pkt = timezone(timedelta(hours=5))
    dt = datetime.now(pkt)
    return dt.strftime('%b %d, %Y, %I:%M:%S %p PKT')

def generate_metadata(clip_num):
    print(f"\n[🧠 Metadata] Cycle #{clip_num} ke liye naya Title aur Description ban raha hai...")
    titles = [t.strip() for t in TITLES_INPUT.split(',,') if t.strip()]
    descs = [d.strip() for d in DESCS_INPUT.split(',,') if d.strip()]
    
    title = random.choice(titles) if titles else "Live Match Today"
    desc_body = random.choice(descs) if descs else "Watch the live action here!"
    
    emojis_list = ["🔥", "🏏", "⚡", "🏆", "💥", "😱", "📺", "🚀"]
    random.shuffle(emojis_list)
    emojis = " ".join(emojis_list[:3])
    
    tags_list = HASHTAGS.split(' ')
    random.shuffle(tags_list)
    tags = " ".join(tags_list[:4])
    
    final_title = title[:240]
    final_desc = f"{final_title} {emojis}\n\n{desc_body}\n\n⏱️ Update: {format_pkt()}\n👇 Watch Full Match Link in First Comment!\n\n{tags}"
    print(f"[✅ Metadata] Ready: {final_title}")
    return final_title, final_desc

def get_stream_data():
    global consecutiveLinkFails
    if os.path.exists('data.json'):
        os.remove('data.json')
        
    result = subprocess.run(['node', 'scraper.js'])
    
    if result.returncode == 0 and os.path.exists('data.json'):
        with open('data.json', 'r') as f:
            data = json.load(f)
        consecutiveLinkFails = 0
        return data
    else:
        consecutiveLinkFails += 1
        print(f"\n🚨 [WARNING] Link fetch failed. Strike: {consecutiveLinkFails}/3")
        if consecutiveLinkFails >= 3:
            print("\n🛑 [FATAL] 3 Strikes. Exiting.")
            sys.exit(1)
        return None

def process_video(data, output_vid):
    print("\n[🎬 Step 1] Stream capture, PiP Frame aur Merging shuru ho rahi hai...")
    headersCmd = f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\nReferer: {data['referer']}\r\nCookie: {data['cookie']}\r\n"
    
    audioFile = "marya_live.mp3"
    bgImage = "website_frame.png"
    staticVideo = "main_video.mp4"
    duration = "10"
    blurAmount = "20:5"
    
    hasBg = os.path.exists(bgImage)
    hasAudio = os.path.exists(audioFile)
    hasMainVideo = os.path.exists(staticVideo)
    tempDynVideo = f"temp_dyn_{int(time.time())}.mp4"

    # --- STEP A ---
    print("[>] Step A: 10 sec ki live clip tayyar kar raha hoon...")
    args1 = ["ffmpeg", "-y", "-thread_queue_size", "1024", "-headers", headersCmd, "-i", data['url']]
    
    if hasBg:
        args1.extend(["-thread_queue_size", "1024", "-loop", "1", "-framerate", "30", "-i", bgImage])
    if hasAudio:
        args1.extend(["-thread_queue_size", "1024", "-stream_loop", "-1", "-i", audioFile])
        
    filterComplex1 = ""
    if hasBg:
        filterComplex1 += f"[0:v]scale=1064:565,boxblur={blurAmount}[pip]; [1:v][pip]overlay=0:250:shortest=1,scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p[outv]"
    else:
        filterComplex1 += f"[0:v]scale=1280:720,boxblur={blurAmount},format=yuv420p[outv]"
        
    args1.extend(["-filter_complex", filterComplex1, "-map", "[outv]"])
    
    if hasAudio:
        audioIndex = 2 if hasBg else 1
        args1.extend(["-map", f"{audioIndex}:a:0"])
    else:
        args1.extend(["-map", "0:a:0"])
        
    args1.extend(["-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-b:a", "128k", "-t", duration, tempDynVideo])
    
    res1 = subprocess.run(args1, stderr=subprocess.PIPE)
    if res1.returncode != 0:
        print(f"[❌] Step A Error Details:\n{res1.stderr.decode('utf-8')[:500]}")
        
    if os.path.exists(tempDynVideo) and os.path.getsize(tempDynVideo) > 1000:
        print("[✅] Step A Done! 10 sec ki clip ban gayi.")
        
        # --- STEP B ---
        if hasMainVideo:
            print("[>] Step B: 'main_video.mp4' mil gayi! Ab dono ko merge kar raha hoon...")
            args2 = [
                "ffmpeg", "-y", "-i", tempDynVideo, "-i", staticVideo,
                "-filter_complex", "[0:v]scale=1280:720,setsar=1,fps=30,format=yuv420p[v0]; [0:a]aformat=sample_rates=44100:channel_layouts=stereo[a0]; [1:v]scale=1280:720,setsar=1,fps=30,format=yuv420p[v1]; [1:a]aformat=sample_rates=44100:channel_layouts=stereo[a1]; [v0][a0][v1][a1]concat=n=2:v=1:a=1[outv][outa]",
                "-map", "[outv]", "-map", "[outa]",
                "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-b:a", "128k", output_vid
            ]
            subprocess.run(args2, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.remove(tempDynVideo)
            if os.path.exists(output_vid) and os.path.getsize(output_vid) > 1000:
                print(f"[✅ Worker 1 & 2] Merging SUCCESS! Final Video Ready: {output_vid}")
                return True
            else:
                print("[❌ Worker 1 & 2] Merging failed.")
        else:
            print("[⚠️] 'main_video.mp4' nahi mili! Sirf 10 sec ki clip ko hi final bana raha hoon.")
            os.rename(tempDynVideo, output_vid)
            return True
            
    return False

def main():
    clipCounter = 1
    streamData = get_stream_data()
    
    while True:
        elapsed = (time.time() * 1000) - START_TIME
        if elapsed > END_TIME_LIMIT_MS:
            print("\n[🛑] Time Limit Reached. Closing Bot.")
            break
            
        print(f"\n{'-'*50}\n--- 🔄 STARTING CYCLE #{clipCounter} ---\n{'-'*50}")
        
        final_title, final_desc = generate_metadata(clipCounter)
        thumb_path = f"thumbnail_{clipCounter}.png"
        video_name = f"Final_Video_{clipCounter}.mp4"
        
        # Call JS for HD Thumbnail
        subprocess.run(['node', 'thumbnail.js', final_title, thumb_path])
        
        # Process Video
        if process_video(streamData, video_name):
            print("\n[🎉] Pipeline Success for this cycle!")
            # Yahan par upload ka function aayega (API/FB)
            
            if os.path.exists(video_name): os.remove(video_name)
            if os.path.exists(thumb_path): os.remove(thumb_path)
        else:
            print("  [❌] Pipeline failed. Refreshing link...")
            streamData = get_stream_data()
            
        print(f"[⏳] Rest for 5 Minutes...")
        time.sleep(WAIT_TIME_MS / 1000)
        clipCounter += 1

if __name__ == "__main__":
    main()
