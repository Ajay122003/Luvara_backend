import os
from supabase import create_client


SUPABASE_URL = os.getenv("SUPABASE_URL").rstrip("/") + "/"
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY
)

def upload_image(file, folder="categories"):
    file_path = f"{folder}/{file.name}"

    supabase.storage.from_("luvara").upload(
        file_path,
        file.read(),
        {"content-type": file.content_type}
    )

    return supabase.storage.from_("luvara").get_public_url(file_path)
