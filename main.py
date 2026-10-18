def get_youtube_video(url, chat_id):
    # المحاولة 1: عبر Cobalt API - بتجاوز حظر يوتيوب
    try:
        print("Trying Cobalt...")
        r = requests.post(
            "https://api.cobalt.tools/api/json",
            json={"url": url, "vCodec": "h264", "vQuality": "720", "aFormat": "mp3", "isAudioOnly": False},
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=30
        )
        data = r.json()
        if data.get("url"):
            print(f"Cobalt got: {data.get('url')}")
            # هذا رابط مباشر mp4
            video_data = requests.get(data["url"], headers={"User-Agent":"Mozilla/5.0"}, timeout=60).content
            tmp_path = "/tmp/youtube.mp4"
            with open(tmp_path, "wb") as f:
                f.write(video_data)
            return tmp_path, "YouTube via Cobalt"
        # اذا رجع picker
        if data.get("picker"):
            direct = data["picker"][0].get("url")
            if direct:
                video_data = requests.get(direct, timeout=60).content
                tmp_path = "/tmp/youtube.mp4"
                with open(tmp_path, "wb") as f:
                    f.write(video_data)
                return tmp_path, "YouTube"
    except Exception as e:
        print(f"Cobalt failed: {e}")

    # المحاولة 2: yt-dlp العادي (بيشتغل لبعض الفيديوهات)
    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': '/tmp/%(id)s.%(ext)s',
            'merge_output_format': 'mp4',
            'quiet': True,
            'extractor_args': {'youtube': {'player_client': ['android']}},
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if not os.path.exists(file_path):
                file_path = file_path.rsplit(".",1)[0] + ".mp4"
            return file_path, info.get('title','')
    except Exception as e:
        print(f"yt-dlp failed: {e}")
        raise e
