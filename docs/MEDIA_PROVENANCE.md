# Media Provenance

**Authors:** Alicia Chua, Pawarit Laosunthara, and Eric Tang, Anyscale

This table maps every distributed video to its origin and role. The web copies are compressed teaching proxies. No audio is included.

| Distributed file | Origin | Lesson-specific modification | Governing terms or action |
| --- | --- | --- | --- |
| `interactive/media/source.mp4` | NVIDIA Cosmos Transfer 2.5 car example, `assets/car_example/car_input.mp4` | Rescaled and transcoded for browser playback | Distributed in the upstream Apache-2.0 source repository with no separate asset notice identified at the recorded revision. See `THIRD_PARTY_NOTICES.md`. |
| `interactive/media/control_edge.mp4` | Edge control computed from the published car example | Rescaled and transcoded for browser playback | Subject to the source clip terms and applicable upstream software terms. |
| `interactive/media/directors_cut_take01.mp4` | Cosmos Transfer 2.5 distilled edge output, seed 2025 | Rescaled, transcoded, and used as fog candidate 01 | Model output derived from the source clip. Review the NVIDIA Open Model License and source clip terms. |
| `interactive/media/directors_cut_take02.mp4` | Cosmos Transfer 2.5 distilled edge output, seed 7319 | Rescaled, transcoded, and used as fog candidate 02 | Same as above. |
| `interactive/media/directors_cut_take03.mp4` | Cosmos Transfer 2.5 distilled edge output, seed 18427 | Rescaled, transcoded, and used as fog candidate 03 | Same as above. |
| `interactive/media/directors_cut_take04.mp4` | Cosmos Transfer 2.5 distilled edge output, seed 29063 | Rescaled, transcoded, and used as fog candidate 04 | Same as above. |
| `interactive/media/directors_cut_take05.mp4` | Cosmos Transfer 2.5 distilled edge output, seed 41851 | Rescaled, transcoded, and used as fog candidate 05 | Same as above. |
| `interactive/media/directors_cut_take06.mp4` | Cosmos Transfer 2.5 distilled edge output, seed 57203 | Rescaled, transcoded, and used as fog candidate 06 | Same as above. |
| `interactive/media/directors_cut_take07.mp4` | Cosmos Transfer 2.5 distilled edge output, seed 70439 | Rescaled, transcoded, and used as fog candidate 07 | Same as above. |
| `interactive/media/directors_cut_take08.mp4` | Cosmos Transfer 2.5 distilled edge output, seed 91873 | Rescaled, transcoded, and used as fog candidate 08 | Same as above. |
| `interactive/media/weather_replication_rain_take01.mp4` | Cosmos Transfer 2.5 distilled edge output, rain prompt, seed 2025 | Rescaled, transcoded, and used as rain candidate 01 | Model output derived from the source clip. Review the NVIDIA Open Model License and source clip terms. |
| `interactive/media/weather_replication_rain_take02.mp4` | Cosmos Transfer 2.5 distilled edge output, rain prompt, seed 7319 | Rescaled, transcoded, and used as rain candidate 02 | Same as above. |
| `interactive/media/weather_replication_rain_take03.mp4` | Cosmos Transfer 2.5 distilled edge output, rain prompt, seed 18427 | Rescaled, transcoded, and used as rain candidate 03 | Same as above. |
| `interactive/media/weather_replication_rain_take04.mp4` | Cosmos Transfer 2.5 distilled edge output, rain prompt, seed 29063 | Rescaled, transcoded, and used as rain candidate 04 | Same as above. |
| `interactive/media/weather_replication_snow_take01.mp4` | Cosmos Transfer 2.5 distilled edge output, snow prompt, seed 2025 | Rescaled, transcoded, and used as snow candidate 01 | Model output derived from the source clip. Review the NVIDIA Open Model License and source clip terms. |
| `interactive/media/weather_replication_snow_take02.mp4` | Cosmos Transfer 2.5 distilled edge output, snow prompt, seed 7319 | Rescaled, transcoded, and used as snow candidate 02 | Same as above. |
| `interactive/media/weather_replication_snow_take03.mp4` | Cosmos Transfer 2.5 distilled edge output, snow prompt, seed 18427 | Rescaled, transcoded, and used as snow candidate 03 | Same as above. |
| `interactive/media/weather_replication_snow_take04.mp4` | Cosmos Transfer 2.5 distilled edge output, snow prompt, seed 29063 | Rescaled, transcoded, and used as snow candidate 04 | Same as above. |
| `interactive/media/judge_reel.mp4` | Lesson edit assembled from documented fog candidates 03, 04, and 07 | Sequenced, labeled, and transcoded for the selector explanation | Subject to the same terms as its component outputs. The edit itself was created for this lesson. |
| `interactive/media/montage-rain-fog-night-clear.mp4` | Author-supplied lesson montage showing rain, fog, night, and clear variants of the same drive | Four-panel composition and web transcode | Subject to the same terms as its component clips. The composition itself was created for this lesson. |

## Upstream locations

- Source repository at recorded revision: https://github.com/nvidia-cosmos/cosmos-transfer2.5/tree/2ff49d0
- Published source clip: https://github.com/nvidia-cosmos/cosmos-transfer2.5/blob/2ff49d0/assets/car_example/car_input.mp4
- Model card: https://huggingface.co/nvidia/Cosmos-Transfer2.5-2B
- Distilled edge checkpoint directory: https://huggingface.co/nvidia/Cosmos-Transfer2.5-2B/tree/main/distilled/general/edge
- Transfer 2.5 paper: https://arxiv.org/abs/2511.00062

The exact Hugging Face model revision was not recorded during generation. This limits byte-for-byte regeneration and is stated rather than inferred.

Third-party source and generated media are excluded from the original-resource licenses in this package. Their applicable upstream terms remain in force.
