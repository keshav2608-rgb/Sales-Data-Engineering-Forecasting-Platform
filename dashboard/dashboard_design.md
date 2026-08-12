# Dashboard Design Guidance

## Principles
- One clear question per chart. Don't combine revenue-by-region and
  revenue-by-category into one chart.
- Max ~6 visual elements per page (scorecards count individually but are
  small - budget accordingly).
- One consistent color per dimension across the whole report (e.g. always
  the same color for "Electronics" on every chart it appears on) - Looker
  Studio lets you set this globally under Theme and Layout.
- Avoid: pie charts with >5 slices, 3D anything, unnecessary gridlines,
  tables wider than ~6 columns.
- Use a single accent color for "actual" and a visually distinct one
  (e.g. dashed line, lighter shade) for "forecast" on the Forecast page -
  the reader should instantly tell historical from predicted.

## Layout
- Page 1 (Executive Overview): scorecards across the top, two charts below.
- Page 2 (Sales Analysis): filters as a left rail or top bar, charts in a
  2x2 grid.
- Page 3 (Forecast): one large combo chart (historical + forecast band) as
  the hero element, with 3 small scorecards (horizon, model, accuracy)
  beside it.

## What answers the business questions
- "How are sales performing?" -> Page 1 scorecards + revenue-over-time line.
- "Which products/categories drive revenue?" -> Page 2 top-products table +
  category bar chart.
- "Which regions perform best?" -> Page 1/2 region bar chart.
- "Is revenue growing?" -> MoM/YoY growth scorecards on Page 1.
- "What will sales look like in the future?" -> Page 3 forecast chart.
