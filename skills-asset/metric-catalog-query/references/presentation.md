# Presentation

Normalize results to `dimensions`, `measures`, `rows`, `totals`, `units`, `timezone`, and `metricDefinitions`. Use response mappings; preserve nulls.

- `raw`: normalized plus validated provider data only when explicitly requested and permitted; never persist it.
- `table`: rows/columns with units and filter context.
- `summary`: concise facts with definition and scope.
- `chart`: declarative chart spec plus normalized data; line for ordered time, bar for categories.
- `auto`: honor explicit visualization words; otherwise scalar→summary, multidimensional rows→table, time series→line.

Downgrade unsupported charts with a warning; never invent dimensions. Independent widgets may run concurrently, but join only compatible periods, granularity, organization, dimensions, units, and definitions. Keep incompatible blocks separate. Partial success remains `partial`; never replace missing values with zero.
