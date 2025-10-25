"""
BeneAI Performance Testing Utilities

This module provides helper functions for testing the end-to-end BeneAI pipeline,
including WebSocket communication, frame processing, metrics calculation, and visualization.
"""

import asyncio
import base64
import json
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import io

import cv2
import numpy as np
import pandas as pd
from PIL import Image
import websockets
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix, accuracy_score


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class TestConfig:
    """Configuration for a single test run"""
    frame_rate: int  # FPS to extract from video
    resolution: Tuple[int, int]  # (width, height)
    jpeg_quality: int  # 1-100
    mediapipe_complexity: int  # 0, 1, or 2
    mediapipe_confidence: float  # 0.0-1.0

    def to_dict(self) -> Dict:
        return asdict(self)

    def config_id(self) -> str:
        """Generate unique ID for this configuration"""
        return f"fps{self.frame_rate}_res{self.resolution[0]}x{self.resolution[1]}_q{self.jpeg_quality}_mc{self.mediapipe_complexity}_conf{self.mediapipe_confidence}"


@dataclass
class EmotionResult:
    """Single emotion detection result"""
    timestamp: float
    emotion: str
    investor_state: str
    confidence: float
    latency_ms: float
    top_emotions: List[Dict[str, float]]


@dataclass
class TestResult:
    """Complete results for a single test run"""
    config: TestConfig
    video_path: str
    emotion_results: List[EmotionResult]

    # Performance metrics
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    throughput_fps: float

    # Accuracy metrics (if ground truth provided)
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    confusion_mat: Optional[np.ndarray] = None

    def to_dict(self) -> Dict:
        result = asdict(self)
        if self.confusion_mat is not None:
            result['confusion_mat'] = self.confusion_mat.tolist()
        return result


# =============================================================================
# Video Processing
# =============================================================================

class VideoProcessor:
    """Extract and process video frames"""

    def __init__(self, video_path: str):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        self.original_fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.total_frames / self.original_fps

    def extract_frames(self, target_fps: int, resolution: Tuple[int, int]) -> List[Tuple[float, np.ndarray]]:
        """
        Extract frames at target FPS and resolution

        Returns:
            List of (timestamp, frame) tuples
        """
        frames = []
        frame_interval = int(self.original_fps / target_fps)

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        frame_idx = 0

        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            if frame_idx % frame_interval == 0:
                # Resize frame
                resized = cv2.resize(frame, resolution)
                timestamp = frame_idx / self.original_fps
                frames.append((timestamp, resized))

            frame_idx += 1

        return frames

    def encode_frame_jpeg(self, frame: np.ndarray, quality: int) -> str:
        """
        Encode frame as JPEG and return base64 string

        Args:
            frame: BGR frame from OpenCV
            quality: JPEG quality 1-100

        Returns:
            Base64-encoded JPEG string
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Convert to PIL Image
        pil_image = Image.fromarray(rgb_frame)

        # Encode as JPEG
        buffer = io.BytesIO()
        pil_image.save(buffer, format='JPEG', quality=quality)
        jpeg_bytes = buffer.getvalue()

        # Base64 encode
        b64_string = base64.b64encode(jpeg_bytes).decode('utf-8')

        return b64_string

    def close(self):
        """Release video capture"""
        self.cap.release()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# =============================================================================
# WebSocket Communication
# =============================================================================

class BeneAIClient:
    """WebSocket client for BeneAI backend"""

    def __init__(self, backend_url: str = "ws://localhost:8000/ws"):
        self.backend_url = backend_url
        self.websocket = None
        self.session_id = None

    async def connect(self):
        """Establish WebSocket connection"""
        self.websocket = await websockets.connect(self.backend_url)
        print(f"Connected to {self.backend_url}")

    async def disconnect(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            print("Disconnected from backend")

    async def send_frame(self, frame_b64: str, timestamp: float) -> Tuple[Dict, float]:
        """
        Send frame to backend and receive emotion analysis

        Returns:
            (response_dict, latency_ms)
        """
        if not self.websocket:
            raise RuntimeError("Not connected. Call connect() first.")

        message = {
            "type": "video_frame",
            "data": frame_b64,
            "timestamp": timestamp
        }

        # Send frame and measure latency
        start_time = time.time()
        await self.websocket.send(json.dumps(message))

        # Receive response
        response = await self.websocket.recv()
        end_time = time.time()

        latency_ms = (end_time - start_time) * 1000
        response_dict = json.loads(response)

        return response_dict, latency_ms

    async def send_audio_chunk(self, audio_b64: str, timestamp: float) -> Dict:
        """Send audio chunk to backend"""
        if not self.websocket:
            raise RuntimeError("Not connected. Call connect() first.")

        message = {
            "type": "audio_chunk",
            "data": audio_b64,
            "timestamp": timestamp,
            "mimeType": "audio/webm;codecs=opus",
            "duration": 2.0
        }

        await self.websocket.send(json.dumps(message))
        response = await self.websocket.recv()
        return json.loads(response)

    async def process_video(
        self,
        frames: List[Tuple[float, str]],
        config: TestConfig,
        progress_callback=None
    ) -> List[EmotionResult]:
        """
        Process all frames through the pipeline

        Args:
            frames: List of (timestamp, base64_frame) tuples
            config: Test configuration
            progress_callback: Optional function to call with progress updates

        Returns:
            List of EmotionResult objects
        """
        results = []

        for idx, (timestamp, frame_b64) in enumerate(frames):
            try:
                response, latency_ms = await self.send_frame(frame_b64, timestamp)

                # Parse emotion response
                if response.get("type") == "emotion_update":
                    data = response.get("data", {})

                    emotion_result = EmotionResult(
                        timestamp=timestamp,
                        emotion=data.get("primary_emotion", "Unknown"),
                        investor_state=data.get("investor_state", "neutral"),
                        confidence=data.get("confidence", 0.0),
                        latency_ms=latency_ms,
                        top_emotions=data.get("top_emotions", [])
                    )
                    results.append(emotion_result)

                if progress_callback:
                    progress_callback(idx + 1, len(frames))

                # Small delay to avoid overwhelming the backend
                await asyncio.sleep(0.05)

            except Exception as e:
                print(f"Error processing frame at {timestamp}s: {e}")
                continue

        return results

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()


# =============================================================================
# Ground Truth Management
# =============================================================================

class GroundTruth:
    """Load and manage ground truth annotations"""

    def __init__(self, annotations_path: str):
        with open(annotations_path, 'r') as f:
            self.data = json.load(f)

        self.annotations = self.data.get('annotations', [])
        self.video_name = self.data.get('video', '')
        self.fps = self.data.get('fps', 30)

        # Sort annotations by timestamp
        self.annotations.sort(key=lambda x: x['timestamp'])

        # Extract unique emotions and states
        self.unique_emotions = sorted(set(a['emotion'] for a in self.annotations))
        self.unique_states = sorted(set(a['investor_state'] for a in self.annotations))

    def get_annotation_at_time(self, timestamp: float, tolerance: float = 0.5) -> Optional[Dict]:
        """
        Find annotation closest to given timestamp within tolerance

        Args:
            timestamp: Time in seconds
            tolerance: Maximum time difference to consider a match (default 0.5s)

        Returns:
            Annotation dict or None if no match found
        """
        closest_annotation = None
        min_diff = float('inf')

        for annotation in self.annotations:
            diff = abs(annotation['timestamp'] - timestamp)
            if diff < min_diff and diff <= tolerance:
                min_diff = diff
                closest_annotation = annotation

        return closest_annotation

    def get_all_timestamps(self) -> List[float]:
        """Get all annotation timestamps"""
        return [a['timestamp'] for a in self.annotations]

    def to_dataframe(self) -> pd.DataFrame:
        """Convert annotations to pandas DataFrame"""
        return pd.DataFrame(self.annotations)


# =============================================================================
# Metrics Calculation
# =============================================================================

class MetricsCalculator:
    """Calculate performance and accuracy metrics"""

    @staticmethod
    def calculate_latency_metrics(emotion_results: List[EmotionResult]) -> Dict[str, float]:
        """Calculate latency statistics"""
        latencies = [r.latency_ms for r in emotion_results]

        if not latencies:
            return {
                'avg_latency_ms': 0.0,
                'p50_latency_ms': 0.0,
                'p95_latency_ms': 0.0,
                'p99_latency_ms': 0.0
            }

        return {
            'avg_latency_ms': np.mean(latencies),
            'p50_latency_ms': np.percentile(latencies, 50),
            'p95_latency_ms': np.percentile(latencies, 95),
            'p99_latency_ms': np.percentile(latencies, 99)
        }

    @staticmethod
    def calculate_throughput(
        emotion_results: List[EmotionResult],
        total_duration: float
    ) -> float:
        """Calculate effective throughput in frames per second"""
        if total_duration == 0:
            return 0.0
        return len(emotion_results) / total_duration

    @staticmethod
    def align_predictions_with_ground_truth(
        emotion_results: List[EmotionResult],
        ground_truth: GroundTruth,
        tolerance: float = 0.5,
        metric_type: str = 'emotion'  # 'emotion' or 'investor_state'
    ) -> Tuple[List[str], List[str]]:
        """
        Align predictions with ground truth annotations

        Args:
            emotion_results: Detected emotions
            ground_truth: Ground truth annotations
            tolerance: Time tolerance for matching (seconds)
            metric_type: What to compare - 'emotion' or 'investor_state'

        Returns:
            (y_true, y_pred) lists for sklearn metrics
        """
        y_true = []
        y_pred = []

        for result in emotion_results:
            annotation = ground_truth.get_annotation_at_time(result.timestamp, tolerance)

            if annotation:
                if metric_type == 'emotion':
                    y_true.append(annotation['emotion'])
                    y_pred.append(result.emotion)
                elif metric_type == 'investor_state':
                    y_true.append(annotation['investor_state'])
                    y_pred.append(result.investor_state)

        return y_true, y_pred

    @staticmethod
    def calculate_accuracy_metrics(
        y_true: List[str],
        y_pred: List[str],
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calculate accuracy, precision, recall, F1, and confusion matrix

        Returns:
            Dictionary with all accuracy metrics
        """
        if not y_true or not y_pred:
            return {
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'confusion_matrix': None,
                'labels': []
            }

        # Get unique labels if not provided
        if labels is None:
            labels = sorted(set(y_true + y_pred))

        # Calculate metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_true, y_pred, average='weighted', zero_division=0
        )
        conf_matrix = confusion_matrix(y_true, y_pred, labels=labels)

        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'confusion_matrix': conf_matrix,
            'labels': labels
        }

    @staticmethod
    def calculate_per_class_metrics(
        y_true: List[str],
        y_pred: List[str],
        labels: List[str]
    ) -> pd.DataFrame:
        """
        Calculate precision, recall, F1 for each class

        Returns:
            DataFrame with per-class metrics
        """
        precision, recall, f1, support = precision_recall_fscore_support(
            y_true, y_pred, labels=labels, zero_division=0
        )

        df = pd.DataFrame({
            'emotion': labels,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'support': support
        })

        return df


# =============================================================================
# Test Execution
# =============================================================================

async def run_single_test(
    video_path: str,
    config: TestConfig,
    backend_url: str,
    ground_truth: Optional[GroundTruth] = None,
    progress_callback=None
) -> TestResult:
    """
    Run a complete test with given configuration

    Args:
        video_path: Path to test video
        config: Test configuration
        backend_url: WebSocket URL for backend
        ground_truth: Optional ground truth annotations
        progress_callback: Optional progress callback function

    Returns:
        TestResult object with all metrics
    """
    print(f"\n{'='*60}")
    print(f"Running test: {config.config_id()}")
    print(f"{'='*60}")

    # Extract frames
    print("Extracting frames...")
    with VideoProcessor(video_path) as vp:
        video_duration = vp.duration
        frames_raw = vp.extract_frames(config.frame_rate, config.resolution)

        # Encode frames
        print(f"Encoding {len(frames_raw)} frames at quality {config.jpeg_quality}...")
        frames_encoded = [
            (timestamp, vp.encode_frame_jpeg(frame, config.jpeg_quality))
            for timestamp, frame in frames_raw
        ]

    # Process through backend
    print("Processing through BeneAI backend...")
    start_time = time.time()

    async with BeneAIClient(backend_url) as client:
        emotion_results = await client.process_video(
            frames_encoded,
            config,
            progress_callback=progress_callback
        )

    end_time = time.time()
    total_time = end_time - start_time

    # Calculate performance metrics
    latency_metrics = MetricsCalculator.calculate_latency_metrics(emotion_results)
    throughput = MetricsCalculator.calculate_throughput(emotion_results, total_time)

    # Calculate accuracy metrics if ground truth provided
    accuracy_metrics = {}
    if ground_truth:
        print("Calculating accuracy metrics...")
        y_true, y_pred = MetricsCalculator.align_predictions_with_ground_truth(
            emotion_results, ground_truth, tolerance=0.5, metric_type='emotion'
        )
        accuracy_metrics = MetricsCalculator.calculate_accuracy_metrics(
            y_true, y_pred, labels=ground_truth.unique_emotions
        )

    # Build result
    result = TestResult(
        config=config,
        video_path=video_path,
        emotion_results=emotion_results,
        avg_latency_ms=latency_metrics['avg_latency_ms'],
        p50_latency_ms=latency_metrics['p50_latency_ms'],
        p95_latency_ms=latency_metrics['p95_latency_ms'],
        p99_latency_ms=latency_metrics['p99_latency_ms'],
        throughput_fps=throughput,
        accuracy=accuracy_metrics.get('accuracy'),
        precision=accuracy_metrics.get('precision'),
        recall=accuracy_metrics.get('recall'),
        f1_score=accuracy_metrics.get('f1_score'),
        confusion_mat=accuracy_metrics.get('confusion_matrix')
    )

    print(f"\n✓ Test completed in {total_time:.2f}s")
    print(f"  Latency: {result.avg_latency_ms:.1f}ms avg, {result.p95_latency_ms:.1f}ms p95")
    print(f"  Throughput: {result.throughput_fps:.2f} fps")
    if result.f1_score:
        print(f"  F1 Score: {result.f1_score:.3f}")

    return result


# =============================================================================
# Results Aggregation
# =============================================================================

def aggregate_results(results: List[TestResult]) -> pd.DataFrame:
    """
    Aggregate multiple test results into a DataFrame

    Args:
        results: List of TestResult objects

    Returns:
        DataFrame with one row per test configuration
    """
    rows = []

    for result in results:
        row = {
            'config_id': result.config.config_id(),
            'frame_rate': result.config.frame_rate,
            'resolution': f"{result.config.resolution[0]}x{result.config.resolution[1]}",
            'jpeg_quality': result.config.jpeg_quality,
            'mediapipe_complexity': result.config.mediapipe_complexity,
            'mediapipe_confidence': result.config.mediapipe_confidence,
            'avg_latency_ms': result.avg_latency_ms,
            'p95_latency_ms': result.p95_latency_ms,
            'throughput_fps': result.throughput_fps,
            'accuracy': result.accuracy,
            'precision': result.precision,
            'recall': result.recall,
            'f1_score': result.f1_score
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    return df
