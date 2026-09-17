## Version 2.1.1(09/17/2026)

### Changed

1. Move the theme repository to `0froq/Qlean`.
2. Add a maintenance notice: I barely use Obsidian anymore, so updates will almost stop, and support for new versions and features may be slow.

## Version 2.1.0(10/09/2025)

### Fixed

1. Bug that option `UI Font` does not apply to some text in settings.
2. Bug that the padding of the code block is kind of so weird.
3. Font family of `#tags` now uses value of option `Monospace Font`.

### Changed

1. Smaller callout padding and margin to avoid too much space.
2. Smaller border radius of code block to be consistent with other elements.

### Added

1. Add `200px` left margin to status bar to avoid overlapping with left sidebar. 
2. Style for "Bases".
3. Style for Stack views. (To be honest, I just notice that Obsidian has this one...)

## Version 2.0.7(01/08/2025)

### Fixed

1. Bug that when [Supercharged Links](obsidian://show-plugin?id=supercharged-links-obsidian) is installed, the link color is not overridden.

## Version 2.0.6(12/28/2024)

### Changed

1. Color of url in source code mode: muted -> same as link color.

### Fixed

1. Bug that the top border of the table is not displayed.


## Version 2.0.5(12/15/2024)

### Fixed

1. Bug that math in tables is not displayed correctly.

## Version 2.0.4(12/15/2024)

### Changed

1. Default value of font weight: `100` -> `400`.

### Fixed

1. Bug in the latest version.

## Version 2.0.3(12/15/2024)

### Added

1. Option `Common Font Weight` to set the font weight of all text elements.

## Version 2.0.2(12/10/2024)

### Added

1. Option `Always Show Full Header in Outline`: if enabled, the full header will always be displayed in the outline, which is useful for long headers.

### Changed

1. Tree items' height: `1.5em` -> `1.2em`.

## Version 2.0.1(11/25/2024)

### Added

1. Option `Cover Mode for Highlight`: if enabled, text in highlight will only be displayed when hovering on it, which is useful for hiding spoilers.

## Version 2.0.0(11/06/2024)

It's a big update! Better explore it by yourself!

### Added

1. Option `Header Hovering Underline`: offers a new "grow" style and the old "fade" style.
2. Extensive support for checkboxes (`- [ ]`), where all lowercase letters, uppercase letters, and some special characters filled in `[]` will render a different SVG icon.
3. Option `Uppercase Set for Checkboxes`: offers two sets of uppercase letters, one is simply the upper letter itself, and the other is social media set.
4. Option `Callouts Border` and `Colorful Callouts Title` in "Callout" section.
5. Section "UI Style":
   1. Option `Toggles Style`: offers a brand new style for toggles.
   2. Option `Glassmorphism Command Palette`: applies the glassmorphism effect to the modals and popups.
6. Same effect as file-tree's ancestors and descendants indicators in outline.
7. Section "Tables":
   1. Option `Always Center Header Rows`: if enabled, the header row will always be aligned in the center.
   2. Option `Full Width Tables`: if enabled, the table's width will be 100% of the container instead of fitting the content.
   3. Option `Top & Bottom Borders for Table`.
8. Visibility of drag handles when hovering on the cell.
9. More...

### Changed

1. Default value of `Tags Border Radius (em)`: `1.0`.
2. Callouts background color: less transparent to avoid weird background color in nested calllouts'.
3. Default value of `Decoration Style for Underlined`: `Wavy`.
4. All file icons.
5. All border radius: more consistent.
6. Tabs' style.
7. All buttons' and inputs' style.
8. Line height and line spacing in preview mode and editing mode: unified as much as possible to avoid flickering when switching between modes.
9. Header hovering underlines' position: adjust to avoid overlapping with the text.
10. Default value of `Decoration Width for Strikethrough`: `2.0`.
11. More...

### Removed

1. Option `Use Built-in Color Picker`.
2. Strikethrough decorations of the checked task(`- [x]`).
3. More...

### Fixed

1. Headers displayed in one line, which produces a horizontal scrollbar.
2. Wrapped code in code block. (I really thought it was a bug)
3. Incorrectly file tree style when it is not the left split.
4. Incorrectly file icons on platforms other than macOS.
5. More...

## Version 1.0.2(11/04/2024)

### Added

1. Option `Enable Alternative Checkboxes`: to toggle the checkbox style offered by this theme. If you have your own checkbox style implemented by CSS snippet, disable this option in order to avoid conflicts.

> Thank to [@damiankorcz](https://github.com/damiankorcz) for the implementation. Read more about this initiative in this repo: [Alternative-Checkboxes-Reference-Set](https://github.com/damiankorcz/Alternative-Checkboxes-Reference-Set).

## Version 1.0.1(02/22/2024)

### Fixed

1. Not fully displayed Mermaid graph.

## Version 1.0.0(02/10/2024)

### Added

1. Option `Header Level Indicator`: if enabled, headers' level indicator will take the collapse indicator's job. You can collapse headers by clicking on the level indicator, and it will give you a clear visual feedback.
2. `line-through` style for checked tasks(`- [x]`).
3. Codeblock language indicator that supports all languages listed in [prismjs](https://prismjs.com/#supported-languages).
4. Option `Use Built-in Color Picker`.

### Removed

1. Decoration options for strong, em, and underline.
2. "Red Close Button" and "Close Button Rotate Animation" option.
3. `box-shadow` and `text-shadow` in tags.
4. Underline of file name in editor mode.

### Changed

1. Smoother header hovering effect.
2. Darker background color in Dark mode.
3. Darker code block background color in Dark mode.
4. Paler text color in Dark mode.
5. Paragraphs' `line-height`: `1.75`.
6. Default highlight style.
7. Option `Callouts' dog-ear`: disabled by default.
8. Better "Copy" button style in codeblock.
9. Smaller `#tag`.
10. Active sideber icon highlighted: `stroke` instead of `fill`.
11. Side dock icon hovering style.
12. Brighter text color in tags.
13. All buttons' style.
14. Tables style.
15. Header hovering underlines: a continuous line.

### Fixed

1. Incorrectly displayed alt text of images.
2. "Wings" of inline codes.
3. Unaccessible topbar in Zen mode.

## Version 0.1.6(12/22/2023)

### Changed

1. Active tab color in dark mode: smoother.
2. Side dock color: the same as main content area color.

### Fixed

1. Unhiden side dock in Zen mode.
2. Unworking style of #tags in "property".

## Version 0.1.5(10/20/2023)

### Added

1. Option `Embed Alt Position` for embeds' alts.

### Fixed

1. Incorrectly displayed file icons of some other types of files.
2. Unworking Hue Slider preview.

## Version 0.1.4(10/19/2023)

### Changed

1. Indication of the active file in file tree: border instead of background.
2. Default font family.

### Fixed

1. Unworking font & accent color change button, with deep regret.

## Version 0.1.3(09/14/2023)

### Changed

1. `#tags` in "Property": the same as that out of "Property".

### Fixed

1. Incorrectly displayed Mermaid graphs.

## Version 0.1.2(09/07/2023)

### Added

1. Option `Embed Alt`, with soon-comming position option.

### Removed

1. Borders of sidebar and topbar in Zen mode.

## Version 0.1.1(09/06/2023)

### Changed

1. Background color of active file in file tree: change to accent color.
2. Selected text color: now works as accent color.

### Fixed

1. Incorrectly displayed left-top corner color.
