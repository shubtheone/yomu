from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, filename):
    # Use dark theme background color
    bg_color = (13, 13, 20)  # #0d0d14
    accent_color = (226, 114, 91) # #e2725b (vermillion)

    # create image
    img = Image.new('RGB', (size, size), bg_color)
    draw = ImageDraw.Draw(img)

    # Draw a rounded rectangle for app icon style
    padding = size // 10
    corner_radius = size // 6
    
    # Calculate box
    box = [padding, padding, size - padding, size - padding]
    draw.rounded_rectangle(box, radius=corner_radius, fill=accent_color)
    
    # Draw Kanji "読"
    # We need a font for kanji. Since we might not have a TTF file,
    # let's draw a simple geometric representation or just fall back to system font if possible
    # Actually, let's try to load a default font or draw a simple "Y" instead if fails.
    
    try:
        # Try to find a font that supports Japanese usually available on Windows
        font_path = "C:\\Windows\\Fonts\\msgothic.ttc"
        if not os.path.exists(font_path):
             font_path = "C:\\Windows\\Fonts\\arial.ttf" # Fallback
        
        font_size = int(size * 0.5)
        font = ImageFont.truetype(font_path, font_size)
        
        text = "読"
        # Get text size
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center text
        x = (size - text_width) / 2
        y = (size - text_height) / 2 - (text_height * 0.1) # slight vertical adjustment
        
        draw.text((x, y), text, font=font, fill=(255, 255, 255))
        
    except Exception as e:
        print(f"Could not load font or draw text: {e}")
        # Draw a fallback "Y"
        try:
            font = ImageFont.load_default()
            # Draw big Y manually or just leave empty
        except:
            pass

    img.save(filename)
    print(f"Saved {filename}")

if __name__ == "__main__":
    create_icon(192, "icon-192.png")
    create_icon(512, "icon-512.png")
