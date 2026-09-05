# Third-Party Notices

This file identifies external software, model, media, research, and trademark references used to create or explain the lesson. It does not replace any upstream license or usage term. It does not grant rights to third-party material.

## NVIDIA Cosmos Transfer 2.5

Purpose in this resource: generation of the fog, rain, and snow video examples.

- Project: https://github.com/nvidia-cosmos/cosmos-transfer2.5
- Source license notice: https://github.com/nvidia-cosmos/cosmos-transfer2.5/blob/main/LICENSE
- Recorded source revision: https://github.com/nvidia-cosmos/cosmos-transfer2.5/tree/2ff49d0
- Model card and applicable terms: https://huggingface.co/nvidia/Cosmos-Transfer2.5-2B
- Distilled edge checkpoint directory: https://huggingface.co/nvidia/Cosmos-Transfer2.5-2B/tree/main/distilled/general/edge
- Transfer 2.5 research: https://arxiv.org/abs/2511.00062
- Transfer1 background: https://arxiv.org/abs/2503.14492

The upstream source repository identifies an Apache-2.0 license for its source code. Model weights are governed separately by NVIDIA's applicable model terms. This package does not include model weights or a copy of the Cosmos source code.

A copy of the upstream Apache-2.0 license is included at `third_party/NVIDIA_COSMOS_APACHE-2.0.txt`.

## Source and generated media

The source driving clip is the published car example distributed at `assets/car_example/car_input.mp4` in the Apache-2.0-licensed Cosmos Transfer 2.5 source repository. No separate asset notice was identified alongside that file at the recorded revision. The package includes the repository license and attributes the clip to NVIDIA. The fog, rain, and snow clips are generated outputs derived from that input. The web copies are compressed for education and offline playback. See `docs/MEDIA_PROVENANCE.md` for a per-file map.

The NVIDIA Open Model License states that NVIDIA claims no ownership rights in model outputs. Users remain responsible for input rights, output review, and applicable terms. All source and generated media remain subject to applicable upstream terms and are excluded from the original-resource licenses in this package.

The experiment console summary available during preparation reported `guardrails: disabled`. The surviving records do not establish whether separate safety checks were applied elsewhere in the workflow. The bundled clips should therefore be reviewed as unverified generated media. NVIDIA's current model terms remain applicable.

**Built on NVIDIA Cosmos.**

## Ray

Purpose in this resource: orchestration of independent GPU generation jobs and explanatory pseudocode.

- Project: https://github.com/ray-project/ray
- Documentation: https://docs.ray.io/
- License notice: https://github.com/ray-project/ray/blob/master/LICENSE

The browser lesson does not bundle Ray or require it at runtime.

## Production tools

ReportLab generated the printable PDFs. FFmpeg produced the compressed web videos and lesson-specific composites. Neither tool is required to open the browser lesson. Their own licenses remain with their respective projects.

- ReportLab: https://www.reportlab.com/dev/docs/
- FFmpeg: https://ffmpeg.org/legal.html

## Research publications

Paper titles, author names, short summaries, and links are included for scholarly citation. Full papers are not redistributed. Bibliographic records appear in `references/REFERENCES.bib`.

## Names and marks

NVIDIA, Cosmos, and Ray names may be trademarks of their respective owners. Their use identifies the tools used in the demonstration. No affiliation, sponsorship, or endorsement is implied.

## Original-resource licenses

Original educational content is licensed under CC BY 4.0. Original code is licensed under Apache 2.0. See `LICENSE_SCOPE.md`. These licenses do not relicense third-party software, model materials, media, publications, names, or marks.
