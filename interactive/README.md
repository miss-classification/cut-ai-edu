# CUT! Best-of-N Studio

**How Do You Test Weather You Cannot Schedule? A Visual Lesson on Verifier-Guided Test-Time Scaling for Generative Video**

Alicia Chua, Pawarit Laosunthara, and Eric Tang · Anyscale

## Present at the poster

Extract the entire ZIP and open **present.html** in a current desktop browser. Select **Full screen** when the projector is connected. Use the arrow keys or the Back and Next buttons. Nothing advances on a timer. The last screen offers Start again for the next group.

| Stop | Ask the audience | Action |
| --- | --- | --- |
| 1. Fog | What should stay fixed when the weather changes? | Show the recorded drive, the generation diagram, and a fog candidate. |
| 2. Vote | Which clip would you keep, and why? | Play both fog takes and record A, B, or neither. |
| 3. Select | Does a stronger score imply a better match? | Choose N = 8 and compare balanced scoring with intensity alone. Set minimum street fidelity to 97 to retain none. |
| 4. Frames | What does the judge receive? | Play the 15-second illustrated paired review. Separate sampled video frames from the supplied evaluation question. |
| 5. Audit | Does the written observation support the score? | Inspect night rain or frost, ask the audience for a decision, then reveal the saved model response. |
| 6. The final cut | Which visible detail supports your decision? | Choose a new scene and move the divider. Vote to freeze the frame. The screening log can save a written observation. |

The first 5 stops take about 3 minutes with a small group. Leave the rest of a 5-minute demonstration to the final comparison and discussion. For a continuous screening, the optional field reel is available below the interactive ending, and at **studio-media/closing-field-reel.v31.mp4**.

## Paint the Trail

In the full lesson, select **Paint the Trail Gallery** in the chapter navigation. The gallery opens the Change conditions section. **Explore gallery here** opens Paint the Trail inline. **Open in new tab** opens the Pages gallery directly. To point a visitor straight to this activity on the deployed lesson, append `#paint-the-trail` to the lesson URL. Projector stop 6 offers a new-tab link after the audience vote.

The online gallery loads only on request. Closing it removes the frame. If it stays blank, use the new-tab link; without internet, choose **Explore 10 recorded comparisons offline**. The ZIP includes the local comparisons, not a mirror of the online gallery.

For another HTML page, the minimal embed is:

```html
<iframe src="https://paint-the-trail-gallery.pages.dev/"
        title="Paint the Trail gallery of weather comparisons"
        style="display:block;width:100%;height:640px;border:0" loading="lazy" allow="fullscreen" allowfullscreen></iframe>
<a href="https://paint-the-trail-gallery.pages.dev/"
   target="_blank" rel="noopener noreferrer">Open Paint the Trail in a new tab</a>
```

## Case file 11 and research debrief

The projector opens audit stop 5 on the frost-at-dawn case. Reveal the response to see why the striped foreground hood and a structure score of 5/5 disagree. On the full site, open **Judge lab → Case file 11: The invented racing hood**. The frame pair is sampled at 2.875 seconds (frame 47 of 93). In a hosted copy or a local browser address, `index.html#invented-hood` opens the case file and `present.html#invented-hood` opens the projector reveal.

**Lessons learned** follows the judge cases. It distinguishes the original illustrative rankings from recorded model ratings. Each finding has a proposed test: independent human labels, checks for object additions or omissions, and evaluation on unseen drives. The optional projector debrief includes the same distinctions.

## Picture resolution

The original fog candidates remain the supplied 640 × 360 web videos. The showcase comparisons are 960 pixels across both pictures and their labels. The final-cut divider uses 472 × 248 content pixels per view, without drawing a small source into a larger intermediate canvas. **Enlarge picture** is optional for the room. The edited reel places the two cropped views at native size and preserves the original 960 × 640 weather montage at native size in its last chapter.

The original labelled downloads are retained. The edited reel, judge animation, two neutral review clips and interactive divider use measured picture boundaries; title and footer strips stay outside their images. See **evidence/picture-quality.json** for dimensions, media provenance, and the measured encoding differences.

For a higher-resolution edition, the seven matched source/output pairs must come from the generation workspace. From the extracted site, run `python tools/collect_projector_pairs.py --root /path/to/cosmos-offroad --output CUT_projector_masters.zip` on the machine with those files. It reads only the seven identified records and their videos and creates a new archive. It runs no model and uploads nothing. The separate city fog study would need its original drive, guide and 8 native candidate videos from the fog-generation workspace.

## Use the full lesson

- **index.html**: the original fog lesson, animated generation diagram, blind vote, nested candidate pools, rubric and gates, weather transformations, reference comparisons, VLM cases, classroom guidance, and interactive finale.
- **evidence.html**: recorded judge outputs, diagnostic limits, the Cosmos 3 Nano comparison, Ray throughput measurements, and hardware measurement boundaries.
- **teaching.html**: instructor routes, assessment guide, and fillable, printable worksheet.
- **TEACHING_DESIGN.md**: learning goals mapped to observable learner actions.
- **evidence/**: fog annotations, recorded prompts and responses, media credits, and chapter-level provenance.
- **studio-media/**: the judge animation in MP4 and GIF, the edited field reel, neutrally captioned review cases, and the original umbrella-to-snow comparison.
- **BUILD_MANIFEST.json**: file hashes and the scope of verification.

Core activities play from the extracted folder without an account, model endpoint, or GPU. Links to publications and external repositories need an internet connection. Keep the HTML, scripts, styles and media folders together. Opening an HTML file inside a ZIP viewer will not reliably load the other files.

## Evidence and reuse

The accepted fog demonstration holds the source drive, request, model and settings fixed while varying the seed. Its weather-intensity, street-fidelity and stability ratings are illustrative judgments. Recorded outputs of Qwen3-VL-32B-Instruct belong to a separate study. The animation uses a saved GOOSE flooded-mud review; no browser interaction issues a new model call.

The four final comparisons are curated examples for visual inspection. Participants supply the retention decision and visible evidence. The interface offers no pass rate or certification. Starter frames may be labelled “poster frame” until video data is available; later decisions record the playback time. Screening notes remain in the page session unless a participant saves the text file.

The research notes separate the original L40S fog run from the later A100 and B200 observations. No matched H100 comparison is supplied. The original [teaching code and notebooks](https://github.com/miss-classification/cut-ai-edu) and [extension code](https://github.com/miss-classification/cosmos-offroad-ray) remain available separately.

## Deployment and preflight

For Cloudflare Pages, upload the static site contents with **index.html at the root**. There is no build command. This ZIP has not been deployed. Before the session, open the extracted presentation on the actual laptop: check a fog vote, a judge reveal, the final divider and keyboard navigation at the projector's resolution.

## Attribution

Original teaching content follows the project's CC BY 4.0 scope; original code follows its Apache 2.0 scope. Media attribution and third-party terms are recorded for each example. GOOSE and GrandTour source footage is CC BY-SA 4.0. The Nairobi impala footage is by Addshore (CC BY-SA 4.0); the winter-road footage is by Vladislav Sanikovich (CC BY 3.0). Boreas and TartanDrive 2.0 source footage are CC BY 4.0. Edited excerpts retain the applicable source terms; the CC BY-SA adaptations are available under CC BY-SA 4.0. See evidence/media-manifest.json and evidence/field-reel.json for source links and modifications. The archive contains no model weights.
