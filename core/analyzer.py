"""
Telegram file analysis module.
Analyzes messages, media and other data.
"""

import os
import io
import asyncio
from typing import List, Dict, Optional, Callable, Tuple
from pathlib import Path
from telethon import TelegramClient, errors
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, MessageService
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False


class FileAnalyzer:
    """Analyzes Telegram files and data."""
    
    def __init__(self, client: Optional[TelegramClient] = None):
        self.client = client
        self.analysis_data: Optional[Dict] = None
    
    def set_client(self, client: TelegramClient):
        """Sets the Telegram client."""
        self.client = client
    
    async def analyze_chat(
        self,
        chat_id: str,
        topic_id: Optional[int] = None,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Analyzes a chat/group/channel/topic and returns statistics.
        
        Args:
            chat_id: Chat ID to analyze
            topic_id: Optional topic ID
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with analysis results
        """
        if not self.client:
            return {"error": "Telegram client not set"}
        
        try:
            entity = await self.client.get_entity(int(chat_id))
            entity_name = getattr(entity, 'title', getattr(entity, 'first_name', 'Unknown'))
        except Exception as e:
            return {"error": f"Error getting entity: {e}"}
        
        total_messages = 0
        total_size = 0
        media_count = 0
        text_count = 0
        file_types = {}
        size_by_type = {}
        
        # Try to get total messages count first (for progress bar)
        total_count = None
        try:
            if hasattr(entity, 'total_messages') and entity.total_messages:
                total_count = entity.total_messages
        except:
            pass
        
        if progress_callback:
            if total_count:
                progress_callback(("start_progress", total_count, "Analyzing messages..."))
            else:
                progress_callback(("start_spinner", "Analyzing messages..."))
        
        # Use iter_messages to get all messages efficiently
        # Add delay to avoid rate limiting (analyze in batches)
        try:
            message_count = 0
            async for msg in self.client.iter_messages(entity, reply_to=topic_id, limit=None):
                if isinstance(msg, MessageService):
                    continue
                
                total_messages += 1
                message_count += 1
                
                # Add small delay every 100 messages to avoid rate limiting
                if message_count % 100 == 0:
                    await asyncio.sleep(0.5)  # Small delay to avoid flooding
                    if progress_callback:
                        if total_count:
                            progress_callback(("update_progress", total_messages))
                        else:
                            progress_callback(("update_spinner", f"Analyzed {total_messages} messages..."))
                
                if msg.media:
                    media_count += 1
                    
                    if isinstance(msg.media, MessageMediaPhoto):
                        file_type = "Photo"
                        # Photos usually don't have size in media, try to get from file if available
                        size = 0
                        if hasattr(msg.media, 'photo') and hasattr(msg.media.photo, 'sizes'):
                            # Get largest size
                            sizes = msg.media.photo.sizes
                            if sizes:
                                largest = max(sizes, key=lambda s: getattr(s, 'size', 0))
                                size = getattr(largest, 'size', 0) or 0
                    elif isinstance(msg.media, MessageMediaDocument):
                        doc = msg.media.document
                        if doc:
                            mime_type = getattr(doc, 'mime_type', '') or ''
                            if 'image' in mime_type:
                                file_type = "Image"
                            elif 'video' in mime_type:
                                file_type = "Video"
                            elif 'audio' in mime_type:
                                file_type = "Audio"
                            elif 'application/pdf' in mime_type:
                                file_type = "PDF"
                            else:
                                file_type = "Document"
                            
                            size = getattr(doc, 'size', 0) or 0
                        else:
                            file_type = "Media"
                            size = 0
                    else:
                        file_type = "Media"
                        size = 0
                    
                    file_types[file_type] = file_types.get(file_type, 0) + 1
                    size_by_type[file_type] = size_by_type.get(file_type, 0) + size
                    total_size += size
                else:
                    text_count += 1
            
            if progress_callback:
                progress_callback(("stop_progress",))
                        
        except errors.FloodWaitError as e:
            if progress_callback:
                progress_callback(("stop_progress",))
            return {"error": f"Rate limit exceeded. Please wait {e.seconds} seconds and try again. Session may have been temporarily disconnected."}
        except errors.AuthKeyError:
            if progress_callback:
                progress_callback(("stop_progress",))
            return {"error": "Session invalidated. Please login again."}
        except Exception as e:
            if progress_callback:
                progress_callback(("stop_progress",))
            return {"error": f"Error fetching messages: {e}"}
        
        # Format sizes
        total_size_mb = total_size / (1024 * 1024)
        total_size_gb = total_size_mb / 1024
        
        self.analysis_data = {
            "entity_name": entity_name,
            "chat_id": chat_id,
            "topic_id": topic_id,
            "total_messages": total_messages,
            "text_messages": text_count,
            "media_messages": media_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size_mb, 2),
            "total_size_gb": round(total_size_gb, 2),
            "file_types": file_types,
            "size_by_type": size_by_type
        }
        
        return self.analysis_data
    
    def format_size(self, size_bytes: int) -> str:
        """Formats size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def generate_chart(self, output_path: Optional[Path] = None) -> bytes:
        """
        Generates a chart image from analysis data.
        
        Args:
            output_path: Optional path to save the image
            
        Returns:
            Image bytes
        """
        if not self.analysis_data:
            raise ValueError("No analysis data available. Run analyze_chat first.")
        
        data = self.analysis_data
        
        # Create figure with subplots (larger size for better quality)
        fig = plt.figure(figsize=(16, 12))
        fig.patch.set_facecolor('#1e1e1e')
        
        # Main title
        fig.suptitle(
            f"Storage Analysis: {data['entity_name']}",
            fontsize=16,
            fontweight='bold',
            color='white',
            y=0.98
        )
        
        # 1. Pie chart - File types distribution (improved with legend)
        ax1 = plt.subplot(2, 2, 1)
        file_types = data['file_types']
        if file_types:
            labels = list(file_types.keys())
            sizes = list(file_types.values())
            colors = plt.cm.tab10(np.linspace(0, 1, min(len(labels), 10)))
            if len(labels) > 10:
                colors = plt.cm.tab20(np.linspace(0, 1, len(labels)))
            
            # Calculate percentages for legend
            total_files = sum(sizes)
            percentages = [(size / total_files * 100) if total_files > 0 else 0 for size in sizes]
            
            # Create labels with percentages for legend
            legend_labels = [f"{label}: {percent:.1f}%" for label, percent in zip(labels, percentages)]
            
            # Draw pie chart without labels or percentages inside
            wedges, texts = ax1.pie(sizes, labels=None, autopct=None, colors=colors, 
                                    startangle=90)
            ax1.set_title('File Types Distribution', color='white', fontweight='bold', pad=20)
            
            # Add legend outside the pie chart with percentages
            ax1.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1),
                      fontsize=9, facecolor='#2d2d2d', edgecolor='none', labelcolor='white')
        else:
            ax1.text(0.5, 0.5, 'No media files', ha='center', va='center', color='white')
            ax1.set_title('File Types Distribution', color='white', fontweight='bold')
        ax1.set_facecolor('#2d2d2d')
        
        # 2. Bar chart - Storage by file type
        ax2 = plt.subplot(2, 2, 2)
        size_by_type = data['size_by_type']
        if size_by_type:
            types = list(size_by_type.keys())
            sizes_mb = [size_by_type[t] / (1024 * 1024) for t in types]
            colors = plt.cm.viridis(np.linspace(0, 1, len(types)))
            bars = ax2.bar(types, sizes_mb, color=colors)
            ax2.set_ylabel('Size (MB)', color='white')
            ax2.set_title('Storage by File Type', color='white', fontweight='bold')
            ax2.tick_params(colors='white')
            ax2.set_facecolor('#2d2d2d')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f} MB',
                        ha='center', va='bottom', color='white', fontsize=8)
            
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        else:
            ax2.text(0.5, 0.5, 'No storage data', ha='center', va='center', color='white')
            ax2.set_title('Storage by File Type', color='white', fontweight='bold')
        ax2.set_facecolor('#2d2d2d')
        
        # 3. Statistics text - improved formatting
        ax3 = plt.subplot(2, 2, 3)
        ax3.axis('off')
        
        # Format file types list
        files_list = ""
        if file_types:
            for ftype, count in file_types.items():
                files_list += f"  {ftype:12s} {count:>8,}\n"
        else:
            files_list = "  No files found\n"
        
        stats_text = f"""STATISTICS
========================================
Total Messages:     {data['total_messages']:>12,}
Text Messages:      {data['text_messages']:>12,}
Media Messages:     {data['media_messages']:>12,}

STORAGE
========================================
Total Size:         {data['total_size_mb']:>12,.2f} MB
Total Size:         {data['total_size_gb']:>12,.2f} GB

FILES
========================================
{files_list}"""
        
        ax3.text(0.5, 0.95, stats_text, fontsize=10, color='white',
                verticalalignment='top', horizontalalignment='center',
                family='monospace',
                bbox=dict(boxstyle='round,pad=0.8', facecolor='#2d2d2d', 
                         edgecolor='#4a4a4a', linewidth=1.5))
        ax3.set_facecolor('#1e1e1e')
        
        # 4. Messages comparison
        ax4 = plt.subplot(2, 2, 4)
        categories = ['Text', 'Media']
        counts = [data['text_messages'], data['media_messages']]
        colors = ['#4CAF50', '#2196F3']
        bars = ax4.bar(categories, counts, color=colors)
        ax4.set_ylabel('Count', color='white')
        ax4.set_title('Messages: Text vs Media', color='white', fontweight='bold')
        ax4.tick_params(colors='white')
        ax4.set_facecolor('#2d2d2d')
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height):,}',
                    ha='center', va='bottom', color='white', fontweight='bold')
        
        # Adjust layout
        plt.tight_layout(rect=[0, 0, 1, 0.97])
        
        # Save to bytes (higher DPI for better quality)
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', facecolor='#1e1e1e', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        img_bytes = img_buffer.read()
        
        # Save to file if path provided (higher DPI for better quality)
        if output_path:
            plt.savefig(output_path, facecolor='#1e1e1e', dpi=300, bbox_inches='tight')
        
        plt.close()
        return img_bytes
    
    def save_chart(self, filename: str = "pigram_analysis.png") -> Path:
        """
        Saves chart to desktop (Windows/Linux) or home directory (Termux).
        
        Args:
            filename: Name of the file
            
        Returns:
            Path to saved file
        """
        # Determine save location
        home = Path.home()
        
        if os.name == 'nt':  # Windows
            desktop = home / "Desktop"
        elif 'ANDROID_ROOT' in os.environ or 'TERMUX_VERSION' in os.environ:  # Termux/Android
            desktop = home
        else:  # Linux
            desktop = home / "Desktop"
            if not desktop.exists():
                desktop = home
        
        desktop.mkdir(exist_ok=True)
        output_path = desktop / filename
        
        self.generate_chart(output_path=output_path)
        return output_path
    
    def copy_chart_to_clipboard(self) -> Tuple[bool, str]:
        """
        Copies statistics text to clipboard.
        
        Returns:
            Tuple of (success, message)
        """
        if not self.analysis_data:
            return False, "No analysis data available"
        
        try:
            data = self.analysis_data
            file_types = data['file_types']
            
            # Format file types list
            files_list = ""
            if file_types:
                for ftype, count in file_types.items():
                    files_list += f"  {ftype:12s} {count:>8,}\n"
            else:
                files_list = "  No files found\n"
            
            # Format statistics text (same format as in chart)
            stats_text = f"""STATISTICS
========================================
Total Messages:     {data['total_messages']:>12,}
Text Messages:      {data['text_messages']:>12,}
Media Messages:     {data['media_messages']:>12,}

STORAGE
========================================
Total Size:         {data['total_size_mb']:>12,.2f} MB
Total Size:         {data['total_size_gb']:>12,.2f} GB

FILES
========================================
{files_list}"""
            
            if HAS_CLIPBOARD:
                try:
                    import pyperclip
                    pyperclip.copy(stats_text)
                    # Verify it was actually copied by reading back
                    try:
                        clipboard_content = pyperclip.paste()
                        if clipboard_content.strip() == stats_text.strip():
                            return True, "Statistics copied to clipboard successfully!"
                        else:
                            # Content doesn't match, clipboard might not be working
                            return False, stats_text
                    except:
                        # Can't verify, assume it worked but return text anyway
                        return False, stats_text
                except Exception as e:
                    # Error during copy, return text for manual copy
                    return False, stats_text
            else:
                return False, stats_text
        except Exception as e:
            return False, f"Error: {e}"
