from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw

OUTPUT_DIR = Path("data/generated_media")
REF_DIR = Path("data/reference_images")


def ensure_dirs():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REF_DIR.mkdir(parents=True, exist_ok=True)


def create_reference_if_missing():
    ensure_dirs()
    ref_file = REF_DIR / "reference.jpg"
    if ref_file.exists():
        return str(ref_file)

    image = Image.new("RGB", (1080, 1920), color=(25, 25, 30))
    draw = ImageDraw.Draw(image)
    draw.rectangle((180, 160, 900, 1760), fill=(60, 70, 90))
    draw.text((220, 800), "PAYAL AI", fill=(255, 255, 255))
    draw.text((220, 900), "REFERENCE STYLE", fill=(170, 195, 255))
    image.save(ref_file)
    return str(ref_file)


def generate_two_photos():
    ensure_dirs()
    ref_file = create_reference_if_missing()
    base = Image.open(ref_file).convert("RGB")
    results = []

    for idx in range(2):
        variant = base.copy()
        variant = ImageEnhance.Contrast(variant).enhance(1.4 + idx * 0.25)
        variant = variant.filter(ImageFilter.SHARPEN)
        output = OUTPUT_DIR / f"photo_{idx + 1}.jpg"
        variant.save(output, quality=90)
        results.append(str(output))

    return results


def generate_video_from_photos(photo_paths, output_name="daily_video.mp4"):
    from moviepy.editor import ImageSequenceClip

    ensure_dirs()
    frames = [Image.open(path).convert("RGB") for path in photo_paths]
    output_path = OUTPUT_DIR / output_name
    clip = ImageSequenceClip([frame for frame in frames], fps=8)
    clip.write_videofile(str(output_path), fps=8, codec="libx264", audio=False)
    return str(output_path)
