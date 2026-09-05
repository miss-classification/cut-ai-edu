# Teaching Materials Manifest

**Authors:** Alicia Chua, Pawarit Laosunthara, and Eric Tang, Anyscale

## Resource title

**How Do You Test Weather You Cannot Schedule?**

Technical subtitle: **A visual lesson on verifier-guided Best-of-N scaling for controllable video**

## Start here

Read `START_HERE.md`, then open `interactive/index.html`.

The browser lesson is the primary learning artifact. The written materials support live teaching, self-guided study, classroom reuse, and technical inspection.

## Package contents

### Primary lesson

| Path | Purpose |
| --- | --- |
| `START_HERE.md` | Orientation, teaching routes, outcomes, and package map |
| `interactive/index.html` | Complete offline interactive lesson |
| `interactive/*.css` | Original layout, visual, motion, and responsive styles |
| `interactive/*.js` | Original interaction, candidate selection, and quiz logic |
| `interactive/media/` | Source, control, generated candidates, and closing montage |

The media folder contains 20 compressed MP4 files:

- one source driving clip
- one edge-control visualization
- eight fog candidates
- four rain candidates
- four snow candidates
- one short judge reel
- one closing montage

### Teaching documents

| Path | Purpose |
| --- | --- |
| `docs/TEACHING_GUIDE.md` | Five-minute, fifteen-minute, and classroom lesson plans |
| `docs/LEARNER_WORKSHEET.md` | Blind choice, rubric design, scoring, critique, and transfer |
| `docs/ANSWER_KEY.md` | Suggested answers and assessment guidance |
| `docs/RUBRIC_AND_SCORING.md` | Criterion definitions, anchors, gates, and score provenance |
| `docs/REPRODUCIBILITY.md` | Controlled design, environment, run record, and limits |
| `docs/ACCESSIBILITY_AND_REUSE.md` | Access modes, text alternative, and adaptation guidance |
| `docs/MEDIA_PROVENANCE.md` | Per-file media origin, edits, upstream locations, and terms boundary |
| `docs/assets/*.gif` | Lightweight moving previews derived from the bundled lesson videos for the repository README |

### Data and executable example

| Path | Purpose |
| --- | --- |
| `data/rubric_scores.csv` | Fixed illustrative visual annotations used by the selector |
| `source/scoring.py` | Dependency-free weighted selection example |

### Optional statistics lab

| Path | Purpose |
| --- | --- |
| `notebooks/selector_lab.ipynb` | Hardware-free analysis of N, mission weights, proxy failure, and rating uncertainty |

The notebook uses only the Python standard library and the bundled CSV. It is optional. The core browser lesson does not require Python.

### Generation records

| Path | Purpose |
| --- | --- |
| `source/experiments/directors_cut.yaml` | Portable eight-seed fog experiment definition |
| `source/experiments/weather_replication.yaml` | Portable rain and snow experiment definition |
| `source/manifests/directors_cut_public.jsonl` | Sanitized fog generation record |
| `source/manifests/weather_replication_public.jsonl` | Sanitized rain and snow generation record |

The public manifests omit machine names, private paths, tokens, and service details. Their checksums describe the original full-resolution outputs, not the compressed teaching proxies.

### Optional generation source

| Path | Purpose |
| --- | --- |
| `generation/cosmos_ray/` | Ray task validation, sweep expansion, Cosmos model actors, execution, and output utilities |
| `generation/experiments/` | Cluster-ready fog, rain, and snow experiment definitions |
| `generation/tests/` | Driver-side tests that run without Cosmos, Ray, PyTorch, or a GPU |
| `generation/README.md` | Setup, validation, execution, safety defaults, and limitations |

### Scholarship, provenance, and compliance

| Path | Purpose |
| --- | --- |
| `references/REFERENCES.bib` | Recent linked papers and implementation references |
| `ORIGINALITY.md` | Original contribution and third-party boundary |
| `THIRD_PARTY_NOTICES.md` | External software, model, media, and trademark notices |
| `LICENSE_CONTENT_CC-BY-4.0.txt` | CC BY 4.0 license notice for original educational content |
| `LICENSE_CODE_APACHE-2.0.txt` | Apache 2.0 license text for original code |
| `LICENSE_SCOPE.md` | Boundary between original licenses and third-party material |
| `third_party/NVIDIA_COSMOS_APACHE-2.0.txt` | Copy of the upstream Cosmos source repository license |
| `MANIFEST.md` | This inventory |
| `SHA256SUMS` | Final package file checksums, generated during packaging |

### Printable PDFs

| Path | Purpose |
| --- | --- |
| `pdf/CUT_Best_of_N_Teaching_Guide.pdf` | Printable facilitator guide |
| `pdf/CUT_Best_of_N_Learner_Worksheet.pdf` | Printable learner worksheet |
| `pdf/CUT_Best_of_N_Answer_Key.pdf` | Printable facilitator answer key |

The required two-page proposal PDF is submitted separately through OpenReview.

## Media naming

Fog candidates use:

```text
interactive/media/directors_cut_take01.mp4
...
interactive/media/directors_cut_take08.mp4
```

Rain and snow candidates use:

```text
interactive/media/weather_replication_rain_take01.mp4
...
interactive/media/weather_replication_rain_take04.mp4

interactive/media/weather_replication_snow_take01.mp4
...
interactive/media/weather_replication_snow_take04.mp4
```

## Score status

The 0-to-100 scores are fixed illustrative visual annotations. They are teaching inputs. They are not ground truth, benchmark results, validated autonomous-vehicle metrics, live video-language model outputs, or safety certification.

## Runtime requirements

Core interactive lesson:

- a modern browser
- no network connection
- no account
- no GPU
- no Python

Scoring example:

- Python 3.10 or newer
- Python standard library only

Optional video regeneration:

- upstream Cosmos Transfer software and model access
- compatible NVIDIA GPU hardware
- the included `generation/cosmos_ray` adapter
- acceptance of all applicable upstream terms

No model weights are included.

## Package verification

The release process validates local links, checks structured data, scans text for private paths and credentials, verifies individual-file limits, tests the ZIP archive, and confirms the final archive remains below 200 MB.
