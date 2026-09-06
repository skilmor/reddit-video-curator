# Reddit Video Curator

A personal read-only content discovery tool for reviewing public Reddit video posts.

## Purpose

The application periodically retrieves recent public video posts from a small predefined set of public subreddits.

It uses public Reddit metadata such as:

- post ID
- title
- subreddit
- creation time
- score
- comment count
- post URL
- public media information

Selected posts are sent to a private Telegram bot for manual review.

## Architecture

Reddit Data API  
↓  
Python collector  
↓  
Filtering  
↓  
Private Telegram review bot

## Reddit interactions

The application is read-only.

It does not:

- create posts or comments
- vote
- send private messages
- moderate communities
- access private Reddit data
- automate user interactions

## Technology

- Python
- Reddit Data API / PRAW
- Telegram Bot API
- FFmpeg
