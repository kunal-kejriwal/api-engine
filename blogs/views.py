from django.shortcuts import render
import requests

WP_API_BASE = "https://kunalkejriwal.com/wp-json/wp/v2"

def fetch_posts(request):
    wp_response = requests.get(
        f"{WP_API_BASE}/posts",
        params={
            "per_page": 10,
            "_embed": "true"
        },
        timeout=5
    )

    posts = wp_response.json()
    
    for post in posts:
        post["featured_image"] = None
        try:
            post["featured_image"] = post["_embedded"]["wp:featuredmedia"][0]["source_url"]
        except Exception:
            pass

    return render(
        request,
        "blogs/blog_list.html",
        {"posts": posts}
    )
