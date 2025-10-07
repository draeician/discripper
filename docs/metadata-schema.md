# Metadata Schema

The ripping pipeline writes a `metadata.json` document alongside ripped files in the
slugged output directory (for example: `~/Videos/the-matrix/metadata.json`). The
document captures disc-level details, the selected classification, the resolved
title, tool versions, and a per-track breakdown of the media that was produced.

## Top-level structure

`metadata.json` is a JSON object with the following fields:

| Field | Type | Description |
| --- | --- | --- |
| `generated_at` | string (ISO 8601) | Timestamp when the metadata document was created (UTC). |
| `disc` | object | Disc metadata containing `label` (string) and `id` (nullable string, currently `null`). |
| `classification` | object | Summary of classification results. Contains `type` (`"movie"` or `"series"`) and `episode_count` (integer). |
| `title` | string or null | Effective title used for naming (CLI flag, config, or fallback). |
| `output_root` | string or null | Absolute path to the directory containing rip artifacts. |
| `tools` | object | Map of tool name → version string (or `null` if unavailable). Includes ripping backends and `ffprobe` when present. |
| `tracks` | array | List of per-track objects (see below). |

## Track entries

Each element in `tracks` describes the media planned and produced for a single
title. Track objects contain the following keys:

| Field | Type | Description |
| --- | --- | --- |
| `index` | integer | 1-based position of the track in the ripping plan. |
| `title` | string | Human-readable label from inspection. |
| `episode_code` | string or null | Episode identifier (e.g., `"s01e01"`) when classification yielded series metadata. |
| `planned_duration_seconds` | number | Duration reported during inspection (float seconds). |
| `chapters` | object | Contains `count` (integer) and `map` (array of `{ "index": int, "duration_seconds": number }` entries describing chapter lengths). |
| `output` | object | Describes the rip artifact with keys: `path` (string), `container` (string or null), `exists` (boolean), `size_bytes` (integer or null). |
| `format` | object | Container summary from `ffprobe` (`container`, `duration_seconds`, `bit_rate`). Values may be `null` when unavailable. |
| `streams` | array | Stream entries from `ffprobe`. Each entry includes `type` (`video`, `audio`, `subtitle`, etc.), `index`, `codec`, `codec_long`, `bit_rate`, `language`, and additional type-specific fields (`width`, `height`, `frame_rate`, `pixel_format` for video; `channels`, `channel_layout`, `sample_rate` for audio; `title` for subtitles). |

When `ffprobe` is unavailable or a file is missing, the corresponding `format`
fields and `streams` array are populated with `null`/empty values while keeping
the schema stable.

## Example

```json
{
  "generated_at": "2024-01-01T00:00:00+00:00",
  "disc": {"label": "Sample Disc", "id": null},
  "classification": {"type": "movie", "episode_count": 1},
  "title": "The Matrix",
  "output_root": "/home/user/Videos/the-matrix",
  "tools": {
    "ffmpeg": "ffmpeg version n6.0",
    "ffprobe": "ffprobe version n6.0"
  },
  "tracks": [
    {
      "index": 1,
      "title": "Main Feature",
      "episode_code": null,
      "planned_duration_seconds": 5400.5,
      "chapters": {
        "count": 12,
        "map": [
          {"index": 1, "duration_seconds": 450.0},
          {"index": 2, "duration_seconds": 460.0}
        ]
      },
      "output": {
        "path": "/home/user/Videos/the-matrix/the-matrix_track01.mp4",
        "container": "mp4",
        "exists": true,
        "size_bytes": 123456789
      },
      "format": {
        "container": "mov,mp4,m4a,3gp,3g2,mj2",
        "duration_seconds": 5400.5,
        "bit_rate": 1500000
      },
      "streams": [
        {
          "type": "video",
          "index": 0,
          "codec": "h264",
          "codec_long": "H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10",
          "bit_rate": 1200000,
          "language": "eng",
          "width": 1920,
          "height": 1080,
          "frame_rate": 29.97,
          "pixel_format": "yuv420p"
        },
        {
          "type": "audio",
          "index": 1,
          "codec": "aac",
          "codec_long": "AAC (Advanced Audio Coding)",
          "bit_rate": 192000,
          "language": "eng",
          "channels": 2,
          "channel_layout": "stereo",
          "sample_rate": 48000
        }
      ]
    }
  ]
}
```
