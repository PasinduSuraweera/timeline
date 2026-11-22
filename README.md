<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/banner-dark.svg" />
    <source media="(prefers-color-scheme: light)" srcset="docs/banner-light.svg" />
    <img alt="A pixel wave drawn from a year of GitHub contributions, with a small surfer on the crest" src="docs/banner-dark.svg" width="880" />
  </picture>
</div>

<br>

<div align="center">

[![Tests][tests-badge]][tests-url]
[![Live site][site-badge]][site-url]
[![GitHub Marketplace][market-badge]][market-url]
[![Action release][release-badge]][release-url]
[![Python][python-badge]][python-url]
[![MIT license][license-badge]][license-url]

</div>

  [tests-badge]: https://github.com/PasinduSuraweera/timeline/actions/workflows/test.yml/badge.svg
  [tests-url]: https://github.com/PasinduSuraweera/timeline/actions/workflows/test.yml
  [site-badge]: https://badgen.net/badge/site/timeline-readme.vercel.app/ff6a3d?labelColor=374151
  [site-url]: https://timeline-readme.vercel.app/
  [market-badge]: https://badgen.net/badge/marketplace/Timeline/ff6a3d?icon=github&labelColor=374151
  [market-url]: https://github.com/marketplace/actions/timeline
  [release-badge]: https://badgen.net/github/release/PasinduSuraweera/timeline-action?label=action&labelColor=374151&color=ff6a3d
  [release-url]: https://github.com/PasinduSuraweera/timeline-action/releases
  [python-badge]: https://badgen.net/badge/python/3.10%2B%20stdlib/ff6a3d?labelColor=374151
  [python-url]: https://github.com/PasinduSuraweera/timeline/tree/main/timeline
  [license-badge]: https://badgen.net/github/license/PasinduSuraweera/timeline?labelColor=374151&color=ff6a3d
  [license-url]: LICENSE

# Timeline

Your GitHub contribution year, rendered as a wave with something riding it.

Each week of your calendar becomes one swell. The band scrolls forever, a sparkle runs along the crest, and a small pixel figure steps up and down as the water passes under it. It is one animated SVG, generated per request, so it follows your calendar without you touching it again.

This started as the header on [my profile](https://github.com/PasinduSuraweera) and was pulled out so anyone can point it at their own username.

## Use it

Pick your settings at [timeline-readme.vercel.app](https://timeline-readme.vercel.app/), or write the URL by hand:

```
[![my contribution wave](https://timeline-readme.vercel.app/api/timeline?user=YOUR_USERNAME)](https://github.com/YOUR_USERNAME)
```

There is a shorter form for the plain case:

```
![my contribution wave](https://timeline-readme.vercel.app/YOUR_USERNAME.svg)
```

To commit the SVG to your own repo on a schedule instead, use the [Timeline Action](https://github.com/marketplace/actions/timeline).

## Themes

Add `&theme=` to the URL.

| | | |
| :---: | :---: | :---: |
| <img src="docs/themes/ember.svg" width="260" alt="ember"><br>`ember` | <img src="docs/themes/ice.svg" width="260" alt="ice"><br>`ice` | <img src="docs/themes/matrix.svg" width="260" alt="matrix"><br>`matrix` |
| <img src="docs/themes/grape.svg" width="260" alt="grape"><br>`grape` | <img src="docs/themes/rose.svg" width="260" alt="rose"><br>`rose` | <img src="docs/themes/gold.svg" width="260" alt="gold"><br>`gold` |
| <img src="docs/themes/mono.svg" width="260" alt="mono"><br>`mono` | <img src="docs/themes/daylight.svg" width="260" alt="daylight"><br>`daylight` | <img src="docs/themes/paper.svg" width="260" alt="paper"><br>`paper` |

## Riders

Add `&rider=` to the URL.

| | | | | |
| :---: | :---: | :---: | :---: | :---: |
| <img src="docs/riders/surfer.svg" width="150" alt="surfer"><br>`surfer` | <img src="docs/riders/sail.svg" width="150" alt="sail"><br>`sail` | <img src="docs/riders/buoy.svg" width="150" alt="buoy"><br>`buoy` | <img src="docs/riders/flag.svg" width="150" alt="flag"><br>`flag` | <img src="docs/riders/none.svg" width="150" alt="none"><br>`none` |

---

Built by [PasinduSuraweera](https://github.com/PasinduSuraweera).
