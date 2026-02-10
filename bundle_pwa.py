import shutil
import os

def create_zip():
    # Define files to include
    include_files = [
        'index.html', 'style.css', 'app.js', 'sw.js', 'manifest.json',
        'icon.svg', 'icon-192.png', 'icon-512.png',
        'library.json', 'dict.json', 'grammar.json',
        'kumo_no_ito.json', 'hashire_melos.json', 'chumon.json', 'rashomon.json',
        'isekai_rezero.json', 'isekai_mushoku.json', 'isekai_bookworm.json'
    ]

    # Create distinct folder
    dist_dir = 'yomu-dist'
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)

    for f in include_files:
        if os.path.exists(f):
            shutil.copy(f, os.path.join(dist_dir, f))
        else:
            print(f"Warning: Missing {f}")

    # Zip it
    shutil.make_archive('yomu-pwa', 'zip', dist_dir)
    print(f"Created yomu-pwa.zip containing {len(include_files)} files.")

if __name__ == '__main__':
    create_zip()
