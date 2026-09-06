import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import praw
from dotenv import load_dotenv


load_dotenv()


SUBREDDITS = [
    "Damnthatsinteresting",
    "interestingasfuck",
    "nextfuckinglevel",
    "BeAmazed",
    "oddlysatisfying",
    "Unexpected",
]

POSTS_PER_SUBREDDIT = 30

MIN_SCORE = 50
MIN_DURATION = 5
MAX_DURATION = 90

OUTPUT_FILE = Path("data/candidates.json")


def create_reddit_client() -> praw.Reddit:
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv(
        "REDDIT_USER_AGENT",
        "windows:reddit-video-curator:v1.0"
    )

    if not client_id:
        raise RuntimeError("REDDIT_CLIENT_ID is missing")

    if not client_secret:
        raise RuntimeError("REDDIT_CLIENT_SECRET is missing")

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )

    # We only read public Reddit data.
    reddit.read_only = True

    return reddit


def get_reddit_video(post):
    """
    Return Reddit-hosted video metadata.

    Reddit-hosted video posts normally expose their media data through
    post.media["reddit_video"].
    """

    if not getattr(post, "is_video", False):
        return None

    media = post.media or {}
    video = media.get("reddit_video")

    if not video:
        return None

    return video


def post_to_candidate(post):
    video = get_reddit_video(post)

    if not video:
        return None

    duration = video.get("duration")

    if duration is None:
        return None

    if duration < MIN_DURATION or duration > MAX_DURATION:
        return None

    if post.score < MIN_SCORE:
        return None

    if getattr(post, "over_18", False):
        return None

    created = datetime.fromtimestamp(
        post.created_utc,
        tz=timezone.utc
    )

    age_seconds = max(time.time() - post.created_utc, 1)
    age_hours = age_seconds / 3600

    # Simple ranking metric.
    # Useful for finding posts gaining score quickly.
    score_velocity = post.score / max(age_hours, 0.25)

    return {
        "id": post.id,
        "title": post.title,
        "subreddit": str(post.subreddit),

        "score": post.score,
        "comments": post.num_comments,

        "created_utc": created.isoformat(),
        "age_hours": round(age_hours, 2),
        "score_velocity": round(score_velocity, 2),

        "duration": duration,
        "width": video.get("width"),
        "height": video.get("height"),

        "post_url": f"https://www.reddit.com{post.permalink}",

        "video": {
            "fallback_url": video.get("fallback_url"),
            "hls_url": video.get("hls_url"),
            "dash_url": video.get("dash_url"),
        },
    }


def collect_from_subreddit(reddit, subreddit_name):
    print(f"\n[r/{subreddit_name}]")

    subreddit = reddit.subreddit(subreddit_name)

    candidates = []

    try:
        posts = subreddit.new(limit=POSTS_PER_SUBREDDIT)

        for post in posts:
            candidate = post_to_candidate(post)

            if candidate is None:
                continue

            candidates.append(candidate)

            print(
                f"  + {candidate['score']:>6} | "
                f"{candidate['duration']:>3}s | "
                f"{candidate['title'][:70]}"
            )

    except Exception as exc:
        print(f"  ERROR: {exc}")

    return candidates


def remove_duplicates(candidates):
    result = {}
    for item in candidates:
        result[item["id"]] = item

    return list(result.values())


def save_candidates(candidates):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(candidates),
        "candidates": candidates,
    }

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(
            payload,
            f,
            ensure_ascii=False,
            indent=2,
        )


def main():
    reddit = create_reddit_client()

    print("Reddit Video Curator")
    print("--------------------")
    print(f"read_only: {reddit.read_only}")

    all_candidates = []

    for subreddit in SUBREDDITS:
        items = collect_from_subreddit(
            reddit,
            subreddit,
        )

        all_candidates.extend(items)

    all_candidates = remove_duplicates(all_candidates)

    # Most rapidly gaining posts first.
    all_candidates.sort(
        key=lambda x: x["score_velocity"],
        reverse=True,
    )

    save_candidates(all_candidates)

    print()
    print(f"Found: {len(all_candidates)} video candidates")
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
