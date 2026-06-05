import argparse
import os
import re
import sys
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def main():
    parser = argparse.ArgumentParser(description='Fetch a blog post by title.')
    parser.add_argument('--title', required=True, help='Title of the blog post to fetch')
    parser.add_argument('--blog-id', help='Blog ID (optional, will use first blog if not provided)')
    args = parser.parse_args()

    title = args.title
    blog_id = args.blog_id

    # Load credentials
    creds_path = 'Config/_SECRETS/blogger_token.json'
    if not os.path.exists(creds_path):
        print(f"Error: Credentials file not found at {creds_path}")
        sys.exit(1)

    try:
        creds = Credentials.from_authorized_user_file(
            creds_path,
            scopes=['https://www.googleapis.com/auth/blogger.readonly']
        )
    except Exception as e:
        print(f"Error loading credentials: {e}")
        sys.exit(1)

    # Refresh if expired
    if creds.expired:
        try:
            creds.refresh(Request())
        except Exception as e:
            print(f"Error refreshing credentials: {e}")
            sys.exit(1)

    # Build service
    try:
        service = build('blogger', 'v3', credentials=creds)
    except Exception as e:
        print(f"Error building Blogger service: {e}")
        sys.exit(1)

    # Determine blog ID if not provided
    if not blog_id:
        try:
            blogs = service.blogs().listByUser(userId='self').execute()
            if 'items' not in blogs or len(blogs['items']) == 0:
                print("Error: No blogs found for this user.")
                sys.exit(1)
            blog_id = blogs['items'][0]['id']
            print(f"Using blog ID: {blog_id}")
        except HttpError as e:
            print(f"Error listing blogs: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error listing blogs: {e}")
            sys.exit(1)

    # Search for post by title
    try:
        search_response = service.posts().search(blogId=blog_id, q=title).execute()
    except HttpError as e:
        print(f"Error searching posts: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error searching posts: {e}")
        sys.exit(1)

    items = search_response.get('items', [])
    if not items:
        print(f"Error: No posts found matching title '{title}'")
        sys.exit(1)

    # Try exact match first
    matched_post = None
    for post in items:
        if post.get('title', '').strip().lower() == title.strip().lower():
            matched_post = post
            break

    # If no exact match, use first partial match
    if not matched_post:
        matched_post = items[0]
        print(f"Warning: No exact match found. Using first partial match: '{matched_post.get('title', '')}'")

    post_id = matched_post['id']
    print(f"Found post ID: {post_id}")

    # Fetch full post content
    try:
        full_post = service.posts().get(blogId=blog_id, postId=post_id).execute()
    except HttpError as e:
        print(f"Error fetching full post: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error fetching full post: {e}")
        sys.exit(1)

    content = full_post.get('content', '')
    if not content:
        print("Error: Post has no content.")
        sys.exit(1)

    # Create safe filename
    safe_title = re.sub(r'[^\w\-]', '_', title)[:60]
    output_dir = 'Input'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f'{safe_title}__ORIGINAL.html')

    # Save content
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Saved to {output_path}")
    except Exception as e:
        print(f"Error saving file: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
