# 📘 Product Requirements Document (PRD)

**Project Name:** `discripper`
**Version:** 1.0
**Author:** Draeician
**Platform:** Linux Mint 22+
**Status:** Draft

---

## 1. 📍 Overview

`discripper` is a command-line utility designed to **rip DVDs and Blu-ray discs** on Linux systems, automatically **detect whether the disc contains a movie or a TV series**, and **extract and organize video files** accordingly. It emphasizes simplicity, automation, and reliance on open-source tools installable via standard package managers (`pip`, `pipx`, `apt`, `.deb`).

The tool targets media collectors, archivists, and home media server users who want a **“set-and-forget” workflow** for digitizing disc collections.

---

## 2. 🎯 Objectives & Goals

* **Simple CLI workflow:** One command to rip and organize a disc.
* **Automated classification:** Automatically detect whether the disc is a movie or TV series.
* **Episode extraction:** For series discs, split episodes into individual MP4 files.
* **Organized output:** Create consistent directory structures and filenames with embedded metadata.
* **Minimal setup:** Only depend on packages installable from standard package managers.
* **Future extensibility:** Allow metadata lookup (e.g., TheTVDB/TMDB) in later versions.

---

## 3. 🧱 System Requirements

| Requirement                  | Details                                                                      |
| ---------------------------- | ---------------------------------------------------------------------------- |
| **OS**                       | Linux Mint 22+ (Ubuntu/Debian derivatives supported)                         |
| **Dependencies**             | Must be installable via `pip`, `pipx`, `apt`, or `.deb`                      |
| **Hardware**                 | USB-connected Blu-ray/DVD drive                                              |
| **Default Output Directory** | `/home/user/Videos` (configurable via YAML/JSON config)                      |
| **Output Format**            | `.mp4`                                                                       |
| **Language**                 | Python 3.10+                                                                 |
| **Compression**              | Optional, handled via external HandBrake CLI (not part of `discripper` core) |

---

## 4. 🔧 Functional Requirements

### 4.1 CLI Behavior

* Tool is invoked manually via command line:

  ```bash
  discripper /dev/sr0
  ```

* Optional flags:

  ```bash
  discripper /dev/sr0 --config ~/.config/discripper.yaml --verbose
  ```

* Behavior:

  1. Detect disc and list all titles/tracks.
  2. Analyze disc structure to classify as **movie** or **TV series**.
  3. If a TV series:

     * Infer episode boundaries from title/chapter length patterns.
     * Extract each episode into its own `.mp4` file.
     * Name and organize output per conventions.
  4. If a movie:

     * Rip main title as a single `.mp4` file.
     * Name based on disc label or detected title.

---

### 4.2 Output Naming Convention

* No spaces or special characters (underscores allowed).

* **TV series format:**

  ```
  <seriesName>/<seriesName>-s<seasonNumber>e<episodeNumber>_<title>.mp4
  ```

  Example:

  ```
  /home/user/Videos/Firefly/Firefly-s01e01_Serenity.mp4
  ```

* **Movie format:**

  ```
  <movieTitle>.mp4
  ```

  Example:

  ```
  /home/user/Videos/The_Matrix.mp4
  ```

---

### 4.3 Configuration File

`~/.config/discripper.yaml` (default location):

```yaml
output_directory: "/home/user/Videos"
compression: false
naming:
  separator: "_"
  lowercase: false
logging:
  level: "INFO"
```

* All defaults should work without a config file.
* Command-line arguments override config file values.

---

## 5. 🧠 Classification Logic (MVP)

* **Movie detection:**

  * One title significantly longer than others (>60 min).
  * Total runtime < 3 hours.

* **TV series detection:**

  * Multiple titles of similar duration (20–60 min).
  * Gaps between track lengths < 20%.

* **Episode inference:**

  * Sort by runtime and order of appearance.
  * Assign sequential episode numbers (e.g., `s01e01`, `s01e02`, ...).

> **Note:** MVP relies purely on disc structure and duration patterns. Metadata APIs (e.g., TheTVDB) may be integrated later.

---

## 6. 📂 Directory Structure & Organization

When ripping a TV series, output is organized as:

```
<output_directory>/<seriesName>/
  ├── <seriesName>-s01e01_<title>.mp4
  ├── <seriesName>-s01e02_<title>.mp4
  └── ...
```

Movies are output directly to the configured directory:

```
<output_directory>/<movieTitle>.mp4
```

---

## 7. ⚙️ Error Handling & Edge Cases

| Scenario                 | Expected Behavior                           |
| ------------------------ | ------------------------------------------- |
| Disc not detected        | Exit with error message and code 1          |
| Ripping fails            | Display error, exit with code 2             |
| Structure unclear        | Default to single movie rip                 |
| Output directory missing | Create directory automatically              |
| Filename collisions      | Append incrementing suffix `_1`, `_2`, etc. |

---

## 8. 📊 Non-Functional Requirements

* **Performance:** Ripping should proceed at optical drive’s maximum supported speed.
* **Portability:** Runs on any Debian-based system with Python 3.10+.
* **Logging:** All actions logged to console and optional log file.
* **Extensibility:** Metadata API integration should require minimal changes to core pipeline.

---

## 9. 🧪 Acceptance Criteria

* [ ] Running `discripper /dev/sr0` rips a movie disc into a single MP4 with a proper filename.
* [ ] Running `discripper /dev/sr0` on a TV series disc splits and names episodes correctly.
* [ ] Output structure matches `<series>/<series>-s01e01_Title.mp4`.
* [ ] Configurable output directory is respected.
* [ ] Errors are handled gracefully with clear messaging.

---

## 10. 🚀 Future Enhancements (v1.1+)

* 📡 Metadata lookup from TheTVDB or TMDB
* 🧪 Improved chapter-to-episode mapping with heuristic learning
* 🧰 Subtitles and audio track selection
* ⚙️ Auto-trigger on disc insertion (via udev/systemd)
* 📦 `.deb` package distribution

---

### 📎 Summary

`discripper` aims to be a **minimal, reliable, and extensible** tool for ripping and organizing DVD/Blu-ray discs on Linux. Its first version focuses on robust local structure detection and automated file organization, laying the groundwork for richer metadata and automation features in future releases.

