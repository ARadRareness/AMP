"""
FastMCP Echo Server
"""

import logging
from fastmcp_http.server import FastMCPHttpServer
import threading
from pydantic import BaseModel
from typing import Optional, List

import mcp_helper

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create server
mcp = FastMCPHttpServer(
    "VideoExplorer",
    description="Video Explorer - A system for managing (Youtube) video downloads, transcriptions, and metadata using AI-assisted video processing",
)

# Reference to the VideoFileExplorer instance (will be set later)
video_explorer = None


class VideoInfo(BaseModel):
    """Information about a downloaded video"""

    name: str
    last_changed: str
    length: str
    summary: Optional[str] = None


@mcp.tool()
def toggle_video_transcriptions(transcriptions_on: bool) -> str:
    """Toggle if video transcriptions should be automatically generated"""
    if video_explorer:
        video_explorer.transcribe_var.set(transcriptions_on)
        video_explorer.toggle_transcribe()
        return f"Video transcriptions are now {'on' if transcriptions_on else 'off'}"
    return "Video explorer not initialized"


@mcp.tool()
def toggle_morning_video_downloads(downloads_on: bool) -> str:
    """Toggle if new videos should be automatically downloaded in the morning"""
    if video_explorer:
        video_explorer.auto_download_var.set(downloads_on)
        video_explorer.toggle_auto_download()
        return f"Morning video downloads are now {'on' if downloads_on else 'off'}"
    return "Video explorer not initialized"


@mcp.tool()
def start_video_downloads() -> str:
    """Start downloading new youtube videos"""
    if video_explorer:
        if not mcp_helper.ask_for_permission(
            "Is it okay if I start downloading videos?"
        ):
            return "Permission denied by user"
        video_explorer.start_video_downloader()
        return "Video downloads started"
    return "Video explorer not initialized"


@mcp.tool()
def get_last_download_start_time() -> str:
    """Get the timestamp of when downloads were last started"""
    if video_explorer:
        return video_explorer.get_last_download_start_time()
    return "Video explorer not initialized"


@mcp.tool()
def list_latest_downloaded_videos(
    limit: int = 10, include_summaries: bool = False
) -> List[VideoInfo]:
    """Get a list of the latest downloaded videos
    Args:
        limit: Maximum number of videos to return (max 100)
        include_summaries: Whether to include video summaries
    Returns:
        List of VideoInfo objects containing video information
    """
    if video_explorer:
        videos = video_explorer.get_latest_downloaded_videos(limit, include_summaries)
        return [VideoInfo(**video) for video in videos]
    return []


@mcp.tool()
def show_window() -> str:
    """Show and activate the Video Explorer window"""
    if video_explorer:
        video_explorer.show_window()
        return "Window shown and activated"
    return "Video explorer not initialized"


def start_mcp_server():
    mcp.run_http()


def run_in_thread(video_explorer_reference):
    global video_explorer
    video_explorer = video_explorer_reference
    thread = threading.Thread(target=start_mcp_server, daemon=True)
    thread.start()
    return thread
