# Timeline

Your GitHub contribution year, rendered as a wave with something riding it.

![a contribution wave](https://timeline-readme.vercel.app/PasinduSuraweera.svg)

Each week of your calendar becomes one swell. The band scrolls forever, a sparkle runs
along the crest, and a small pixel figure steps up and down as the water passes under it.
It is one animated SVG, generated per request, so it follows your calendar without you
touching it again.

This started as the header on [my profile](https://github.com/PasinduSuraweera) and was
pulled out so anyone can point it at their own username.

## Use it

Pick your settings at **[timeline-readme.vercel.app](https://timeline-readme.vercel.app)**, or write the URL by hand:

```markdown
[![my contribution wave](https://timeline-readme.vercel.app/api/timeline?user=YOUR_USERNAME)](https://github.com/YOUR_USERNAME)
```

There is a shorter form for the plain case:

```markdown
![my contribution wave](https://timeline-readme.vercel.app/YOUR_USERNAME.svg)
```

## Settings

Everything is a query parameter. Unknown values fall back to the default rather than
erroring, so a typo gives you a plain wave instead of a broken image.

| Setting | Values | Default | What it changes |
| --- | --- | --- | --- |
| `user` | a GitHub username | required | Whose calendar is drawn |
| `theme` | `ember` `ice` `matrix` `grape` `rose` `gold` `mono` `daylight` `paper` | `ember` | The palette |
| `accent` | hex, with or without `#` | from theme | The body of the wave. The crest cap and sparkle are derived from it |
| `bg` | hex | from theme | Background behind the water |
| `hot`, `glint`, `line` | hex | derived | The crest cap, the sparkle, the border |
| `width` | 320 to 1600 | `880` | Band width in pixels |
| `height` | 60 to 400 | `140` | Band height in pixels |
| `cell` | 2 to 10 | `4` | Size of one dot, so how coarse the pixel grid looks |
| `speed` | 4 to 300 | `33` | Seconds for one full scroll. Lower is faster |
| `smooth` | 0.2 to 5 | `1` | How much the week-to-week noise is calmed into swell |
| `weeks` | 8 to 53 | `52` | How much history to draw |
| `rider` | `surfer` `sail` `buoy` `flag` `none` | `surfer` | What rides the crest |
| `rider_at` | 0 to 100 | `33` | Where it sits, as a percentage across |
| `glints` | `on`, `off` | `on` | The sparkle travelling along the ridge |
| `dots` | `on`, `off` | `on` | The dim dot grid behind the water |
| `border` | `on`, `off` | `off` | A hairline border around the band |
| `fallback` | `sine` `flat` `none` | `sine` | What to draw when the calendar cannot be read. `none` returns 404 instead |

Some spellings are accepted as aliases: `username`, `login` and `name` for `user`;
`color` and `colour` for `accent`; `duration` for `speed`; `sprite` for `rider`;
`scale` for `cell`; `background` for `bg`; `sparkle` for `glints`; `grid` for `dots`.

The width and height are snapped down to whole dots, so `width=875&cell=4` draws 872
pixels. Pick multiples of `cell` if an exact size matters.

### Dark and light

One image cannot react to the reader's colour scheme, but two can:

```html
<picture>
  <source media="(prefers-color-scheme: light)" srcset="https://timeline-readme.vercel.app/api/timeline?user=YOU&amp;theme=paper">
  <img src="https://timeline-readme.vercel.app/api/timeline?user=YOU" width="100%" alt="my contribution wave">
</picture>
```

### Motion

Readers who have asked their system to reduce motion get a still frame. Nothing scrolls,
nothing sparkles, and the rider stays put.

## Run your own copy

The renderer is pure standard-library Python. No numpy, no Pillow, no build step, nothing
to install.

```bash
git clone https://github.com/PasinduSuraweera/timeline
cd timeline
python3 devserver.py          # http://localhost:8000
```

Deploy the same directory to Vercel and the routes come up as they are. `vercel.json`
already maps `/api/timeline`, `/timeline.svg` and `/<username>.svg`.

Set `GITHUB_TOKEN` to a classic token with no scopes selected, or a fine-grained token
with read access to public data. It is optional: without it the public contribution
fragment is read instead, which needs no credentials but sometimes exposes only the five
shading levels rather than exact daily counts. The wave keeps its shape either way, and
`/api/meta?user=NAME` reports which route answered.

`TIMELINE_CACHE_SECONDS` controls the cache header, default 1800.

## Skip the hosting

If you would rather commit the SVG into your own repo, the Action renders it on a schedule
and pushes it when the shape changes. Nothing is served at request time, and the image is
just a file in your repository.

```yaml
# .github/workflows/timeline.yml
name: timeline

on:
  schedule: [{ cron: "15 6 * * *" }]
  workflow_dispatch:

permissions:
  contents: write

jobs:
  timeline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: PasinduSuraweera/timeline@v1
        with:
          user: ${{ github.repository_owner }}
          out: assets/timeline.svg
          theme: ember
      - name: Commit the wave if it moved
        run: |
          git add -- assets/timeline.svg
          git diff --cached --quiet && exit 0
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git commit -m "Update contribution wave"
          git push
```

Then embed the file: `![my contribution wave](assets/timeline.svg)`.

The same thing locally:

```bash
python3 cli.py --user octocat --out assets/timeline.svg --theme ice --rider sail
```

## How it works

1. **Read the calendar.** Daily counts come from the GraphQL API when a token is present,
   otherwise from the public contributions fragment. Days are grouped into calendar weeks
   and summed. Partial weeks at either end are dropped, because the current week is always
   incomplete and counting it prints a dip into the water that is an artefact of the clock.
2. **Make it loop.** The first and last weeks are eased toward a shared value, so the point
   where the scroll wraps does not read as a step.
3. **Turn weeks into water.** The series is resampled to one value per column and blurred
   with a circular Gaussian, which turns week-to-week spikes into swell.
4. **Light the grid.** Each cell is lit by its distance from the water line: a hot cap on
   the ridge, one cell of haze above, an exponential falloff beneath, and a dim floor
   everywhere else so the whole band reads as a board waiting for data.
5. **Draw it twice.** The field is rendered into an indexed PNG at double width. Translating
   by exactly one width loops seamlessly. Around 2 KB.
6. **Add the rider.** The figure holds a fixed horizontal position while the water moves, so
   the ridge row beneath it changes over the loop. One CSS keyframe is emitted per change,
   with stepped easing, so it lands on whole pixels rather than sliding between them.

The output is a single self-contained SVG of about 30 KB, with the band as a data URI.

## Development

```bash
python3 -m unittest discover -s tests -v
```

The suite covers the wave maths, the PNG encoder including chunk CRCs and seamless tiling,
option clamping, and that hostile input never reaches the markup.

## Limits

- GitHub caches README images through its own proxy, so a fresh commit takes a while to
  show up in the water. This is not something the renderer can hurry along.
- A year with no variation cannot make a wave. Those fall back to the stand-in swell.
- Private contributions only appear if the token owner can see them, which for someone
  else's calendar means they cannot.

## Licence

MIT.
