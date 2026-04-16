import os
import time
import json
import random
import subprocess
import sys
import requests
from datetime import datetime, timezone, timedelta

print("\n" + "="*50)
print("   🚀 PYTHON-JS HYBRID VIDEO FACTORY (PROXY + FB UPLOAD)")
print("="*50)

# ==========================================
# ⚙️ SETTINGS & METADATA
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

# ==========================================
# 🔍 JS CALLER (Reads data.json)
# ==========================================
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

# ==========================================
# 🎥 FFMPEG MANAGER
# ==========================================
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
    
    subprocess.run(args1, stderr=subprocess.DEVNULL)
        
    if os.path.exists(tempDynVideo) and os.path.getsize(tempDynVideo) > 1000:
        print("[✅] Step A Done! 10 sec ki clip ban gayi.")
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
            print("[⚠️] 'main_video.mp4' nahi mili! Sirf 10 sec ki clip ko hi final bana raha hoon.")
            os.rename(tempDynVideo, output_vid)
            return True
    return False

# ==========================================
# 📘 FACEBOOK UPLOAD & MONITOR SYSTEM
# ==========================================
def fb_check_and_comment(token, frame_path, comment_text):
    if not token: return
    try:
        res_me = requests.get("https://graph.facebook.com/v18.0/me", params={"access_token": token, "fields": "id,name"}).json()
        if 'id' not in res_me: return
        page_id = res_me['id']
        print(f"\n[🔍 FB] Monitoring Page: {res_me.get('name')} (ID: {page_id})")
        
        res_posts = requests.get(f"https://graph.facebook.com/v18.0/{page_id}/posts", params={"fields": "id,created_time", "access_token": token}).json()
        posts = res_posts.get('data', [])
        now = datetime.now(timezone.utc)
        
        recent_posts = []
        for post in posts:
            post_time = datetime.strptime(post['created_time'], "%Y-%m-%dT%H:%M:%S%z")
            if (now - post_time).total_seconds() <= 3600:
                recent_posts.append(post)
                
        print(f"  [📊 FB] Found {len(recent_posts)} post(s) created in the last 1 hour.")
        
        for post in recent_posts:
            post_id = post['id']
            print(f"  [👉 FB] Checking Post ID: {post_id}")
            
            res_comments = requests.get(f"https://graph.facebook.com/v18.0/{post_id}/comments", params={"fields": "from", "access_token": token}).json()
            comments = res_comments.get('data', [])
            already_commented = any(c.get('from', {}).get('id') == page_id for c in comments)
            
            if already_commented:
                print("  [✅ FB] Page has ALREADY commented on this post. Skipping.")
            else:
                print("  [🚨 FB] Author comment NOT FOUND! Taking action...")
                
                # 1. Post Comment
                comment_url = f"https://graph.facebook.com/v18.0/{post_id}/comments"
                comment_img_path = "comment_image.jpeg"
                try:
                    if os.path.exists(comment_img_path):
                        with open(comment_img_path, 'rb') as img:
                            requests.post(comment_url, data={"message": comment_text, "access_token": token}, files={"source": img})
                    else:
                        requests.post(comment_url, data={"message": comment_text, "access_token": token})
                    print("  [✅ FB] Promotional Comment Placed Successfully!")
                except Exception as e:
                    print("  [❌ FB] Comment Error")

                # 2. Force HD Thumbnail Upload
                if os.path.exists(frame_path):
                    print("  [🖼️ FB] Updating Thumbnail with HD LIVE FRAME...")
                    try:
                        res_attach = requests.get(f"https://graph.facebook.com/v18.0/{post_id}", params={"fields": "attachments", "access_token": token}).json()
                        attachments = res_attach.get('attachments', {}).get('data', [])
                        video_id = None
                        if attachments and 'target' in attachments[0] and 'id' in attachments[0]['target']:
                            video_id = attachments[0]['target']['id']
                            
                        if video_id:
                            thumb_url = f"https://graph.facebook.com/v18.0/{video_id}/thumbnails"
                            with open(frame_path, 'rb') as thumb_img:
                                res_thumb = requests.post(thumb_url, data={"access_token": token, "is_preferred": "true"}, files={"source": thumb_img}).json()
                                if res_thumb.get('success'):
                                    print("  [✅ FB] HD Live Frame set as Video Cover Photo!")
                    except Exception as e:
                        print("  [❌ FB] Thumbnail Error")
    except Exception as e:
        print("  [❌ FB] API Connection Error")

# ==========================================
# 🚀 MAIN LOOP
# ==========================================
def main():
    clipCounter = 1
    streamData = get_stream_data()
    
    # Dual Token Logic Setup
    token_selection = os.environ.get('TOKEN_SELECTION', 'Dual')
    token1 = os.environ.get('FB_TOKEN_1', '').strip()
    token2 = os.environ.get('FB_TOKEN_2', '').strip()
    
    active_tokens = []
    if token_selection == 'Token1' and token1: active_tokens.append(token1)
    elif token_selection == 'Token2' and token2: active_tokens.append(token2)
    elif token_selection == 'Dual':
        if token1: active_tokens.append(token1)
        if token2: active_tokens.append(token2)

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
            print("\n[🎉] Pipeline Success for this cycle! (Video aur Thumbnail ready hain)")
        else:
            print("  [❌] Pipeline failed. Refreshing link...")
            streamData = get_stream_data()
            
        # ==========================================
        # ⏳ SMART WAIT TIME + FACEBOOK MONITOR
        # ==========================================
        print(f"\n[⏳] 3 Minute ka wait shuru... Is dauran Python Facebook Worker apna kaam karega!")
        wait_start_time = time.time()
        
        if active_tokens:
            for t in active_tokens:
                fb_check_and_comment(t, thumb_path, final_desc)
        else:
            print("  [⚠️ FB] Koi Facebook Token nahi mila. Monitor skip kar raha hoon.")
            
        # Cleanup Files
        if os.path.exists(video_name): os.remove(video_name)
        if os.path.exists(thumb_path): os.remove(thumb_path)
            
        time_spent = time.time() - wait_start_time
        remaining_wait = (WAIT_TIME_MS / 1000.0) - time_spent
        if remaining_wait < 10: remaining_wait = 10
        
        print(f"[💤] FB Scan Done. Aglay clip ke liye {int(remaining_wait)} seconds rest kar raha hoon...")
        time.sleep(remaining_wait)
        clipCounter += 1

if __name__ == "__main__":
    main()























# import os
# import time
# import json
# import random
# import subprocess
# import sys
# from datetime import datetime, timezone, timedelta

# print("\n" + "="*50)
# print("   🚀 PYTHON-JS HYBRID VIDEO FACTORY (PROXY + METADATA)")
# print("="*50)

# # ==========================================
# # ⚙️ SETTINGS
# # ==========================================
# TITLES_INPUT = os.environ.get('TITLES_LIST', 'Live Match Today,,Watch Full Match DC vs GT')
# DESCS_INPUT = os.environ.get('DESCS_LIST', 'Watch the live action here')
# HASHTAGS = os.environ.get('HASHTAGS', '#IPL2026 #DCvsGT #CricketLovers #LiveMatch')

# WAIT_TIME_MS = 300 * 1000 
# START_TIME = time.time() * 1000
# END_TIME_LIMIT_MS = (5 * 60 * 60 + 50 * 60) * 1000 

# consecutiveLinkFails = 0

# def format_pkt():
#     pkt = timezone(timedelta(hours=5))
#     dt = datetime.now(pkt)
#     return dt.strftime('%b %d, %Y, %I:%M:%S %p PKT')

# def generate_metadata(clip_num):
#     print(f"\n[🧠 Metadata] Cycle #{clip_num} ke liye naya Title aur Description ban raha hai...")
#     titles = [t.strip() for t in TITLES_INPUT.split(',,') if t.strip()]
#     descs = [d.strip() for d in DESCS_INPUT.split(',,') if d.strip()]
    
#     title = random.choice(titles) if titles else "Live Match Today"
#     desc_body = random.choice(descs) if descs else "Watch the live action here!"
    
#     emojis_list = ["🔥", "🏏", "⚡", "🏆", "💥", "😱", "📺", "🚀"]
#     random.shuffle(emojis_list)
#     emojis = " ".join(emojis_list[:3])
    
#     tags_list = HASHTAGS.split(' ')
#     random.shuffle(tags_list)
#     tags = " ".join(tags_list[:4])
    
#     final_title = title[:240]
#     final_desc = f"{final_title} {emojis}\n\n{desc_body}\n\n⏱️ Update: {format_pkt()}\n👇 Watch Full Match Link in First Comment!\n\n{tags}"
#     print(f"[✅ Metadata] Ready: {final_title}")
#     return final_title, final_desc

# def get_stream_data():
#     global consecutiveLinkFails
#     if os.path.exists('data.json'):
#         os.remove('data.json')
        
#     result = subprocess.run(['node', 'scraper.js'])
    
#     if result.returncode == 0 and os.path.exists('data.json'):
#         with open('data.json', 'r') as f:
#             data = json.load(f)
#         consecutiveLinkFails = 0
#         return data
#     else:
#         consecutiveLinkFails += 1
#         print(f"\n🚨 [WARNING] Link fetch failed. Strike: {consecutiveLinkFails}/3")
#         if consecutiveLinkFails >= 3:
#             print("\n🛑 [FATAL] 3 Strikes. Exiting.")
#             sys.exit(1)
#         return None

# def process_video(data, output_vid):
#     print("\n[🎬 Step 1] Stream capture, PiP Frame aur Merging shuru ho rahi hai...")
#     headersCmd = f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\nReferer: {data['referer']}\r\nCookie: {data['cookie']}\r\n"
    
#     audioFile = "marya_live.mp3"
#     bgImage = "website_frame.png"
#     staticVideo = "main_video.mp4"
#     duration = "10"
#     blurAmount = "20:5"
    
#     hasBg = os.path.exists(bgImage)
#     hasAudio = os.path.exists(audioFile)
#     hasMainVideo = os.path.exists(staticVideo)
#     tempDynVideo = f"temp_dyn_{int(time.time())}.mp4"

#     # --- STEP A ---
#     print("[>] Step A: 10 sec ki live clip tayyar kar raha hoon...")
#     args1 = ["ffmpeg", "-y", "-thread_queue_size", "1024", "-headers", headersCmd, "-i", data['url']]
    
#     if hasBg:
#         args1.extend(["-thread_queue_size", "1024", "-loop", "1", "-framerate", "30", "-i", bgImage])
#     if hasAudio:
#         args1.extend(["-thread_queue_size", "1024", "-stream_loop", "-1", "-i", audioFile])
        
#     filterComplex1 = ""
#     if hasBg:
#         filterComplex1 += f"[0:v]scale=1064:565,boxblur={blurAmount}[pip]; [1:v][pip]overlay=0:250:shortest=1,scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p[outv]"
#     else:
#         filterComplex1 += f"[0:v]scale=1280:720,boxblur={blurAmount},format=yuv420p[outv]"
        
#     args1.extend(["-filter_complex", filterComplex1, "-map", "[outv]"])
    
#     if hasAudio:
#         audioIndex = 2 if hasBg else 1
#         args1.extend(["-map", f"{audioIndex}:a:0"])
#     else:
#         args1.extend(["-map", "0:a:0"])
        
#     args1.extend(["-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-b:a", "128k", "-t", duration, tempDynVideo])
    
#     res1 = subprocess.run(args1, stderr=subprocess.PIPE)
#     if res1.returncode != 0:
#         print(f"[❌] Step A Error Details:\n{res1.stderr.decode('utf-8')[:500]}")
        
#     if os.path.exists(tempDynVideo) and os.path.getsize(tempDynVideo) > 1000:
#         print("[✅] Step A Done! 10 sec ki clip ban gayi.")
        
#         # --- STEP B ---
#         if hasMainVideo:
#             print("[>] Step B: 'main_video.mp4' mil gayi! Ab dono ko merge kar raha hoon...")
#             args2 = [
#                 "ffmpeg", "-y", "-i", tempDynVideo, "-i", staticVideo,
#                 "-filter_complex", "[0:v]scale=1280:720,setsar=1,fps=30,format=yuv420p[v0]; [0:a]aformat=sample_rates=44100:channel_layouts=stereo[a0]; [1:v]scale=1280:720,setsar=1,fps=30,format=yuv420p[v1]; [1:a]aformat=sample_rates=44100:channel_layouts=stereo[a1]; [v0][a0][v1][a1]concat=n=2:v=1:a=1[outv][outa]",
#                 "-map", "[outv]", "-map", "[outa]",
#                 "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-b:a", "128k", output_vid
#             ]
#             subprocess.run(args2, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#             os.remove(tempDynVideo)
#             if os.path.exists(output_vid) and os.path.getsize(output_vid) > 1000:
#                 print(f"[✅ Worker 1 & 2] Merging SUCCESS! Final Video Ready: {output_vid}")
#                 return True
#             else:
#                 print("[❌ Worker 1 & 2] Merging failed.")
#         else:
#             print("[⚠️] 'main_video.mp4' nahi mili! Sirf 10 sec ki clip ko hi final bana raha hoon.")
#             os.rename(tempDynVideo, output_vid)
#             return True
            
#     return False

# def main():
#     clipCounter = 1
#     streamData = get_stream_data()
    
#     while True:
#         elapsed = (time.time() * 1000) - START_TIME
#         if elapsed > END_TIME_LIMIT_MS:
#             print("\n[🛑] Time Limit Reached. Closing Bot.")
#             break
            
#         print(f"\n{'-'*50}\n--- 🔄 STARTING CYCLE #{clipCounter} ---\n{'-'*50}")
        
#         final_title, final_desc = generate_metadata(clipCounter)
#         thumb_path = f"thumbnail_{clipCounter}.png"
#         video_name = f"Final_Video_{clipCounter}.mp4"
        
#         # Call JS for HD Thumbnail
#         subprocess.run(['node', 'thumbnail.js', final_title, thumb_path])
        
#         # Process Video
#         if process_video(streamData, video_name):
#             print("\n[🎉] Pipeline Success for this cycle!")
#             # Yahan par upload ka function aayega (API/FB)
            
#             if os.path.exists(video_name): os.remove(video_name)
#             if os.path.exists(thumb_path): os.remove(thumb_path)
#         else:
#             print("  [❌] Pipeline failed. Refreshing link...")
#             streamData = get_stream_data()
            
#         print(f"[⏳] Rest for 5 Minutes...")
#         time.sleep(WAIT_TIME_MS / 1000)
#         clipCounter += 1

# if __name__ == "__main__":
#     main()
