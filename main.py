from app.daily_job import generate_daily_plan
from app.image_pipeline import generate_two_photos, generate_video_from_photos


def run_once():
    result = generate_daily_plan()
    photos = generate_two_photos()
    video_path = generate_video_from_photos(photos, output_name="daily_video.mp4")

    print("Plan:", result["plan"])
    print("AI output:", result["ai_text"])
    print("Caption:", result["caption"])
    print("Photos:", photos)
    print("Video:", video_path)


if __name__ == "__main__":
    run_once()
